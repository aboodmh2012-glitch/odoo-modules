import hmac
import json

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class SocialFacebookWebhook(http.Controller):
    @http.route(
        "/social/facebook/<string:key>",
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def receive(self, key, **kwargs):
        account = (
            request.env["social.account"]
            .sudo()
            .search(
                [
                    ("webhook_key", "=", key),
                    ("platform", "=", "facebook"),
                    ("messaging_enabled", "=", True),
                ],
                limit=1,
            )
        )
        if not account:
            return request.make_response("Not found", status=404)

        # Meta subscription challenge (no signature on GET).
        if request.httprequest.method == "GET":
            mode = kwargs.get("hub.mode") or request.params.get("hub.mode")
            token = kwargs.get("hub.verify_token") or request.params.get("hub.verify_token")
            challenge = kwargs.get("hub.challenge") or request.params.get("hub.challenge")
            try:
                expected = account._secret("webhook_secret_env")
            except UserError:
                return request.make_response("Not configured", status=503)
            if mode == "subscribe" and token and hmac.compare_digest(expected, token):
                return request.make_response(challenge or "", status=200)
            return request.make_response("Forbidden", status=403)

        if request.httprequest.content_length and request.httprequest.content_length > 262144:
            return request.make_response("Too large", status=413)
        raw = request.httprequest.get_data()
        if len(raw) > 262144:
            return request.make_response("Too large", status=413)
        signature = request.httprequest.headers.get("X-Hub-Signature-256", "")
        try:
            ok = account._verify_meta_signature(raw, signature)
        except UserError:
            return request.make_response("Not configured", status=503)
        if not ok:
            return request.make_response("Forbidden", status=403)

        operator = account.webhook_user_id
        if (
            not operator
            or not operator.active
            or operator.share
            or account.company_id not in operator.company_ids
            or operator not in account.user_ids
            or not operator.has_group("social.group_social_user")
        ):
            return request.make_response("Not configured", status=503)

        try:
            data = json.loads(raw)
            if data.get("object") != "page":
                return request.make_response("OK", status=200)
            jobs = []
            for entry in data.get("entry") or []:
                entry_id = str(entry.get("id") or "")
                # Public feed comments (BrightBean: feed field).
                for change in entry.get("changes") or []:
                    if change.get("field") != "feed":
                        continue
                    value = change.get("value") or {}
                    # Ingest new comments only. A comment is stored once, keyed by
                    # its id; "edited"/"remove" verbs would dedupe against the
                    # original at the delivery layer and never update it, so they
                    # are dropped explicitly instead of silently accepted.
                    if value.get("item") != "comment" or value.get("verb") != "add":
                        continue
                    comment_id = str(value.get("comment_id") or value.get("id") or "")
                    sender_id = str((value.get("from") or {}).get("id") or "unknown")
                    sender_name = str((value.get("from") or {}).get("name") or sender_id)[:128]
                    text = str(value.get("message") or "")[:16000]
                    if not comment_id or not text:
                        continue
                    timestamp = int(value.get("created_time") or entry.get("time") or 0)
                    if not 0 <= timestamp <= 253402300799:
                        continue
                    jobs.append((entry_id, comment_id, sender_id, sender_name, text, timestamp, "comment"))
                # Messenger DMs (BrightBean: messages field / messaging array).
                for event in entry.get("messaging") or []:
                    message = event.get("message") or {}
                    if message.get("is_echo") or message.get("is_deleted"):
                        continue
                    mid = str(message.get("mid") or "")
                    sender_id = str((event.get("sender") or {}).get("id") or "")
                    text = str(message.get("text") or "")[:16000]
                    if not mid or not sender_id or not text:
                        continue
                    timestamp = int(event.get("timestamp") or entry.get("time") or 0)
                    # Meta messaging timestamps are milliseconds.
                    if timestamp > 10_000_000_000:
                        timestamp //= 1000
                    if not 0 <= timestamp <= 253402300799:
                        continue
                    # Thread key = PSID so replies go back to the same person.
                    jobs.append((entry_id, mid, sender_id, sender_id, text, timestamp, "private"))
        except (ValueError, TypeError, KeyError, AttributeError):
            return request.make_response("Invalid update", status=400)

        for entry_id, change_id, sender_id, sender_name, text, timestamp, kind in jobs:
            identity = f"social-facebook-{account.id}-{change_id}"
            (
                account.with_user(operator)
                .with_context(allowed_company_ids=[account.company_id.id])
                .with_delay(
                    identity_key=identity,
                    max_retries=5,
                    description=f"Social Facebook update {change_id}",
                )
                ._process_facebook_update(entry_id, change_id, sender_id, sender_name, text, timestamp, kind)
            )
        return request.make_response("OK", status=200)

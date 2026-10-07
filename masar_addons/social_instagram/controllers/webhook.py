import hmac
import json

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class SocialInstagramWebhook(http.Controller):
    @http.route(
        "/social/instagram/<string:key>",
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
                    ("platform", "=", "instagram"),
                    ("messaging_enabled", "=", True),
                ],
                limit=1,
            )
        )
        if not account:
            return request.make_response("Not found", status=404)

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
            if data.get("object") not in ("instagram", "page"):
                return request.make_response("OK", status=200)
            jobs = []
            for entry in data.get("entry") or []:
                entry_id = str(entry.get("id") or "")
                for change in entry.get("changes") or []:
                    field = change.get("field")
                    value = change.get("value") or {}
                    # Instagram comment webhooks (Graph).
                    if field not in ("comments", "live_comments"):
                        continue
                    comment_id = str(value.get("id") or "")
                    sender_id = str((value.get("from") or {}).get("id") or "unknown")
                    sender_name = str((value.get("from") or {}).get("username") or sender_id)[:128]
                    text = str(value.get("text") or "")[:16000]
                    if not comment_id or not text:
                        continue
                    raw_ts = value.get("timestamp")
                    if isinstance(raw_ts, (int, float)):
                        timestamp = int(raw_ts)
                    else:
                        timestamp = int(entry.get("time") or 0)
                    if not 0 <= timestamp <= 253402300799:
                        continue
                    jobs.append((entry_id, comment_id, sender_id, sender_name, text, timestamp, "comment"))
        except (ValueError, TypeError, KeyError, AttributeError):
            return request.make_response("Invalid update", status=400)

        for entry_id, change_id, sender_id, sender_name, text, timestamp, kind in jobs:
            identity = f"social-instagram-{account.id}-{change_id}"
            (
                account.with_user(operator)
                .with_context(allowed_company_ids=[account.company_id.id])
                .with_delay(
                    identity_key=identity,
                    max_retries=5,
                    description=f"Social Instagram update {change_id}",
                )
                ._process_instagram_update(entry_id, change_id, sender_id, sender_name, text, timestamp, kind)
            )
        return request.make_response("OK", status=200)

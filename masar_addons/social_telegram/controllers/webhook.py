import hmac
import json

from odoo import http
from odoo.http import request
from odoo.exceptions import UserError


class SocialTelegramWebhook(http.Controller):
    @http.route("/social/telegram/<string:key>", type="http", auth="public", methods=["POST"], csrf=False, save_session=False)
    def receive(self, key, **kwargs):
        # Sudo is limited to authenticated route lookup and credential reference.
        # Processing runs later as an explicit, limited company/account operator.
        if request.httprequest.content_length and request.httprequest.content_length > 65536:
            return request.make_response("Too large", status=413)
        account = request.env["social.account"].sudo().search([("webhook_key", "=", key), ("platform", "=", "telegram"), ("messaging_enabled", "=", True)], limit=1)
        if not account:
            return request.make_response("Not found", status=404)
        try:
            expected = account._secret("webhook_secret_env")
        except UserError:
            return request.make_response("Not configured", status=503)
        supplied = request.httprequest.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(expected, supplied):
            return request.make_response("Forbidden", status=403)
        operator = account.webhook_user_id
        if not operator.active or operator.share or account.company_id not in operator.company_ids or operator not in account.user_ids:
            return request.make_response("Not configured", status=503)
        if not operator.has_group("social.group_social_user"):
            return request.make_response("Not configured", status=503)
        try:
            raw = request.httprequest.get_data()
            if len(raw) > 65536:
                return request.make_response("Too large", status=413)
            data = json.loads(raw)
            message = data.get("message", {})
            # Initial connector intentionally accepts only private text messages.
            if message.get("chat", {}).get("type") != "private" or not message.get("text"):
                return request.make_response("OK", status=200)
            update_id = int(data["update_id"])
            message_id = int(message["message_id"])
            chat_id = int(message["chat"]["id"])
            sender_id = int(message["from"]["id"])
            name = str(message["from"].get("first_name") or sender_id)[:128]
            text = str(message["text"])[:16000]
            timestamp = int(message.get("date") or 0)
            if not 0 <= timestamp <= 253402300799:
                raise ValueError()
        except (ValueError, TypeError, KeyError, AttributeError):
            return request.make_response("Invalid update", status=400)
        account.with_user(operator).with_context(allowed_company_ids=[account.company_id.id]).with_delay(identity_key=f"social-telegram-{account.id}-{update_id}", max_retries=5, description=f"Social Telegram update {update_id}")._process_telegram_update(update_id, message_id, chat_id, sender_id, name, text, timestamp)
        return request.make_response("OK", status=200)

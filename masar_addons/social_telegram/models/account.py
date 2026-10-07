import base64
from datetime import datetime, timezone

import requests

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain


class SocialAccount(models.Model):
    _inherit = "social.account"

    platform = fields.Selection(selection_add=[("telegram", "Telegram Bot")], ondelete={"telegram": "set default"})

    def _validate_target(self, target):
        if self.platform != "telegram":
            return super()._validate_target(target)
        self._secret()
        text = target.platform_content or target.post_id.content
        media = target.post_id.attachment_ids
        if len(media) > 1:
            raise UserError(_("This Telegram connector supports one image or video per publication."))
        limit = 1024 if media else 4096
        if len(text.encode("utf-16-le")) // 2 > limit:
            raise UserError(_("Telegram text exceeds the supported length (%s).", limit))
        if media:
            media.check_access("read")
            if media.type != "binary" or media.mimetype not in ("image/jpeg", "image/png", "video/mp4"):
                raise UserError(_("Use an attached JPEG, PNG or MP4 file."))
            maximum = 10 * 1024 * 1024 if media.mimetype.startswith("image/") else 50 * 1024 * 1024
            if media.file_size > maximum:
                raise UserError(_("Media exceeds the connector upload limit."))

    def _telegram_request(self, method, payload, files=None):
        token = self._secret()
        try:
            response = requests.post(f"https://api.telegram.org/bot{token}/{method}", data=payload, files=files, timeout=(10, 45))
        except requests.RequestException:
            # Never include exception text: requests embeds the secret URL.
            raise DeliveryUncertain() from None
        if response.status_code == 429:
            raise DeliveryTemporary()
        if response.status_code >= 500:
            raise DeliveryUncertain()
        try:
            data = response.json()
        except (ValueError, TypeError):
            raise DeliveryUncertain() from None
        if response.status_code != 200 or not data.get("ok"):
            raise DeliveryPermanent()
        result = data.get("result", {})
        if not isinstance(result, dict) or "message_id" not in result:
            raise DeliveryUncertain()
        return {"id": str(result["message_id"])}

    def _publish_target(self, target):
        if self.platform != "telegram":
            return super()._publish_target(target)
        text = target.platform_content or target.post_id.content
        media = target.post_id.attachment_ids
        if not media:
            return self._telegram_request("sendMessage", {"chat_id": self.external_account_id, "text": text})
        media.check_access("read")
        photo = media.mimetype.startswith("image/")
        key = "photo" if photo else "video"
        return self._telegram_request("sendPhoto" if photo else "sendVideo", {"chat_id": self.external_account_id, "caption": text}, files={key: (media.name, base64.b64decode(media.datas), media.mimetype)})

    def _send_reply(self, conversation, text):
        if self.platform != "telegram":
            return super()._send_reply(conversation, text)
        if conversation.kind != "private" or len(text.encode("utf-16-le")) // 2 > 4096:
            raise DeliveryPermanent()
        return self._telegram_request("sendMessage", {"chat_id": conversation.external_conversation_id, "text": text})

    def _process_telegram_update(self, update_id, message_id, chat_id, sender_id, sender_name, text, timestamp):
        self.ensure_one()
        self._assert_operate("messaging")
        occurred_at = datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None) if timestamp else fields.Datetime.now()
        self.env["social.conversation"]._receive(self, f"{chat_id}:{message_id}", str(chat_id), str(sender_id), sender_name, text, occurred_at)

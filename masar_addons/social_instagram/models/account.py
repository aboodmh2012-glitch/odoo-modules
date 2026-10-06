from datetime import datetime, timezone

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain


class SocialAccount(models.Model):
    _inherit = "social.account"

    platform = fields.Selection(
        selection_add=[("instagram", "Instagram Business")],
        ondelete={"instagram": "set default"},
    )

    def _validate_target(self, target):
        if self.platform != "instagram":
            return super()._validate_target(target)
        self._secret()
        text = target.platform_content or target.post_id.content or ""
        media = target.post_id.attachment_ids
        if len(media) != 1:
            raise UserError(_("Instagram publishing requires exactly one JPEG image attachment."))
        media.check_access("read")
        # Meta Content Publishing accepts JPEG only (not PNG).
        if media.type != "binary" or media.mimetype != "image/jpeg":
            raise UserError(_("Instagram supports JPEG images only in this connector."))
        if media.file_size > 8 * 1024 * 1024:
            raise UserError(_("Instagram image exceeds the 8 MB connector limit."))
        if len(text) > 2200:
            raise UserError(_("Instagram caption exceeds 2,200 characters."))

    def _public_media_url(self, attachment):
        """Instagram Content Publishing requires a publicly reachable image URL."""
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        if not base:
            raise DeliveryPermanent()
        attachment.generate_access_token()
        token = attachment.access_token
        if not token:
            raise DeliveryUncertain()
        return f"{base.rstrip('/')}/web/content/{attachment.id}?access_token={token}&download=true"

    def _instagram_permalink(self, media_id):
        """Fetch the real permalink; never invent a shortcode URL from the media id."""
        try:
            detail = self._meta_graph_request("GET", str(media_id), params={"fields": "permalink"})
        except (DeliveryPermanent, DeliveryTemporary, DeliveryUncertain):
            return False
        return detail.get("permalink") or False

    def _publish_target(self, target):
        if self.platform != "instagram":
            return super()._publish_target(target)
        text = target.platform_content or target.post_id.content or ""
        media = target.post_id.attachment_ids
        media.check_access("read")
        ig_user_id = self.external_account_id
        image_url = self._public_media_url(media)
        container = self._meta_graph_request(
            "POST",
            f"{ig_user_id}/media",
            data={"image_url": image_url, "caption": text},
            timeout=(10, 60),
        )
        creation_id = container.get("id")
        if not creation_id:
            raise DeliveryUncertain()
        published = self._meta_graph_request(
            "POST",
            f"{ig_user_id}/media_publish",
            data={"creation_id": creation_id},
            timeout=(10, 60),
        )
        media_id = published.get("id")
        if not media_id:
            raise DeliveryUncertain()
        return {"id": str(media_id), "url": self._instagram_permalink(media_id)}

    def _send_reply(self, conversation, text):
        if self.platform != "instagram":
            return super()._send_reply(conversation, text)
        if conversation.kind not in ("comment", "mention") or not text.strip():
            raise DeliveryPermanent()
        if len(text) > 2200:
            raise DeliveryPermanent()
        data = self._meta_graph_request(
            "POST",
            f"{conversation.external_conversation_id}/replies",
            data={"message": text},
        )
        reply_id = data.get("id")
        if not reply_id:
            raise DeliveryUncertain()
        return {"id": str(reply_id)}

    def _process_instagram_update(self, entry_id, change_id, sender_id, sender_name, text, timestamp, kind):
        self.ensure_one()
        self._assert_operate("messaging")
        occurred_at = (
            datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None)
            if timestamp
            else fields.Datetime.now()
        )
        self.env["social.conversation"]._receive(
            self,
            change_id,
            change_id,
            str(sender_id),
            sender_name,
            text,
            occurred_at,
            kind=kind,
        )

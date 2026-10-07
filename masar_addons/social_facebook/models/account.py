import base64
from datetime import datetime, timezone

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryUncertain


class SocialAccount(models.Model):
    _inherit = "social.account"

    platform = fields.Selection(
        selection_add=[("facebook", "Facebook Page")],
        ondelete={"facebook": "set default"},
    )

    def _validate_target(self, target):
        if self.platform != "facebook":
            return super()._validate_target(target)
        self._secret()
        text = target.platform_content or target.post_id.content or ""
        media = target.post_id.attachment_ids
        if len(media) > 1:
            raise UserError(_("This Facebook connector supports one image or video per publication."))
        if not text.strip() and not media:
            raise UserError(_("Add text or one media attachment for Facebook."))
        if len(text) > 63206:
            raise UserError(_("Facebook text exceeds the supported length."))
        if media:
            media.check_access("read")
            if media.type != "binary" or media.mimetype not in (
                "image/jpeg",
                "image/png",
                "video/mp4",
            ):
                raise UserError(_("Use an attached JPEG, PNG or MP4 file."))
            maximum = 10 * 1024 * 1024 if media.mimetype.startswith("image/") else 100 * 1024 * 1024
            if media.file_size > maximum:
                raise UserError(_("Media exceeds the connector upload limit."))

    def _publish_target(self, target):
        if self.platform != "facebook":
            return super()._publish_target(target)
        text = target.platform_content or target.post_id.content or ""
        media = target.post_id.attachment_ids
        # Meta Business SDK Page node (create_feed / photos / videos edges).
        if not media:
            data = self._meta_page_publish_text(text)
            post_id = data.get("id")
            if not post_id:
                raise DeliveryUncertain()
            return {"id": str(post_id), "url": f"https://www.facebook.com/{post_id}"}
        media.check_access("read")
        raw = base64.b64decode(media.datas)
        if media.mimetype.startswith("image/"):
            data = self._meta_page_publish_photo(
                text, raw, media.name or "image.jpg", media.mimetype
            )
            post_id = data.get("post_id") or data.get("id")
        else:
            data = self._meta_page_publish_video(
                text, raw, media.name or "video.mp4", media.mimetype
            )
            post_id = data.get("id")
        if not post_id:
            raise DeliveryUncertain()
        return {"id": str(post_id), "url": f"https://www.facebook.com/{post_id}"}

    def _send_reply(self, conversation, text):
        if self.platform != "facebook":
            return super()._send_reply(conversation, text)
        if not text.strip():
            raise DeliveryPermanent()
        if conversation.kind == "private":
            # Messenger: thread id is the PSID (BrightBean meta_messaging).
            if len(text) > 2000:
                raise DeliveryPermanent()
            recipient = conversation.external_conversation_id
            if conversation.profile_id and conversation.profile_id.external_id:
                recipient = conversation.profile_id.external_id
            data = self._meta_send_message(recipient, text)
            mid = (data.get("message_id") or data.get("id") or "")
            if not mid:
                raise DeliveryUncertain()
            return {"id": str(mid)}
        if conversation.kind not in ("comment", "mention"):
            raise DeliveryPermanent()
        if len(text) > 8000:
            raise DeliveryPermanent()
        data = self._meta_page_comment(conversation.external_conversation_id, text)
        comment_id = data.get("id")
        if not comment_id:
            raise DeliveryUncertain()
        return {"id": str(comment_id)}

    def _process_facebook_update(self, entry_id, change_id, sender_id, sender_name, text, timestamp, kind):
        self.ensure_one()
        self._assert_operate("messaging")
        occurred_at = (
            datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None)
            if timestamp
            else fields.Datetime.now()
        )
        # Comments: thread = comment id. Messenger: thread = PSID (sender).
        thread_id = sender_id if kind == "private" else change_id
        self.env["social.conversation"]._receive(
            self,
            change_id,
            thread_id,
            str(sender_id),
            sender_name,
            text,
            occurred_at,
            kind=kind,
        )

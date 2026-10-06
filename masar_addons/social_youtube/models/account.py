# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import base64
import os
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryUncertain

from . import api as yt_api

TITLE_MAX = 100
DESC_MAX = 5000
VIDEO_MIMETYPES = ("video/mp4", "video/quicktime", "video/x-msvideo", "video/webm")
MAX_VIDEO_BYTES = 256 * 1024 * 1024  # connector cap; YouTube allows more via chunking


class SocialAccount(models.Model):
    _inherit = "social.account"

    platform = fields.Selection(
        selection_add=[("youtube", "YouTube Channel")],
        ondelete={"youtube": "set default"},
    )
    google_refresh_token = fields.Char(
        string="Google refresh token",
        groups="social.group_social_admin",
        copy=False,
        help="OAuth refresh token; used to mint short-lived access tokens. Never shown to operators.",
    )

    # ---- app credentials + token refresh ------------------------------------
    def _google_app_credentials(self):
        ICP = self.env["ir.config_parameter"].sudo()
        client_id = (os.environ.get("SOCIAL_YOUTUBE_CLIENT_ID") or "").strip() or (
            ICP.get_param("social.youtube_client_id") or ""
        ).strip()
        client_secret = (os.environ.get("SOCIAL_YOUTUBE_CLIENT_SECRET") or "").strip() or (
            ICP.get_param("social.youtube_client_secret") or ""
        ).strip()
        return client_id, client_secret

    def _youtube_token(self):
        """Return a valid access token, refreshing via the refresh token if needed."""
        self.ensure_one()
        rec = self.sudo()
        now = fields.Datetime.now()
        if rec.access_token and rec.token_expiry and rec.token_expiry > now + timedelta(seconds=60):
            return rec.access_token
        if not rec.google_refresh_token:
            raise DeliveryPermanent()  # needs a re-link
        client_id, client_secret = self._google_app_credentials()
        if not client_id or not client_secret:
            raise DeliveryPermanent()
        data = yt_api.refresh_token(client_id, client_secret, rec.google_refresh_token)
        token = data.get("access_token")
        if not token:
            raise DeliveryPermanent()
        rec.write(
            {
                "access_token": token,
                "token_expiry": now + timedelta(seconds=int(data.get("expires_in") or 3600)),
            }
        )
        return token

    # ---- publish contract (video upload only) --------------------------------
    def _validate_target(self, target):
        if self.platform != "youtube":
            return super()._validate_target(target)
        if not self.sudo().google_refresh_token:
            raise UserError(_("Re-link this YouTube channel before publishing."))
        media = target.post_id.attachment_ids
        if len(media) != 1:
            raise UserError(_("YouTube publishing requires exactly one video attachment."))
        media.check_access("read")
        if media.type != "binary" or media.mimetype not in VIDEO_MIMETYPES:
            raise UserError(_("Attach a video file (MP4/MOV/AVI/WebM) to publish to YouTube."))
        if media.file_size and media.file_size > MAX_VIDEO_BYTES:
            raise UserError(_("Video exceeds the connector upload limit (256 MB)."))
        title = (target.platform_content or target.post_id.name or "").strip()
        if not title:
            raise UserError(_("Set a video title (the post title) before publishing to YouTube."))

    def _publish_target(self, target):
        if self.platform != "youtube":
            return super()._publish_target(target)
        media = target.post_id.attachment_ids[:1]
        media.check_access("read")
        title = (target.platform_content or target.post_id.name or "").strip()[:TITLE_MAX]
        description = (target.post_id.content or "").strip()[:DESC_MAX]
        metadata = {
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        }
        raw = base64.b64decode(media.datas)
        result = yt_api.upload_video(self._youtube_token(), metadata, raw, media.mimetype)
        vid = result.get("id")
        if not vid:
            raise DeliveryUncertain()
        return {"id": str(vid), "url": f"https://youtu.be/{vid}"}

    # ---- reply contract (comment reply — YouTube has no DMs) ------------------
    def _send_reply(self, conversation, text):
        if self.platform != "youtube":
            return super()._send_reply(conversation, text)
        if conversation.kind not in ("comment", "mention") or not (text or "").strip():
            raise DeliveryPermanent()
        body = {"snippet": {"parentId": conversation.external_conversation_id, "textOriginal": text}}
        resp = yt_api.data_request(
            "POST", "comments?part=snippet", self._youtube_token(), json_body=body
        )
        try:
            data = resp.json() or {}
        except (ValueError, TypeError):
            raise DeliveryUncertain()
        cid = data.get("id")
        if not cid:
            raise DeliveryUncertain()
        return {"id": str(cid)}

    # ---- insights ------------------------------------------------------------
    def action_youtube_stats(self):
        self.ensure_one()
        if not self.env.user.has_group("social.group_social_admin"):
            raise UserError(_("Only Social Connection Administrators can read YouTube insights."))
        try:
            resp = yt_api.data_request(
                "GET",
                "channels",
                self._youtube_token(),
                params={"part": "statistics", "mine": "true"},
            )
            items = (resp.json() or {}).get("items") or []
        except (DeliveryPermanent, DeliveryUncertain):
            raise UserError(_("Could not read YouTube statistics. Re-link the channel."))
        stats = (items[0].get("statistics") if items else {}) or {}
        self.sudo().write({"last_sync_at": fields.Datetime.now(), "connection_status": "connected"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("YouTube"),
                "message": _(
                    "Subscribers: %(subs)s · Views: %(views)s · Videos: %(videos)s",
                    subs=stats.get("subscriberCount", "?"),
                    views=stats.get("viewCount", "?"),
                    videos=stats.get("videoCount", "?"),
                ),
                "type": "success",
                "sticky": False,
            },
        }

    # ---- entry points --------------------------------------------------------
    @api.model
    def action_connect_youtube(self, *args, **kwargs):
        del args, kwargs
        self.env["social.account"].check_access("create")
        if "social.youtube.oauth" not in self.env:
            raise UserError(_("Install Social · YouTube first."))
        return self.env["social.youtube.oauth"].action_start()

    def action_connect_provider(self, *args, **kwargs):
        if self.platform == "youtube" and "social.youtube.oauth" in self.env:
            if not self.env.user.has_group("social.group_social_admin"):
                raise AccessError(_("Only Social Connection Administrators can link accounts."))
            return self.env["social.youtube.oauth"].action_start()
        return super().action_connect_provider(*args, **kwargs)

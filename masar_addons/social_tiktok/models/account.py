# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import base64
import os
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryUncertain

from . import api as tt_api

CAPTION_MAX = 2200
VIDEO_MIMETYPES = ("video/mp4", "video/quicktime", "video/webm")
MAX_VIDEO_BYTES = 64 * 1024 * 1024  # single-chunk cap for this connector


class SocialAccount(models.Model):
    _inherit = "social.account"

    platform = fields.Selection(
        selection_add=[("tiktok", "TikTok")],
        ondelete={"tiktok": "set default"},
    )
    tiktok_refresh_token = fields.Char(
        string="TikTok refresh token",
        groups="social.group_social_admin",
        copy=False,
        help="OAuth refresh token; used to mint short-lived access tokens. Never shown to operators.",
    )

    def _tiktok_app_credentials(self):
        ICP = self.env["ir.config_parameter"].sudo()
        client_key = (os.environ.get("SOCIAL_TIKTOK_CLIENT_KEY") or "").strip() or (
            ICP.get_str("social.tiktok_client_key") or ""
        ).strip()
        client_secret = (os.environ.get("SOCIAL_TIKTOK_CLIENT_SECRET") or "").strip() or (
            ICP.get_str("social.tiktok_client_secret") or ""
        ).strip()
        return client_key, client_secret

    def _tiktok_token(self):
        self.ensure_one()
        rec = self.sudo()
        now = fields.Datetime.now()
        if rec.access_token and rec.token_expiry and rec.token_expiry > now + timedelta(seconds=60):
            return rec.access_token
        if not rec.tiktok_refresh_token:
            raise DeliveryPermanent()
        client_key, client_secret = self._tiktok_app_credentials()
        if not client_key or not client_secret:
            raise DeliveryPermanent()
        data = tt_api.refresh_token(client_key, client_secret, rec.tiktok_refresh_token)
        token = data.get("access_token")
        if not token:
            raise DeliveryPermanent()
        vals = {
            "access_token": token,
            "token_expiry": now + timedelta(seconds=int(data.get("expires_in") or 86400)),
        }
        if data.get("refresh_token"):
            vals["tiktok_refresh_token"] = data["refresh_token"]
        rec.write(vals)
        return token

    # ---- publish contract (video only; TikTok has no comment/DM API) ---------
    def _validate_target(self, target):
        if self.platform != "tiktok":
            return super()._validate_target(target)
        if not self.sudo().tiktok_refresh_token:
            raise UserError(_("Re-link this TikTok account before publishing."))
        media = target.post_id.attachment_ids
        if len(media) != 1:
            raise UserError(_("TikTok publishing requires exactly one video attachment."))
        media.check_access("read")
        if media.type != "binary" or media.mimetype not in VIDEO_MIMETYPES:
            raise UserError(_("Attach a video file (MP4/MOV/WebM) to publish to TikTok."))
        if media.file_size and media.file_size > MAX_VIDEO_BYTES:
            raise UserError(_("Video exceeds the connector upload limit (64 MB)."))

    def _choose_privacy(self, token):
        """Query creator info for allowed privacy levels (required before direct post)."""
        info = tt_api.api_post("post/publish/creator_info/query/", token)
        options = ((info.get("data") or {}).get("privacy_level_options")) or []
        if "PUBLIC_TO_EVERYONE" in options:
            return "PUBLIC_TO_EVERYONE"
        return options[0] if options else "SELF_ONLY"

    def _publish_target(self, target):
        if self.platform != "tiktok":
            return super()._publish_target(target)
        media = target.post_id.attachment_ids[:1]
        media.check_access("read")
        caption = (target.platform_content or target.post_id.content or target.post_id.name or "").strip()[:CAPTION_MAX]
        raw = base64.b64decode(media.datas)
        size = len(raw)
        token = self._tiktok_token()
        privacy = self._choose_privacy(token)
        init = tt_api.api_post(
            "post/publish/video/init/",
            token,
            json_body={
                "post_info": {
                    "title": caption,
                    "privacy_level": privacy,
                    "disable_comment": False,
                    "disable_duet": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": size,
                    "chunk_size": size,
                    "total_chunk_count": 1,
                },
            },
        )
        data = init.get("data") or {}
        publish_id = data.get("publish_id")
        upload_url = data.get("upload_url")
        if not publish_id or not upload_url:
            raise DeliveryUncertain()
        tt_api.upload_chunk(upload_url, raw, media.mimetype)
        # Publishing is asynchronous on TikTok's side; the publish_id is the
        # durable handle (status can be polled via post/publish/status/fetch/).
        return {"id": str(publish_id)}

    # ---- entry points --------------------------------------------------------
    @api.model
    def action_connect_tiktok(self, *args, **kwargs):
        del args, kwargs
        self.env["social.account"].check_access("create")
        if "social.tiktok.oauth" not in self.env:
            raise UserError(_("Install Social · TikTok first."))
        return self.env["social.tiktok.oauth"].action_start()

    def action_connect_provider(self, *args, **kwargs):
        if self.platform == "tiktok" and "social.tiktok.oauth" in self.env:
            if not self.env.user.has_group("social.group_social_admin"):
                raise AccessError(_("Only Social Connection Administrators can link accounts."))
            return self.env["social.tiktok.oauth"].action_start()
        return super().action_connect_provider(*args, **kwargs)

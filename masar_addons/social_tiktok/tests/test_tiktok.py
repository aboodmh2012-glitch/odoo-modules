# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import time
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.social_tiktok.models import api as tt_api


@tagged("post_install", "-at_install")
class TestSocialTiktok(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids = [
            (4, cls.env.ref("social.group_social_admin").id),
            (4, cls.env.ref("social.group_social_user").id),
            (4, cls.env.ref("social.group_social_manager").id),
            (4, cls.env.ref("social.group_social_publisher").id),
        ]
        ICP = cls.env["ir.config_parameter"].sudo()
        ICP.set_str("social.tiktok_client_key", "key-123")
        ICP.set_str("social.tiktok_client_secret", "sekret")
        ICP.set_str("web.base.url", "https://example.test")
        cls.oauth = cls.env["social.tiktok.oauth"]
        cls.account = cls.env["social.account"].create(
            {
                "name": "MASAR TikTok",
                "platform": "tiktok",
                "external_account_id": "openid-1",
                "access_token": "ACCESS",
                "tiktok_refresh_token": "REFRESH",
                "token_expiry": fields.Datetime.now() + timedelta(hours=12),
                "publishing_enabled": True,
                "connection_status": "connected",
            }
        )

    def _video_post(self, mimetype="video/mp4"):
        att = self.env["ir.attachment"].create(
            {"name": "v.mp4", "raw": b"clip", "mimetype": mimetype}
        )
        post = self.env["social.post"].create({"name": "Trend", "content": "caption"})
        post.attachment_ids = [(6, 0, att.ids)]
        target = self.env["social.post.target"].create(
            {"post_id": post.id, "account_id": self.account.id}
        )
        return post, target

    # ---- state / scopes ------------------------------------------------------
    def test_state_roundtrip(self):
        state = self.oauth._sign_state({"uid": self.env.uid, "ts": int(time.time())})
        self.assertEqual(self.oauth._parse_state(state)["uid"], self.env.uid)

    def test_state_tamper(self):
        state = self.oauth._sign_state({"uid": self.env.uid, "ts": int(time.time())})
        sig, body = state.split(".", 1)
        with self.assertRaises(UserError):
            self.oauth._parse_state(sig + "." + body.replace("uid", "x"))

    def test_scopes_publish_only(self):
        self.assertIn("video.publish", tt_api.SCOPES)
        self.assertNotIn("comment", tt_api.SCOPES.lower())

    def test_messaging_disabled(self):
        # No comment/DM API on TikTok — the account never enables messaging.
        self.assertFalse(self.account.messaging_enabled)

    # ---- token refresh -------------------------------------------------------
    def test_token_refresh(self):
        self.account.sudo().write({"token_expiry": fields.Datetime.now() - timedelta(minutes=1)})
        with patch.object(
            tt_api, "refresh_token",
            return_value={"access_token": "NEW", "expires_in": 86400, "refresh_token": "R2"},
        ):
            self.assertEqual(self.account._tiktok_token(), "NEW")
        self.assertEqual(self.account.sudo().access_token, "NEW")
        self.assertEqual(self.account.sudo().tiktok_refresh_token, "R2")

    # ---- validation ----------------------------------------------------------
    def test_validate_requires_video(self):
        post = self.env["social.post"].create({"name": "t", "content": "x"})
        target = self.env["social.post.target"].create(
            {"post_id": post.id, "account_id": self.account.id}
        )
        with self.assertRaises(UserError):
            self.account._validate_target(target)

    def test_validate_ok(self):
        _p, target = self._video_post()
        self.account._validate_target(target)

    # ---- reply not supported --------------------------------------------------
    def test_reply_not_supported(self):
        # TikTok has no reply API; _send_reply falls through to the base method,
        # which raises regardless of the conversation passed.
        with self.assertRaises(UserError):
            self.account._send_reply(self.env["social.conversation"], "hello")

    # ---- publish flow (mocked) -----------------------------------------------
    def test_publish_direct_post(self):
        _p, target = self._video_post()
        calls = []

        def fake_post(path, token, json_body=None, timeout=(10, 60)):
            calls.append(path)
            if path == "post/publish/creator_info/query/":
                return {"data": {"privacy_level_options": ["PUBLIC_TO_EVERYONE", "SELF_ONLY"]}}
            if path == "post/publish/video/init/":
                return {"data": {"publish_id": "pub-1", "upload_url": "https://up.tiktok/x"}}
            return {"data": {}}

        with patch.object(self.account.__class__, "_tiktok_token", return_value="TT"), patch.object(
            tt_api, "api_post", side_effect=fake_post
        ), patch.object(tt_api, "upload_chunk", return_value=True) as up:
            res = self.account._publish_target(target)
        self.assertEqual(res["id"], "pub-1")
        self.assertIn("post/publish/creator_info/query/", calls)
        self.assertIn("post/publish/video/init/", calls)
        up.assert_called_once()

    # ---- link flow -----------------------------------------------------------
    def test_exchange_and_link(self):
        def fake_exchange(key, secret, code, redirect):
            return {
                "access_token": "A",
                "refresh_token": "R",
                "open_id": "openid-9",
                "expires_in": 86400,
            }

        with patch.object(tt_api, "exchange_token", side_effect=fake_exchange), patch.object(
            tt_api, "get_user_info", return_value={"display_name": "MASAR Official"}
        ):
            access, refresh, expires_in, rows = self.oauth.exchange_code("code")
        self.assertEqual(rows, [{"external_id": "openid-9", "name": "MASAR Official"}])
        action = self.oauth.open_page_wizard(access, refresh, expires_in, rows)
        wiz = self.env["social.tiktok.link.wizard"].browse(action["res_id"])
        wiz.line_ids[:1].action_select()
        linked = self.env["social.account"].search(
            [("platform", "=", "tiktok"), ("external_account_id", "=", "openid-9")]
        )
        self.assertTrue(linked)
        self.assertFalse(linked.messaging_enabled)

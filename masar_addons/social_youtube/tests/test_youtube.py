# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import base64
import time
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.social_youtube.models import api as yt_api


def _resp(payload=None, headers=None, status=200):
    return SimpleNamespace(status_code=status, headers=headers or {}, json=lambda: payload or {})


@tagged("post_install", "-at_install")
class TestSocialYoutube(TransactionCase):
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
        ICP.set_param("social.youtube_client_id", "client-123")
        ICP.set_param("social.youtube_client_secret", "sekret")
        ICP.set_param("web.base.url", "https://example.test")
        cls.oauth = cls.env["social.youtube.oauth"]
        cls.account = cls.env["social.account"].create(
            {
                "name": "MASAR Channel",
                "platform": "youtube",
                "external_account_id": "UC123",
                "access_token": "ACCESS",
                "google_refresh_token": "REFRESH",
                "token_expiry": fields.Datetime.now() + timedelta(hours=1),
                "publishing_enabled": True,
                "messaging_enabled": True,
                "connection_status": "connected",
            }
        )

    def _video_post(self, mimetype="video/mp4"):
        att = self.env["ir.attachment"].create(
            {"name": "v.mp4", "datas": base64.b64encode(b"video-bytes").decode(), "mimetype": mimetype}
        )
        post = self.env["social.post"].create({"name": "My clip", "content": "desc"})
        post.attachment_ids = [(6, 0, att.ids)]
        target = self.env["social.post.target"].create(
            {"post_id": post.id, "account_id": self.account.id}
        )
        return post, target

    # ---- OAuth state ---------------------------------------------------------
    def test_state_roundtrip(self):
        state = self.oauth._sign_state({"uid": self.env.uid, "ts": int(time.time())})
        self.assertEqual(self.oauth._parse_state(state)["uid"], self.env.uid)

    def test_state_tamper(self):
        state = self.oauth._sign_state({"uid": self.env.uid, "ts": int(time.time())})
        sig, body = state.split(".", 1)
        with self.assertRaises(UserError):
            self.oauth._parse_state(sig + "." + body.replace("uid", "uidX"))

    def test_scopes_no_dm(self):
        self.assertIn("youtube.upload", yt_api.SCOPES)
        self.assertNotIn("message", yt_api.SCOPES.lower())

    # ---- token refresh -------------------------------------------------------
    def test_token_refresh_when_expired(self):
        self.account.sudo().write({"token_expiry": fields.Datetime.now() - timedelta(minutes=5)})
        with patch.object(yt_api, "refresh_token", return_value={"access_token": "NEW", "expires_in": 3600}):
            token = self.account._youtube_token()
        self.assertEqual(token, "NEW")
        self.assertEqual(self.account.sudo().access_token, "NEW")

    def test_token_kept_when_valid(self):
        with patch.object(yt_api, "refresh_token", side_effect=AssertionError("should not refresh")):
            self.assertEqual(self.account._youtube_token(), "ACCESS")

    # ---- validation ----------------------------------------------------------
    def test_validate_requires_video(self):
        post = self.env["social.post"].create({"name": "text only", "content": "hi"})
        target = self.env["social.post.target"].create(
            {"post_id": post.id, "account_id": self.account.id}
        )
        with self.assertRaises(UserError):
            self.account._validate_target(target)

    def test_validate_rejects_non_video(self):
        _p, target = self._video_post(mimetype="image/png")
        with self.assertRaises(UserError):
            self.account._validate_target(target)

    def test_validate_ok(self):
        _p, target = self._video_post()
        self.account._validate_target(target)

    # ---- publish -------------------------------------------------------------
    def test_publish_uploads_video(self):
        _p, target = self._video_post()
        captured = {}

        def fake_upload(token, metadata, raw, mimetype, timeout=(10, 300)):
            captured.update(token=token, metadata=metadata, mimetype=mimetype, raw=raw)
            return {"id": "VID123"}

        with patch.object(self.account.__class__, "_youtube_token", return_value="TT"), patch.object(
            yt_api, "upload_video", side_effect=fake_upload
        ):
            res = self.account._publish_target(target)
        self.assertEqual(res["id"], "VID123")
        self.assertEqual(res["url"], "https://youtu.be/VID123")
        self.assertEqual(captured["metadata"]["snippet"]["title"], "My clip")
        self.assertEqual(captured["raw"], b"video-bytes")

    # ---- reply (comment) -----------------------------------------------------
    def test_reply_posts_comment(self):
        conversation = self.env["social.conversation"].sudo()._receive(
            self.account, "ext-1", "COMMENT_PARENT", "prof-1", "Fan", "great!", kind="comment"
        )
        captured = {}

        def fake_req(method, path, token, params=None, json_body=None, timeout=(10, 45)):
            captured.update(path=path, json_body=json_body)
            return _resp(payload={"id": "COMMENT_REPLY"})

        with patch.object(self.account.__class__, "_youtube_token", return_value="TT"), patch.object(
            yt_api, "data_request", side_effect=fake_req
        ):
            res = self.account._send_reply(conversation, "thanks")
        self.assertEqual(res["id"], "COMMENT_REPLY")
        self.assertEqual(captured["json_body"]["snippet"]["parentId"], "COMMENT_PARENT")

    # ---- link flow (mocked) --------------------------------------------------
    def test_exchange_and_link(self):
        def fake_exchange(cid, secret, code, redirect):
            return {"access_token": "A", "refresh_token": "R", "expires_in": 3600}

        def fake_req(method, path, token, params=None, json_body=None, timeout=(10, 45)):
            return _resp(payload={"items": [{"id": "UC999", "snippet": {"title": "New Channel"}}]})

        with patch.object(yt_api, "exchange_token", side_effect=fake_exchange), patch.object(
            yt_api, "data_request", side_effect=fake_req
        ):
            access, refresh, expires_in, rows = self.oauth.exchange_code("code")
        self.assertEqual((access, refresh), ("A", "R"))
        self.assertEqual(rows, [{"external_id": "UC999", "name": "New Channel"}])
        action = self.oauth.open_page_wizard(access, refresh, expires_in, rows)
        wiz = self.env["social.youtube.link.wizard"].browse(action["res_id"])
        wiz.line_ids[:1].action_select()
        linked = self.env["social.account"].search(
            [("platform", "=", "youtube"), ("external_account_id", "=", "UC999")]
        )
        self.assertTrue(linked)
        self.assertEqual(linked.sudo().google_refresh_token, "R")

    def test_missing_refresh_token_raises(self):
        def fake_exchange(cid, secret, code, redirect):
            return {"access_token": "A", "expires_in": 3600}  # no refresh_token

        with patch.object(yt_api, "exchange_token", side_effect=fake_exchange):
            with self.assertRaises(UserError):
                self.oauth.exchange_code("code")

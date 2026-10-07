# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import time
from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.social_linkedin.models import api as li_api


def _resp(headers=None, payload=None, status=200):
    return SimpleNamespace(
        status_code=status,
        headers=headers or {},
        json=lambda: payload or {},
    )


@tagged("post_install", "-at_install")
class TestSocialLinkedin(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids = [
            (4, cls.env.ref("social.group_social_admin").id),
            (4, cls.env.ref("social.group_social_user").id),
            (4, cls.env.ref("social.group_social_manager").id),
            (4, cls.env.ref("social.group_social_publisher").id),
        ]
        # Server-owned app credentials via ICP (env vars are not set in CI).
        ICP = cls.env["ir.config_parameter"].sudo()
        ICP.set_param("social.linkedin_client_id", "1234567890")
        ICP.set_param("social.linkedin_client_secret", "top-secret-value")
        ICP.set_param("web.base.url", "https://example.test")
        cls.oauth = cls.env["social.linkedin.oauth"]
        cls.account = cls.env["social.account"].create(
            {
                "name": "MASAR LinkedIn",
                "platform": "linkedin",
                "external_account_id": "999",
                "access_token": "PAGE-TOKEN",
                "publishing_enabled": True,
                "messaging_enabled": True,
                "connection_status": "connected",
            }
        )

    # ---- OAuth state security -------------------------------------------------
    def test_state_roundtrip_and_binding(self):
        state = self.oauth._sign_state(
            {"uid": self.env.uid, "company_id": self.env.company.id, "ts": int(time.time()), "nonce": "x"}
        )
        payload = self.oauth._parse_state(state)
        self.assertEqual(payload["uid"], self.env.uid)

    def test_state_tamper_rejected(self):
        state = self.oauth._sign_state({"uid": self.env.uid, "ts": int(time.time())})
        sig, body = state.split(".", 1)
        tampered = sig + "." + body.replace('"uid"', '"uidX"')
        with self.assertRaises(UserError):
            self.oauth._parse_state(tampered)

    def test_state_expired_rejected(self):
        state = self.oauth._sign_state({"uid": self.env.uid, "ts": int(time.time()) - 1000})
        with self.assertRaises(UserError):
            self.oauth._parse_state(state)

    def test_missing_credentials_raises(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("social.linkedin_client_id", "")
        ICP.set_param("social.linkedin_client_secret", "")
        with patch.dict("os.environ", {}, clear=False) as _env:
            import os
            os.environ.pop("SOCIAL_LINKEDIN_CLIENT_ID", None)
            os.environ.pop("SOCIAL_LINKEDIN_CLIENT_SECRET", None)
            with self.assertRaises(UserError):
                self.oauth._app_credentials()

    def test_scopes_have_no_dm(self):
        # LinkedIn has no organization DM API — connector must never request one.
        self.assertNotIn("messaging", li_api.SCOPES)
        self.assertIn("w_organization_social", li_api.SCOPES)

    # ---- capability / validation ---------------------------------------------
    def _make_post(self, content="Hello world", attach=False):
        vals = {"name": "P", "content": content}
        post = self.env["social.post"].create(vals)
        target = self.env["social.post.target"].create(
            {"post_id": post.id, "account_id": self.account.id}
        )
        if attach:
            att = self.env["ir.attachment"].create(
                {"name": "a.png", "datas": "aGk=", "mimetype": "image/png"}
            )
            post.attachment_ids = [(6, 0, att.ids)]
        return post, target

    def test_validate_rejects_attachment(self):
        _post, target = self._make_post(attach=True)
        with self.assertRaises(UserError):
            self.account._validate_target(target)

    def test_validate_rejects_empty(self):
        _post, target = self._make_post(content="   ")
        with self.assertRaises(UserError):
            self.account._validate_target(target)

    def test_validate_ok(self):
        _post, target = self._make_post()
        self.account._validate_target(target)  # no raise

    # ---- publish --------------------------------------------------------------
    def test_publish_builds_post_and_returns_urn(self):
        _post, target = self._make_post(content="Launch day")
        captured = {}

        def fake(method, path, token, version, json=None, params=None, timeout=(10, 45)):
            captured.update(method=method, path=path, token=token, json=json)
            return _resp(headers={"x-restli-id": "urn:li:share:123"})

        with patch.object(li_api, "rest_request", side_effect=fake):
            res = self.account._publish_target(target)
        self.assertEqual(res["id"], "urn:li:share:123")
        self.assertIn("urn:li:share:123", res["url"])
        self.assertEqual(captured["path"], "posts")
        self.assertEqual(captured["json"]["author"], "urn:li:organization:999")
        self.assertEqual(captured["json"]["commentary"], "Launch day")
        self.assertEqual(captured["token"], "PAGE-TOKEN")

    # ---- reply (comment) ------------------------------------------------------
    def test_reply_posts_comment(self):
        conv = self.env["social.conversation"]
        # Build a minimal comment conversation via the private receiver.
        conversation = conv.sudo()._receive(
            self.account, "ext-1", "urn:li:share:777", "prof-1", "Fan", "nice!", kind="comment"
        )
        captured = {}

        def fake(method, path, token, version, json=None, params=None, timeout=(10, 45)):
            captured.update(path=path, json=json)
            return _resp(headers={"x-restli-id": "urn:li:comment:1"})

        with patch.object(li_api, "rest_request", side_effect=fake):
            res = self.account._send_reply(conversation, "thank you")
        self.assertEqual(res["id"], "urn:li:comment:1")
        self.assertEqual(captured["path"], "socialActions/urn:li:share:777/comments")
        self.assertEqual(captured["json"]["message"]["text"], "thank you")

    # ---- linking flow (mocked network) ---------------------------------------
    def test_exchange_and_link(self):
        def fake_exchange(cid, secret, code, redirect):
            return {"access_token": "NEW-TOKEN", "expires_in": 5184000}

        def fake_rest(method, path, token, version, json=None, params=None, timeout=(10, 45)):
            if path == "organizationAcls":
                return _resp(payload={"elements": [{"organization": "urn:li:organization:42"}]})
            if path.startswith("organizations/"):
                return _resp(payload={"id": 42, "localizedName": "MASAR Global"})
            return _resp(payload={})

        with patch.object(li_api, "exchange_token", side_effect=fake_exchange), patch.object(
            li_api, "rest_request", side_effect=fake_rest
        ):
            token, expires_in, rows = self.oauth.exchange_code("the-code")
        self.assertEqual(token, "NEW-TOKEN")
        self.assertEqual(rows, [{"external_id": "42", "name": "MASAR Global"}])
        action = self.oauth.open_page_wizard(token, expires_in, rows)
        wiz = self.env["social.linkedin.link.wizard"].browse(action["res_id"])
        wiz.line_ids[:1].action_select()
        linked = self.env["social.account"].search(
            [("platform", "=", "linkedin"), ("external_account_id", "=", "42")]
        )
        self.assertTrue(linked)
        self.assertEqual(linked.connection_status, "connected")
        self.assertTrue(linked.publishing_enabled)

import os
from unittest.mock import patch
from types import SimpleNamespace

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged("post_install", "-at_install")
class TestInstagram(TransactionCase):
    def setUp(self):
        super().setUp()
        self.account = self.env["social.account"].create(
            {
                "name": "IG Business",
                "platform": "instagram",
                "external_account_id": "17841400000000",
                "access_token": "never-log-this-ig-token",
                "meta_app_secret_env": "SOCIAL_TEST_IG_APP_SECRET",
                "connection_status": "connected",
            }
        )
        self.patch(
            os,
            "environ",
            {
                "SOCIAL_TEST_IG_APP_SECRET": "never-log-this-app-secret",
                "SOCIAL_META_APP_ID": "123456789012345",
                "SOCIAL_META_APP_SECRET": "never-log-this-app-secret",
            },
        )

    def test_publish_two_step(self):
        attachment = self.env["ir.attachment"].create(
            {
                "name": "pic.jpg",
                "type": "binary",
                "datas": "iVBORw0KGgo=",
                "mimetype": "image/jpeg",
            }
        )
        self.env["ir.config_parameter"].sudo().set_param("web.base.url", "https://example.test")
        post = self.env["social.post"].create(
            {
                "name": "IG post",
                "content": "Caption",
                "attachment_ids": [(6, 0, [attachment.id])],
            }
        )
        target = SimpleNamespace(platform_content="Caption", post_id=post)

        def fake_graph(method, path, data=None, files=None, params=None, timeout=(10, 45)):
            if path.endswith("/media"):
                return {"id": "container-1"}
            if path.endswith("/media_publish"):
                return {"id": "media-9"}
            if path == "media-9":
                return {"permalink": "https://www.instagram.com/p/ABC123/"}
            return {}

        with patch.object(type(self.account), "_meta_graph_request", side_effect=fake_graph):
            self.account._validate_target(target)
            result = self.account._publish_target(target)
            self.assertEqual(result["id"], "media-9")
            self.assertEqual(result["url"], "https://www.instagram.com/p/ABC123/")

    def test_missing_media_rejected(self):
        post = self.env["social.post"].create({"name": "No media", "content": "x"})
        with self.assertRaises(UserError):
            self.account._validate_target(SimpleNamespace(platform_content="x", post_id=post))

    def test_png_rejected(self):
        attachment = self.env["ir.attachment"].create(
            {
                "name": "pic.png",
                "type": "binary",
                "datas": "iVBORw0KGgo=",
                "mimetype": "image/png",
            }
        )
        post = self.env["social.post"].create(
            {
                "name": "PNG",
                "content": "x",
                "attachment_ids": [(6, 0, [attachment.id])],
            }
        )
        with self.assertRaises(UserError):
            self.account._validate_target(SimpleNamespace(platform_content="x", post_id=post))

import os
from unittest.mock import Mock, patch

from odoo.tests import TransactionCase, tagged
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain


@tagged("post_install", "-at_install")
class TestFacebook(TransactionCase):
    def setUp(self):
        super().setUp()
        self.account = self.env["social.account"].create(
            {
                "name": "FB Page",
                "platform": "facebook",
                "external_account_id": "111222333",
                "access_token": "never-log-this-page-token",
                "meta_app_secret_env": "SOCIAL_TEST_FB_APP_SECRET",
                "connection_status": "connected",
            }
        )
        self.patch(
            os,
            "environ",
            {
                "SOCIAL_TEST_FB_APP_SECRET": "never-log-this-app-secret",
                "SOCIAL_META_APP_ID": "123456789012345",
                "SOCIAL_META_APP_SECRET": "never-log-this-app-secret",
            },
        )

    def test_text_delivery_via_sdk(self):
        with patch(
            "odoo.addons.social_meta.models.account.page_create_feed",
            return_value={"id": "111222333_99"},
        ) as publish:
            result = self.account._meta_page_publish_text("Hello")
            self.assertEqual(result["id"], "111222333_99")
            self.assertEqual(publish.call_args.args[1], "111222333")
            self.assertEqual(publish.call_args.args[2], "Hello")

    def test_graph_request_uses_sdk(self):
        with patch(
            "odoo.addons.social_meta.models.account.graph_call",
            return_value={"id": "111222333_99"},
        ) as call:
            with patch.object(type(self.account), "_meta_facebook_api", return_value=Mock()):
                result = self.account._meta_graph_request(
                    "POST", "111222333/feed", data={"message": "Hello"}
                )
            self.assertEqual(result["id"], "111222333_99")
            self.assertEqual(call.call_args.args[1], "POST")
            self.assertEqual(call.call_args.args[2], "111222333/feed")

    def test_error_classification(self):
        from facebook_business.exceptions import FacebookRequestError
        from odoo.addons.social_meta.models import sdk as sdk_mod

        for status, code, exception in (
            (429, 1, DeliveryTemporary),
            (400, 4, DeliveryTemporary),
            (403, 10, DeliveryPermanent),
            (503, 1, DeliveryUncertain),
        ):
            err = FacebookRequestError(
                message="redacted",
                request_context={"method": "POST", "path": "x", "params": {}, "headers": {}, "files": {}},
                http_status=status,
                http_headers={},
                body=f'{{"error":{{"code":{code},"message":"x"}}}}',
            )
            with self.assertRaises(exception):
                sdk_mod.raise_delivery_from_sdk(err)

    def test_network_failure_redacted(self):
        with patch(
            "odoo.addons.social_meta.models.account.graph_call",
            side_effect=DeliveryUncertain(),
        ):
            with patch.object(type(self.account), "_meta_facebook_api", return_value=Mock()):
                with self.assertRaises(DeliveryUncertain) as caught:
                    self.account._meta_graph_request("POST", "111222333/feed", data={})
            self.assertNotIn("never-log-this-page-token", str(caught.exception))

    def test_signature_verification(self):
        import hashlib
        import hmac

        raw = b'{"object":"page"}'
        digest = hmac.new(b"never-log-this-app-secret", raw, hashlib.sha256).hexdigest()
        self.assertTrue(self.account._verify_meta_signature(raw, f"sha256={digest}"))
        self.assertFalse(self.account._verify_meta_signature(raw, "sha256=deadbeef"))

    def test_sdk_module_exports_v26(self):
        from odoo.addons.social_meta.models.sdk import GRAPH_VERSION, sdk_available

        self.assertEqual(GRAPH_VERSION, "v26.0")
        self.assertTrue(sdk_available())

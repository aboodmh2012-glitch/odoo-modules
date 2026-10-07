from unittest.mock import patch

from odoo.tests import TransactionCase, tagged, new_test_user


@tagged("post_install", "-at_install")
class TestSocialMetaOauth(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = new_test_user(cls.env, login="social-meta-admin", groups="social.group_social_admin")
        cls.env["ir.config_parameter"].sudo().set_str("social.meta_app_id", "123456789")
        cls.env["ir.config_parameter"].sudo().set_str("social.meta_app_secret", "test-secret")
        cls.env["ir.config_parameter"].sudo().set_str("web.base.url", "https://example.test")

    def test_link_account_opens_facebook(self):
        action = self.env["social.meta.oauth"].with_user(self.admin).action_start("facebook")
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn("facebook.com", action["url"])
        self.assertIn("client_id=123456789", action["url"])
        self.assertIn("oauth%2Fcallback", action["url"])
        self.assertIn("auth_type=rerequest", action["url"])
        self.assertIn("pages_messaging", action["url"])

    def test_missing_app_credentials_opens_setup(self):
        self.env["ir.config_parameter"].sudo().set_str("social.meta_app_id", False)
        self.env["ir.config_parameter"].sudo().set_str("social.meta_app_secret", False)
        with patch.dict("os.environ", {"SOCIAL_META_APP_ID": "", "SOCIAL_META_APP_SECRET": ""}, clear=False):
            action = self.env["social.meta.oauth"].with_user(self.admin).action_start("facebook")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "social.meta.app.config")

    def test_wizard_creates_account_with_token(self):
        wiz = self.env["social.meta.link.wizard"].with_user(self.admin).create(
            {
                "media_type": "facebook",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "My Page",
                            "external_id": "page-99",
                            "page_id": "page-99",
                            "access_token": "PAGE_TOKEN_VALUE",
                        },
                    )
                ],
            }
        )
        action = wiz.line_ids[0].action_select()
        account = self.env["social.account"].browse(action["res_id"])
        self.assertEqual(account.platform, "facebook")
        self.assertEqual(account.external_account_id, "page-99")
        self.assertEqual(account.with_user(self.admin).meta_page_id, "page-99")
        self.assertEqual(account.connection_status, "connected")
        self.assertTrue(account.last_sync_at)
        self.assertIn("pages_manage_posts", account.with_user(self.admin).granted_scopes or "")
        self.assertIn("pages_messaging", account.with_user(self.admin).granted_scopes or "")
        self.assertIn("read_insights", account.with_user(self.admin).granted_scopes or "")
        self.assertEqual(account.with_user(self.admin).access_token, "PAGE_TOKEN_VALUE")
        self.assertEqual(account._secret(), "PAGE_TOKEN_VALUE")

    def test_connect_facebook_opens_oauth(self):
        # Simulate list-button RPC that may pass an extra positional argument.
        action = self.env["social.account"].with_user(self.admin).action_connect_facebook([])
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn("facebook.com", action["url"])
        self.assertIn("pages_show_list", action["url"])
        self.assertIn("read_insights", action["url"])
        self.assertIn("pages_messaging", action["url"])
        self.assertIn("auth_type=rerequest", action["url"])

    def test_normalize_app_id_digits(self):
        from odoo.addons.social_meta.models.app_config import normalize_meta_app_id

        self.assertEqual(normalize_meta_app_id(" 123 456 789 "), "123456789")
        self.assertEqual(normalize_meta_app_id("MyApp"), "")
        self.assertEqual(normalize_meta_app_id("id:9876543210"), "9876543210")

    def test_connect_wizard_rejects_app_name(self):
        wiz = self.env["social.meta.app.config"].with_user(self.admin).create(
            {
                "app_id": "MASAR Social",
                "app_secret": "secret",
                "media_type": "facebook",
                "redirect_uri": "https://example.test/social/meta/oauth/callback",
            }
        )
        from odoo.exceptions import UserError

        with self.assertRaises(UserError):
            wiz.action_save_and_link()

    def test_connect_wizard_strips_and_opens_facebook(self):
        wiz = self.env["social.meta.app.config"].with_user(self.admin).create(
            {
                "app_id": "123-456-789012",
                "app_secret": "secret-value",
                "media_type": "facebook",
                "redirect_uri": "https://example.test/social/meta/oauth/callback",
            }
        )
        action = wiz.action_save_and_link()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn("client_id=123456789012", action["url"])
        self.assertEqual(
            self.env["ir.config_parameter"].sudo().get_str("social.meta_app_id"),
            "123456789012",
        )


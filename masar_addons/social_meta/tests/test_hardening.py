# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.social_meta.models import sdk as sdk_mod


@tagged("post_install", "-at_install")
class TestSocialMetaHardening(TransactionCase):
    # ---- Graph version resolution -------------------------------------------
    def test_graph_version_env_override(self):
        with patch.dict("os.environ", {"SOCIAL_META_GRAPH_VERSION": "v25.0"}):
            self.assertEqual(sdk_mod._default_graph_version(), "v25.0")

    def test_graph_version_env_normalizes_prefix(self):
        with patch.dict("os.environ", {"SOCIAL_META_GRAPH_VERSION": "27.0"}):
            self.assertEqual(sdk_mod._default_graph_version(), "v27.0")

    def test_graph_version_from_sdk_default(self):
        import os

        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("SOCIAL_META_GRAPH_VERSION", None)
            version = sdk_mod._default_graph_version()
        self.assertTrue(version.startswith("v"))

    # ---- rate-limit telemetry never raises ----------------------------------
    def test_log_rate_limit_is_safe(self):
        class R:
            def __init__(self, headers):
                self._h = headers

            def headers(self):
                return self._h

        # High usage → warns, no raise.
        sdk_mod._log_rate_limit(R({"x-app-usage": '{"call_count": 95, "total_time": 10}'}))
        # Malformed → swallowed.
        sdk_mod._log_rate_limit(R({"x-app-usage": "not-json"}))
        # Missing method → swallowed.
        sdk_mod._log_rate_limit(object())

    # ---- token re-validation cron -------------------------------------------
    def test_cron_flags_invalid_token(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("social.meta_app_id", "1234567890")
        ICP.set_param("social.meta_app_secret", "secret")
        account = self.env["social.account"].create(
            {
                "name": "FB Page",
                "platform": "facebook",
                "external_account_id": "PAGE1",
                "meta_page_id": "PAGE1",
                "access_token": "PAGE-TOKEN",
                "connection_status": "connected",
                "publishing_enabled": True,
            }
        )
        Account = type(account)
        with patch.object(Account, "_meta_facebook_api", return_value=object()), patch(
            "odoo.addons.social_meta.models.account.debug_token",
            return_value={"data": {"is_valid": False}},
        ):
            self.env["social.account"]._cron_meta_check_tokens()
        account.invalidate_recordset()
        self.assertEqual(account.connection_status, "error")

    def test_cron_keeps_valid_token(self):
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("social.meta_app_id", "1234567890")
        ICP.set_param("social.meta_app_secret", "secret")
        account = self.env["social.account"].create(
            {
                "name": "FB Page 2",
                "platform": "facebook",
                "external_account_id": "PAGE2",
                "meta_page_id": "PAGE2",
                "access_token": "PAGE-TOKEN",
                "connection_status": "connected",
                "publishing_enabled": True,
            }
        )
        Account = type(account)
        with patch.object(Account, "_meta_facebook_api", return_value=object()), patch(
            "odoo.addons.social_meta.models.account.debug_token",
            return_value={"data": {"is_valid": True}},
        ):
            self.env["social.account"]._cron_meta_check_tokens()
        account.invalidate_recordset()
        self.assertEqual(account.connection_status, "connected")

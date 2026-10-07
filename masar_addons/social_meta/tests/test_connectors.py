# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
"""BrightBean connector helper unit tests (no Graph network)."""
from odoo.tests import TransactionCase, tagged

from odoo.addons.social_meta.models.connectors import (
    FACEBOOK_LOGIN_EXTRA_PARAMS,
    build_send_payload,
    facebook_login_params,
    page_can_publish,
    resolve_recipient_id,
)


@tagged("post_install", "-at_install")
class TestSocialMetaConnectors(TransactionCase):
    def test_facebook_login_params_rerequest(self):
        params = facebook_login_params(
            client_id="123",
            redirect_uri="https://example.test/cb",
            state="sig.body",
            scopes="pages_show_list,pages_messaging",
        )
        self.assertEqual(params["auth_type"], "rerequest")
        self.assertEqual(params["auth_type"], FACEBOOK_LOGIN_EXTRA_PARAMS["auth_type"])
        self.assertEqual(params["scope"], "pages_show_list,pages_messaging")
        self.assertNotIn("config_id", params)

    def test_facebook_login_params_config_id(self):
        params = facebook_login_params(
            client_id="123",
            redirect_uri="https://example.test/cb",
            state="sig.body",
            scopes=["a", "b"],
            config_id="cfg-9",
        )
        self.assertEqual(params["config_id"], "cfg-9")
        self.assertEqual(params["override_default_response_type"], "true")
        self.assertNotIn("scope", params)

    def test_page_can_publish(self):
        self.assertTrue(page_can_publish({"id": "1"}))
        self.assertTrue(page_can_publish({"id": "1", "tasks": ["CREATE_CONTENT", "MODERATE"]}))
        self.assertFalse(page_can_publish({"id": "1", "tasks": ["MODERATE"]}))
        self.assertFalse(page_can_publish({"id": "1", "tasks": []}))

    def test_resolve_recipient_id(self):
        self.assertEqual(resolve_recipient_id({"recipient_id": "PSID1"}), "PSID1")
        self.assertEqual(resolve_recipient_id({"sender": {"id": "PSID2"}}), "PSID2")
        self.assertEqual(resolve_recipient_id({"from": {"id": "PSID3"}}), "PSID3")
        self.assertEqual(resolve_recipient_id({}), "")

    def test_build_send_payload(self):
        payload = build_send_payload("PSID", "hello")
        self.assertEqual(payload["recipient"]["id"], "PSID")
        self.assertEqual(payload["message"]["text"], "hello")
        self.assertEqual(payload["messaging_type"], "RESPONSE")
        tagged = build_send_payload("PSID", "hello", human_agent=True)
        self.assertEqual(tagged["messaging_type"], "MESSAGE_TAG")
        self.assertEqual(tagged["tag"], "HUMAN_AGENT")

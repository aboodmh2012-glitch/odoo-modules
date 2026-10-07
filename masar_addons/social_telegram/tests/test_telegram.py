import os
from unittest.mock import Mock, patch

import requests

from odoo.tests import TransactionCase, tagged
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain


@tagged("post_install", "-at_install")
class TestTelegram(TransactionCase):
    def setUp(self):
        super().setUp()
        self.account = self.env["social.account"].create({"name": "Telegram", "platform": "telegram", "external_account_id": "-100123", "credential_env": "SOCIAL_TEST_TOKEN"})
        self.patch(os, "environ", {"SOCIAL_TEST_TOKEN": "never-log-this-token"})

    def test_text_delivery(self):
        response = Mock(status_code=200)
        response.json.return_value = {"ok": True, "result": {"message_id": 42}}
        with patch("odoo.addons.social_telegram.models.account.requests.post", return_value=response) as send:
            self.assertEqual(self.account._telegram_request("sendMessage", {"text": "Hello"})["id"], "42")
            self.assertEqual(send.call_args.kwargs["timeout"], (10, 45))

    def test_error_classification(self):
        for status, exception in ((429, DeliveryTemporary), (403, DeliveryPermanent), (503, DeliveryUncertain)):
            response = Mock(status_code=status)
            response.json.return_value = {"ok": False}
            with patch("odoo.addons.social_telegram.models.account.requests.post", return_value=response):
                with self.assertRaises(exception):
                    self.account._telegram_request("sendMessage", {})

    def test_network_failure_redacted(self):
        with patch("odoo.addons.social_telegram.models.account.requests.post", side_effect=requests.Timeout("never-log-this-token")):
            with self.assertRaises(DeliveryUncertain) as caught:
                self.account._telegram_request("sendMessage", {})
            self.assertNotIn("never-log-this-token", str(caught.exception))

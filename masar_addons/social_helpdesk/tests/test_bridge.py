from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged, new_test_user


@tagged("post_install", "-at_install")
class TestBridge(TransactionCase):
    def test_conversion_respects_target_permissions(self):
        user = new_test_user(self.env, login="social_helpdesk-operator", groups="social.group_social_user")
        account = self.env["social.account"].create({"name": "Inbox", "external_account_id": "social_helpdesk", "messaging_enabled": True, "user_ids": [Command.link(user.id)]})
        conversation = self.env["social.conversation"].with_user(user)._receive(account.with_user(user), "1", "1", "1", "Customer", "Need assistance")
        with self.assertRaises(AccessError):
            conversation.action_create_ticket()
        self.assertFalse(conversation.sudo().ticket_id)

    def test_conversion_uses_real_record_and_reuses_link(self):
        account = self.env["social.account"].create({"name": "Inbox", "external_account_id": "bridge-success", "messaging_enabled": True, "user_ids": [Command.link(self.env.uid)]})
        # Superuser still opts into operation groups for the workflow guard.
        self.env.user.write({"group_ids": [Command.link(self.env.ref("social.group_social_manager").id)]})
        conversation = self.env["social.conversation"]._receive(account, "1", "1", "1", "Customer", "Need assistance")
        first = conversation.action_create_ticket()
        second = conversation.action_create_ticket()
        self.assertEqual(first["res_model"], "helpdesk.ticket")
        self.assertEqual(first["res_id"], second["res_id"])
        self.assertTrue(conversation.ticket_id.exists())

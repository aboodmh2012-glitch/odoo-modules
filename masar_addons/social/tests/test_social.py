from unittest.mock import patch
from lxml import etree
from uuid import uuid4

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged, new_test_user
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.social.models.attempt import deliver, checkpoint_key
from odoo.addons.social.models.errors import DeliveryTemporary, DeliveryPermanent, DeliveryUncertain


@tagged("post_install", "-at_install")
class TestSocial(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.publisher = new_test_user(cls.env, login="social-publisher", groups="social.group_social_publisher")
        cls.outsider = new_test_user(cls.env, login="social-outsider", groups="social.group_social_user")
        cls.account = cls.env["social.account"].create({"name": "Test channel", "external_account_id": "channel", "user_ids": [Command.link(cls.publisher.id)], "publishing_enabled": True, "messaging_enabled": True})

    def setUp(self):
        super().setUp()
        self.patch(type(self.account), "_validate_target", lambda account, target: None)

    def post(self, accounts=None):
        return self.env["social.post"].with_user(self.publisher).create({"name": "Campaign draft", "content": "Hello", "target_ids": [Command.create({"account_id": account.id}) for account in (accounts or self.account)]})

    def conversation(self):
        return self.env["social.conversation"].with_user(self.publisher)._receive(self.account.with_user(self.publisher), "message1", "thread1", "person1", "Customer", "Please help")

    def test_core_without_connector(self):
        self.assertEqual(self.account.platform, "unconfigured")
        self.assertTrue(self.env["social.post"].with_user(self.publisher).create({"name": "No accounts needed", "content": "Draft"}))

    def test_account_isolation_and_credentials(self):
        self.assertNotIn(self.account, self.env["social.account"].with_user(self.outsider).search([]))
        with self.assertRaises(AccessError):
            self.account.with_user(self.publisher).read(["credential_env"])
        with self.assertRaises(AccessError):
            self.account.with_user(self.publisher).write({"publishing_enabled": False})

    def test_company_isolation(self):
        other = self.env["res.company"].create({"name": "Other Social Company"})
        account = self.env["social.account"].create({"name": "Other", "external_account_id": "other", "company_id": other.id})
        self.assertNotIn(account, self.env["social.account"].with_user(self.publisher).search([]))
        with self.assertRaises(AccessError):
            self.post(account)

    def test_workflow_not_rpc_writable(self):
        post = self.post()
        with self.assertRaises(AccessError):
            post.write({"state": "approved", "approved_digest": post._digest()})
        with self.assertRaises(AccessError):
            post.target_ids.write({"state": "published"})
        with self.assertRaises(AccessError):
            post.with_user(self.outsider).action_approve()

    def test_approval_freezes_content(self):
        post = self.post()
        post.action_approve()
        with self.assertRaises(UserError):
            post.write({"content": "Changed"})
        with self.assertRaises(UserError):
            post.target_ids.write({"platform_content": "Changed"})
        post.action_reset_draft()
        post.write({"content": "Changed"})
        self.assertFalse(post.approved_digest)

    def test_tier_approval_required(self):
        self.env["tier.definition"].create({"name": "Editorial review", "model_id": self.env["ir.model"]._get_id("social.post"), "review_type": "individual", "reviewer_id": self.publisher.id, "definition_domain": "[]", "company_id": self.env.company.id})
        post = self.post()
        with self.assertRaises(UserError):
            post.action_approve()
        post.action_request_review()
        self.assertTrue(post.review_ids)
        post.validate_tier()
        post.action_approve()
        self.assertEqual(post.state, "approved")

    def test_schedule_and_cancel(self):
        post = self.post()
        post.scheduled_at = fields.Datetime.add(fields.Datetime.now(), days=1)
        post.action_approve()
        post.action_publish()
        job = self.env["queue.job"].search([("identity_key", "=", f"social-publish-{post.target_ids.id}-{post.target_ids.queue_generation}")], limit=1)
        self.assertTrue(job)
        self.assertEqual(job.eta, post.scheduled_at)
        post.action_cancel()
        self.assertEqual(post.target_ids.state, "cancelled")
        with patch.object(type(self.account), "_publish_target") as publish:
            post.target_ids._job_publish()
            publish.assert_not_called()

    def test_old_job_cannot_publish_rescheduled_content(self):
        post = self.post()
        post.action_approve()
        post.action_publish()
        old_generation = post.target_ids.queue_generation
        post.action_reset_draft()
        post.write({"scheduled_at": fields.Datetime.add(fields.Datetime.now(), days=2)})
        post.action_approve()
        post.action_publish()
        self.assertNotEqual(old_generation, post.target_ids.queue_generation)
        with patch("odoo.addons.social.models.post.deliver") as send:
            post.target_ids._job_publish(old_generation)
            send.assert_not_called()
        self.assertEqual(post.target_ids.state, "queued")

    def test_targets_fail_independently(self):
        second = self.account.copy({"external_account_id": "second", "name": "Second"})
        post = self.post(self.account | second)
        post.action_approve()
        post.action_publish()
        first, other = post.target_ids
        with patch("odoo.addons.social.models.post.deliver", return_value={"id": "123"}):
            first._job_publish()
            first._job_publish()
        with patch("odoo.addons.social.models.post.deliver", side_effect=DeliveryPermanent):
            other._job_publish()
        self.assertEqual(first.state, "published")
        self.assertEqual(other.state, "failed")
        with self.assertRaises(UserError):
            post.action_reset_draft()

    def test_uncertain_is_not_retried(self):
        post = self.post()
        post.action_approve()
        post.action_publish()
        with patch("odoo.addons.social.models.post.deliver", side_effect=DeliveryUncertain):
            post.target_ids._job_publish()
        self.assertEqual(post.target_ids.state, "uncertain")
        with self.assertRaises(UserError):
            post.target_ids.action_retry()

    def test_inbound_deduplicates(self):
        first, second = self.conversation(), self.conversation()
        self.assertEqual(first, second)
        self.assertEqual(len(first.delivery_ids), 1)
        self.assertTrue(first.needs_reply)
        self.assertFalse(first.partner_id)
        self.assertTrue(first.preview)
        self.assertEqual(first.priority, "0")

    def test_inbox_priority_and_platforms(self):
        conversation = self.conversation()
        conversation.action_assign_me()
        conversation.write({"priority": "2"})
        self.assertEqual(conversation.priority, "2")
        platforms = self.env["social.conversation"]._inbox_platforms()
        self.assertIsInstance(platforms, list)

    def test_assignment_and_internal_note(self):
        conversation = self.conversation()
        conversation.message_post(body="An internal note")
        self.assertEqual(len(conversation.delivery_ids), 1)
        conversation.reply_text = "Hello customer"
        with self.assertRaises(AccessError):
            conversation.action_send_reply()
        conversation.action_assign_me()
        conversation.action_send_reply()
        outgoing = conversation.delivery_ids.filtered(lambda d: d.direction == "outgoing")
        self.assertEqual(outgoing.state, "queued")
        self.assertTrue(outgoing.body_digest)
        with patch("odoo.addons.social.models.conversation.deliver", return_value={"id": "reply-1"}):
            outgoing._job_send()
        self.assertEqual(outgoing.state, "sent")
        self.assertFalse(conversation.needs_reply)

    def test_contact_action_is_idempotent(self):
        profile = self.conversation().profile_id
        with self.assertRaises(AccessError):
            profile.action_create_contact()
        self.publisher.write({"group_ids": [Command.link(self.env.ref("base.group_partner_manager").id)]})
        first = profile.action_create_contact()
        second = profile.action_create_contact()
        self.assertEqual(first["res_id"], second["res_id"])
        self.assertTrue(profile.partner_id)
        with self.assertRaises(AccessError):
            profile.write({"external_profile_id": "someone-else"})

    def test_transport_write_denied(self):
        delivery = self.conversation().delivery_ids
        with self.assertRaises(AccessError):
            delivery.write({"state": "sent"})
        with self.assertRaises(AccessError):
            delivery.unlink()

    def test_checkpoint_replays_success_without_http(self):
        record = self.post().target_ids.with_context(job_uuid=str(uuid4()))
        try:
            with patch.object(type(self.account), "_publish_target", return_value={"id": "remote-1"}) as publish:
                callback = lambda: record.account_id._publish_target(record)
                self.assertEqual(deliver(record, callback)["id"], "remote-1")
                self.assertEqual(deliver(record.with_context(job_uuid=str(uuid4())), callback)["id"], "remote-1")
                self.assertEqual(publish.call_count, 1)
        finally:
            self._remove_checkpoint(record)

    def test_checkpoint_never_retries_unknown(self):
        record = self.post().target_ids.with_context(job_uuid=str(uuid4()))
        try:
            with patch.object(type(self.account), "_publish_target", side_effect=DeliveryUncertain) as publish:
                for unused in range(2):
                    with self.assertRaises(DeliveryUncertain):
                        deliver(record, lambda: record.account_id._publish_target(record))
                self.assertEqual(publish.call_count, 1)
        finally:
            self._remove_checkpoint(record)

    def test_checkpoint_bounded_transient_retries(self):
        record = self.post().target_ids.with_context(job_uuid=str(uuid4()))
        try:
            with patch.object(type(self.account), "_publish_target", side_effect=DeliveryTemporary) as publish:
                for unused in range(4):
                    with self.assertRaises(DeliveryTemporary):
                        deliver(record, lambda: record.account_id._publish_target(record))
                with self.assertRaises(DeliveryPermanent):
                    deliver(record, lambda: record.account_id._publish_target(record))
                self.assertEqual(publish.call_count, 5)
        finally:
            self._remove_checkpoint(record)

    def _remove_checkpoint(self, record):
        with self.registry.cursor() as cr:
            cr.execute("DELETE FROM social_attempt WHERE key=%s", [checkpoint_key(record)])
            cr.commit()

    def test_native_views_and_actions(self):
        for model in ("social.post", "social.account", "social.conversation", "social.profile"):
            view_type = "form"
            view = self.env[model].with_user(self.publisher).get_view(view_type=view_type)
            self.assertEqual(etree.fromstring(view["arch"]).tag, view_type)
        for name in ("dashboard", "posts", "inbox", "monitor", "profiles", "accounts"):
            self.assertTrue(self.env.ref(f"social.action_social_{name}"))


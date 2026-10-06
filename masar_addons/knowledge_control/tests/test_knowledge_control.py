# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestKnowledgeControl(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Page = cls.env["document.page"]
        cls.category = cls.Page.create(
            {
                "name": "KC Test Category",
                "type": "category",
                "content": "<p>cat</p>",
            }
        )
        cls.page = cls.Page.create(
            {
                "name": "AML Policy",
                "type": "content",
                "parent_id": cls.category.id,
                "content": "<p>AML body v1</p>",
                "draft_name": "1.0",
                "draft_summary": "Initial",
                "kc_controlled": True,
                "kc_document_type": "policy",
                "kc_state": "draft",
                "masar_doc_code": "AML-POL-001",
                "masar_status": "draft",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Ack User"})

    def test_ordinary_page_unaffected(self):
        ordinary = self.Page.create(
            {
                "name": "FAQ",
                "type": "content",
                "parent_id": self.category.id,
                "content": "<p>faq</p>",
                "draft_name": "a",
                "draft_summary": "n",
                "kc_controlled": False,
            }
        )
        ordinary.write({"content": "<p>faq2</p>", "draft_name": "b", "draft_summary": "n2"})
        self.assertFalse(ordinary.kc_published_history_id)

    def test_publish_freezes_history_not_new_page(self):
        self.page.action_kc_request_approval()
        self.assertEqual(self.page.kc_state, "approval")
        self.page.action_kc_publish()
        self.assertEqual(self.page.kc_state, "published")
        hist = self.page.kc_published_history_id
        self.assertTrue(hist.kc_frozen)
        self.assertEqual(hist.kc_version_label, "1.0")
        self.assertTrue(hist.kc_content_sha256)
        with self.assertRaises(UserError):
            self.page.write({"content": "<p>tamper</p>"})
        with self.assertRaises(UserError):
            self.page.unlink()

    def test_in_place_revision_and_ack_per_version(self):
        self.page.action_kc_publish()
        hist_v1 = self.page.kc_published_history_id
        Dist = self.env["document.page.distribution"]
        line = Dist.create(
            {
                "page_id": self.page.id,
                "history_id": hist_v1.id,
                "partner_id": self.partner.id,
                "acknowledgment_text": "Ack v1 wording",
            }
        )
        line.action_acknowledge()
        self.assertEqual(line.acknowledgment_text, "Ack v1 wording")

        self.page.action_kc_start_revision()
        self.assertEqual(self.page.kc_state, "draft")
        self.assertEqual(self.page.kc_published_history_id, hist_v1)
        self.page.write(
            {
                "content": "<p>AML body v2</p>",
                "draft_name": "2.0",
                "draft_summary": "Major update",
                "kc_version_type": "major",
            }
        )
        self.page.action_kc_publish()
        hist_v2 = self.page.kc_published_history_id
        self.assertNotEqual(hist_v1, hist_v2)
        self.assertEqual(hist_v2.kc_version_label, "2.0")
        self.assertTrue(hist_v1.kc_frozen)
        self.assertEqual(self.page.kc_ack_count, 0)
        Dist.create(
            {
                "page_id": self.page.id,
                "history_id": hist_v2.id,
                "partner_id": self.partner.id,
            }
        )
        self.assertEqual(self.page.kc_ack_pending_count, 1)

    def test_policy_procedure_link(self):
        procedure = self.Page.create(
            {
                "name": "KYC Procedure",
                "type": "content",
                "parent_id": self.category.id,
                "content": "<p>steps</p>",
                "draft_name": "1.0",
                "draft_summary": "init",
                "kc_controlled": True,
                "kc_document_type": "procedure",
                "kc_policy_ids": [(6, 0, [self.page.id])],
            }
        )
        self.assertIn(self.page, procedure.kc_policy_ids)
        self.assertIn(procedure, self.page.kc_procedure_ids)

    def test_editorial_version_advances_minor_without_collision(self):
        """Regression: an editorial publish must take a NEW number.

        Previously the editorial branch kept the predecessor's major.minor,
        which collided with the frozen previous version under the partial unique
        index and made every editorial publish raise "version already exists".
        """
        self.page.action_kc_publish()
        self.assertEqual(self.page.kc_published_history_id.kc_version_label, "1.0")
        self.page.action_kc_start_revision()
        self.page.write(
            {
                "content": "<p>AML body v1 - typo fix</p>",
                "draft_name": "1.0.1",
                "draft_summary": "Editorial correction",
                "kc_version_type": "editorial",
            }
        )
        # Must not raise, and must advance the minor number.
        self.page.action_kc_publish()
        self.assertEqual(self.page.kc_published_history_id.kc_version_label, "1.1")
        self.assertEqual(self.page.kc_published_history_id.kc_version_type, "editorial")

    def test_reminder_activity_is_not_duplicated(self):
        """Regression: repeated reminders (manual or daily cron) must not stack
        a second open acknowledgment to-do for the same recipient."""
        self.page.action_kc_publish()
        hist = self.page.kc_published_history_id
        user = self.env["res.users"].create(
            {"name": "Recip", "login": "recip_kc_test"}
        )
        Dist = self.env["document.page.distribution"]
        line = Dist.create(
            {
                "page_id": self.page.id,
                "history_id": hist.id,
                "partner_id": user.partner_id.id,
                "user_id": user.id,
            }
        )
        ack_type = self.env.ref("knowledge_control.mail_activity_kc_acknowledge")
        line.action_send_reminder()
        line.action_send_reminder()
        line.action_send_reminder()
        open_acks = line.activity_ids.filtered(
            lambda a: a.activity_type_id == ack_type and a.user_id == user
        )
        self.assertEqual(len(open_acks), 1, "reminders must be idempotent")

    def test_publish_blocked_when_validation_needed_but_unvalidated(self):
        """Regression: a controlled page that needs Tier Validation must not
        publish while validation_status is anything other than "validated"
        (the old gate let the "no review yet" state slip through)."""
        tier_def = self.env.ref("knowledge_control.tier_definition_kc_publish")
        tier_def.active = True
        page = self.Page.create(
            {
                "name": "Gated Policy",
                "type": "content",
                "parent_id": self.category.id,
                "content": "<p>gated</p>",
                "draft_name": "1.0",
                "draft_summary": "init",
                "kc_controlled": True,
                "kc_document_type": "policy",
                "kc_state": "approval",
                "masar_doc_code": "GATE-POL-001",
            }
        )
        self.assertTrue(page.need_validation)
        self.assertNotEqual(page.validation_status, "validated")
        with self.assertRaises(UserError):
            page.action_kc_publish()

    def test_distribute_wizard_snapshots_wording(self):
        self.page.action_kc_publish()
        self.page.kc_ack_confirmation_text = "Custom confirm text"
        wiz = self.env["document.page.distribute.wizard"].create(
            {
                "page_id": self.page.id,
                "history_id": self.page.kc_published_history_id.id,
                "partner_ids": [(6, 0, [self.partner.id])],
                "create_activity": False,
            }
        )
        wiz.action_distribute()
        line = self.env["document.page.distribution"].search(
            [("page_id", "=", self.page.id)], limit=1
        )
        self.assertEqual(line.acknowledgment_text, "Custom confirm text")
        self.assertEqual(line.history_id, self.page.kc_published_history_id)

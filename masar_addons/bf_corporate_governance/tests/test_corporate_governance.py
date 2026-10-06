# -*- coding: utf-8 -*-
# Copyright (c) 2026 Les services de consultation Blue Fox, Inc.
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Corporate governance — sequence, compliance status, signatories, evidence, ACL."""

import html
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


class TestCorporateResolution(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.sudo().write({
            "group_ids": [(4, cls.env.ref(
                "bf_corporate_governance.group_corporate_manager"
            ).id)],
        })

    def _create(self, **kwargs):
        vals = {
            "name": "Test resolution",
            "resolution_type": "board",
            "meeting_date": fields.Date.today(),
        }
        vals.update(kwargs)
        return self.env["corporate.resolution"].create(vals)

    def test_a_resolution_gets_a_reference_from_the_sequence(self):
        resolution = self._create()
        self.assertTrue(resolution.sequence)
        self.assertNotEqual(resolution.sequence, "New")

    def test_two_resolutions_do_not_share_a_reference(self):
        first = self._create()
        second = self._create(name="Second resolution")
        self.assertNotEqual(first.sequence, second.sequence)

    def test_an_explicit_reference_is_kept(self):
        resolution = self._create(sequence="RES-MANUAL-1")
        self.assertEqual(resolution.sequence, "RES-MANUAL-1")

    def test_state_actions(self):
        resolution = self._create()
        self.assertEqual(resolution.status, "draft")
        resolution.action_propose()
        self.assertEqual(resolution.status, "proposed")
        resolution.action_adopt()
        self.assertEqual(resolution.status, "adopted")
        resolution.action_reset_draft()
        self.assertEqual(resolution.status, "draft")
        resolution.action_propose()
        resolution.action_reject()
        self.assertEqual(resolution.status, "rejected")


class TestCorporateCompliance(TransactionCase):

    def _create(self, days, **kwargs):
        vals = {
            "name": "Test deadline",
            "event_type": "annual_declaration",
            "due_date": fields.Date.today() + timedelta(days=days),
        }
        vals.update(kwargs)
        return self.env["corporate.compliance.event"].create(vals)

    def test_status_follows_the_due_date(self):
        self.assertEqual(self._create(-1).status, "overdue")
        self.assertEqual(self._create(0).status, "due_soon")
        self.assertEqual(self._create(30).status, "due_soon")
        self.assertEqual(self._create(31).status, "upcoming")

    def test_completing_an_event_wins_over_the_due_date(self):
        event = self._create(-90)
        self.assertEqual(event.status, "overdue")
        event.action_complete()
        self.assertEqual(event.status, "completed")

    def test_cron_is_idempotent_across_retries(self):
        Event = self.env["corporate.compliance.event"]
        event = self._create(7)
        Event._cron_check_compliance_deadlines()
        event.invalidate_recordset()
        self.assertTrue(event.reminder_sent)
        self.assertEqual(event.reminder_due_date, event.due_date)
        count_after_first = self.env["mail.activity"].search_count([
            ("res_model", "=", "corporate.compliance.event"),
            ("res_id", "=", event.id),
        ])
        Event._cron_check_compliance_deadlines()
        count_after_second = self.env["mail.activity"].search_count([
            ("res_model", "=", "corporate.compliance.event"),
            ("res_id", "=", event.id),
        ])
        self.assertEqual(count_after_first, count_after_second)

    def test_due_date_change_allows_new_reminder_cycle(self):
        event = self._create(7)
        self.env["corporate.compliance.event"]._cron_check_compliance_deadlines()
        event.invalidate_recordset()
        self.assertTrue(event.reminder_sent)
        new_due = fields.Date.today() + timedelta(days=14)
        event.write({"due_date": new_due})
        self.assertFalse(event.reminder_sent)
        self.assertFalse(event.reminder_due_date)


class TestDirectorOfficerActive(TransactionCase):

    def _partner(self, name):
        return self.env["res.partner"].create({"name": name})

    def test_director_active_until_end_date(self):
        director = self.env["corporate.director"].create({
            "partner_id": self._partner("Director One").id,
            "appointment_date": fields.Date.today() - timedelta(days=30),
        })
        self.assertTrue(director.is_active)
        director = self.env["corporate.director"].create({
            "partner_id": self._partner("Director Two").id,
            "appointment_date": fields.Date.today() - timedelta(days=60),
            "end_date": fields.Date.today(),
        })
        self.assertFalse(director.is_active)

    def test_officer_active_until_end_date(self):
        officer = self.env["corporate.officer"].create({
            "partner_id": self._partner("Officer One").id,
            "title": "secretary",
            "appointment_date": fields.Date.today() - timedelta(days=30),
        })
        self.assertTrue(officer.is_active)
        officer = self.env["corporate.officer"].create({
            "partner_id": self._partner("Officer Two").id,
            "title": "treasurer",
            "appointment_date": fields.Date.today() - timedelta(days=60),
            "end_date": fields.Date.today(),
        })
        self.assertFalse(officer.is_active)


@tagged("post_install", "-at_install")
class TestSignatoriesAndPdf(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.shareholder = cls.env["res.partner"].create({"name": "Sole Shareholder"})
        cls.officer = cls.env["res.partner"].create({"name": "Countersigning Officer"})
        cls.outgoing = cls.env["res.partner"].create({"name": "Outgoing Director"})
        cls.incoming = cls.env["res.partner"].create({"name": "Incoming Director"})

    def _resolution(self, **kwargs):
        vals = {
            "name": "Test resolution",
            "resolution_type": "board",
            "meeting_date": fields.Date.today(),
            "company_id": self.company.id,
        }
        vals.update(kwargs)
        return self.env["corporate.resolution"].create(vals)

    def _render(self, resolution):
        return html.unescape(str(self.env["ir.qweb"]._render(
            "bf_corporate_governance.report_corporate_resolution",
            {"docs": resolution, "env": self.env},
        )))

    def _director(self, partner, appointed, end=False):
        return self.env["corporate.director"].create({
            "partner_id": partner.id,
            "appointment_date": appointed,
            "end_date": end,
            "company_id": self.company.id,
        })

    def test_signatories_win_over_the_director_registry(self):
        self._director(self.incoming, fields.Date.today() - timedelta(days=30))
        resolution = self._resolution(resolution_type="written_shareholder")
        self.env["corporate.resolution.signatory"].create([
            {
                "resolution_id": resolution.id,
                "sequence": 10,
                "partner_id": self.shareholder.id,
                "capacity": "sole_shareholder",
            },
            {
                "resolution_id": resolution.id,
                "sequence": 20,
                "partner_id": self.officer.id,
                "capacity": "other",
                "capacity_custom": "Vice President, Secretary and Treasurer",
                "purpose": "for the sole purpose of acknowledging the conflict disclosure",
            },
        ])
        signatories = resolution._get_signatories()
        self.assertEqual(
            [s["name"] for s in signatories],
            ["Sole Shareholder", "Countersigning Officer"],
        )
        self.assertEqual(signatories[0]["capacity"], "Sole shareholder")
        self.assertEqual(
            signatories[1]["capacity"],
            "Vice President, Secretary and Treasurer",
        )
        self.assertNotIn("Director", [s["capacity"] for s in signatories])

    def test_other_capacity_demands_its_text(self):
        resolution = self._resolution(resolution_type="written_shareholder")
        with self.assertRaises(ValidationError):
            self.env["corporate.resolution.signatory"].create({
                "resolution_id": resolution.id,
                "partner_id": self.shareholder.id,
                "capacity": "other",
            })

    def test_duplicating_a_resolution_keeps_its_signature_block(self):
        resolution = self._resolution(resolution_type="written_shareholder")
        self.env["corporate.resolution.signatory"].create([
            {
                "resolution_id": resolution.id,
                "partner_id": self.shareholder.id,
                "capacity": "sole_shareholder",
            },
            {
                "resolution_id": resolution.id,
                "partner_id": self.officer.id,
                "capacity": "officer",
            },
        ])
        copy = resolution.copy()
        self.assertEqual(
            [s.partner_id.name for s in copy.signatory_ids],
            ["Sole Shareholder", "Countersigning Officer"],
        )

    def test_board_fallback_uses_directors_at_meeting_date(self):
        meeting = fields.Date.today() - timedelta(days=10)
        self._director(
            self.outgoing,
            fields.Date.today() - timedelta(days=100),
            end=meeting,
        )
        self._director(self.incoming, meeting - timedelta(days=1))
        resolution = self._resolution(meeting_date=meeting)
        signatories = resolution._get_signatories()
        self.assertEqual([s["name"] for s in signatories], ["Incoming Director"])
        self.assertEqual(signatories[0]["capacity"], "Director")

    def test_pdf_prints_custom_capacity(self):
        resolution = self._resolution(resolution_type="written_shareholder")
        self.env["corporate.resolution.signatory"].create([
            {
                "resolution_id": resolution.id,
                "partner_id": self.shareholder.id,
                "capacity": "sole_shareholder",
            },
            {
                "resolution_id": resolution.id,
                "partner_id": self.officer.id,
                "capacity": "other",
                "capacity_custom": "Vice President, Secretary and Treasurer",
                "purpose": "for the sole purpose of acknowledging the conflict disclosure",
            },
        ])
        rendered = self._render(resolution)
        self.assertIn(
            '<div class="res-sig-role">Vice President, Secretary and Treasurer</div>',
            rendered,
        )
        self.assertIn(
            '<div class="res-sig-purpose">for the sole purpose of acknowledging the '
            "conflict disclosure</div>",
            rendered,
        )


@tagged("post_install", "-at_install")
class TestMinuteBookEvidence(TransactionCase):
    """Pages = navigation; frozen history = evidence."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.sudo().write({
            "group_ids": [(4, cls.env.ref(
                "bf_corporate_governance.group_corporate_manager"
            ).id)],
        })

    def test_reject_non_frozen_history_as_evidence(self):
        category = self.env["document.page"].create({
            "name": "MB Cat",
            "type": "category",
            "content": "<p>c</p>",
        })
        page = self.env["document.page"].create({
            "name": "Policy",
            "type": "content",
            "parent_id": category.id,
            "content": "<p>body</p>",
            "draft_name": "1.0",
            "draft_summary": "init",
            "minute_book_section": "policies",
            "kc_controlled": True,
            "kc_document_type": "policy",
            "kc_state": "draft",
            "masar_doc_code": "GOV-POL-001",
            "masar_status": "draft",
        })
        hist = self.env["document.page.history"].search(
            [("page_id", "=", page.id)], limit=1
        )
        self.assertTrue(hist)
        self.assertFalse(hist.kc_frozen)
        resolution = self.env["corporate.resolution"].create({
            "name": "Adopt policy",
            "resolution_type": "board",
            "meeting_date": fields.Date.today(),
            "document_ids": [(6, 0, page.ids)],
        })
        with self.assertRaises(ValidationError):
            resolution.write({"approved_history_ids": [(6, 0, hist.ids)]})

    def test_adopt_requires_frozen_evidence_for_controlled_pages(self):
        category = self.env["document.page"].create({
            "name": "MB Cat2",
            "type": "category",
            "content": "<p>c</p>",
        })
        page = self.env["document.page"].create({
            "name": "Board Policy",
            "type": "content",
            "parent_id": category.id,
            "content": "<p>policy</p>",
            "draft_name": "1.0",
            "draft_summary": "init",
            "minute_book_section": "policies",
            "kc_controlled": True,
            "kc_document_type": "policy",
            "kc_state": "draft",
            "masar_doc_code": "GOV-POL-002",
            "masar_status": "draft",
        })
        resolution = self.env["corporate.resolution"].create({
            "name": "Adopt without evidence",
            "resolution_type": "board",
            "meeting_date": fields.Date.today(),
            "document_ids": [(6, 0, page.ids)],
            "status": "proposed",
        })
        with self.assertRaises(ValidationError):
            resolution.action_adopt()

    def test_adopt_with_published_frozen_history(self):
        category = self.env["document.page"].create({
            "name": "MB Cat3",
            "type": "category",
            "content": "<p>c</p>",
        })
        page = self.env["document.page"].create({
            "name": "Published Policy",
            "type": "content",
            "parent_id": category.id,
            "content": "<p>policy v1</p>",
            "draft_name": "1.0",
            "draft_summary": "init",
            "minute_book_section": "policies",
            "kc_controlled": True,
            "kc_document_type": "policy",
            "kc_state": "draft",
            "masar_doc_code": "GOV-POL-003",
            "masar_status": "draft",
        })
        page.action_kc_publish()
        hist = page.kc_published_history_id
        self.assertTrue(hist.kc_frozen)
        resolution = self.env["corporate.resolution"].create({
            "name": "Adopt with evidence",
            "resolution_type": "board",
            "meeting_date": fields.Date.today(),
            "document_ids": [(6, 0, page.ids)],
            "approved_history_ids": [(6, 0, hist.ids)],
            "status": "proposed",
        })
        resolution.action_adopt()
        self.assertEqual(resolution.status, "adopted")
        self.assertIn(hist, resolution.approved_history_ids)


@tagged("post_install", "-at_install")
class TestCorporateSecurity(TransactionCase):
    """Multi-company + group ACL smoke tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Governance Co B"})
        cls.partner_a = cls.env["res.partner"].create({"name": "Director A"})
        cls.partner_b = cls.env["res.partner"].create({"name": "Director B"})
        cls.res_a = cls.env["corporate.resolution"].create({
            "name": "Res A",
            "resolution_type": "board",
            "meeting_date": fields.Date.today(),
            "company_id": cls.company_a.id,
        })
        cls.res_b = cls.env["corporate.resolution"].create({
            "name": "Res B",
            "resolution_type": "board",
            "meeting_date": fields.Date.today(),
            "company_id": cls.company_b.id,
        })
        cls.dir_a = cls.env["corporate.director"].create({
            "partner_id": cls.partner_a.id,
            "appointment_date": fields.Date.today(),
            "company_id": cls.company_a.id,
        })
        cls.dir_b = cls.env["corporate.director"].create({
            "partner_id": cls.partner_b.id,
            "appointment_date": fields.Date.today(),
            "company_id": cls.company_b.id,
        })

        Users = cls.env["res.users"].with_context(no_reset_password=True)
        group_user = cls.env.ref("bf_corporate_governance.group_corporate_user")
        group_manager = cls.env.ref("bf_corporate_governance.group_corporate_manager")
        cls.user_a = Users.create({
            "name": "Gov User A",
            "login": "gov_user_a",
            "company_id": cls.company_a.id,
            "company_ids": [(6, 0, [cls.company_a.id])],
            "group_ids": [(6, 0, [group_user.id])],
        })
        cls.manager_a = Users.create({
            "name": "Gov Manager A",
            "login": "gov_manager_a",
            "company_id": cls.company_a.id,
            "company_ids": [(6, 0, [cls.company_a.id])],
            "group_ids": [(6, 0, [group_manager.id])],
        })
        cls.plain = Users.create({
            "name": "Plain Internal",
            "login": "gov_plain",
            "company_id": cls.company_a.id,
            "company_ids": [(6, 0, [cls.company_a.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
        })

    def test_company_a_user_cannot_read_company_b_resolution(self):
        Resolution = self.env["corporate.resolution"].with_user(self.user_a)
        self.assertTrue(Resolution.browse(self.res_a.id).exists())
        self.assertFalse(Resolution.search([("id", "=", self.res_b.id)]))

    def test_company_a_user_cannot_read_company_b_director(self):
        Director = self.env["corporate.director"].with_user(self.user_a)
        self.assertTrue(Director.browse(self.dir_a.id).exists())
        self.assertFalse(Director.search([("id", "=", self.dir_b.id)]))

    def test_plain_user_has_no_resolution_access(self):
        with self.assertRaises(AccessError):
            self.env["corporate.resolution"].with_user(self.plain).search([])

    def test_user_cannot_create_resolution(self):
        with self.assertRaises(AccessError):
            self.env["corporate.resolution"].with_user(self.user_a).create({
                "name": "Forbidden",
                "resolution_type": "board",
                "meeting_date": fields.Date.today(),
                "company_id": self.company_a.id,
            })

    def test_manager_can_create_resolution(self):
        rec = self.env["corporate.resolution"].with_user(self.manager_a).create({
            "name": "Allowed",
            "resolution_type": "board",
            "meeting_date": fields.Date.today(),
            "company_id": self.company_a.id,
        })
        self.assertTrue(rec.id)

    def test_user_cannot_adopt_resolution(self):
        self.res_a.action_propose()
        with self.assertRaises((ValidationError, AccessError)):
            self.res_a.with_user(self.user_a).action_adopt()

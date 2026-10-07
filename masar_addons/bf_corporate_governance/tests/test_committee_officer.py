# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCommitteeAndOfficerLink(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Director One"})
        cls.chair = cls.env["res.partner"].create({"name": "Committee Chair"})
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Ops CEO",
                "company_id": cls.company.id,
            }
        )

    def test_officer_employee_link(self):
        officer = self.env["corporate.officer"].create(
            {
                "partner_id": self.partner.id,
                "title": "director_general",
                "appointment_date": fields.Date.today(),
                "employee_id": self.employee.id,
                "company_id": self.company.id,
            }
        )
        self.assertTrue(officer.is_active)
        self.assertEqual(officer.employee_id, self.employee)

    def test_committee_membership_and_derived_chair(self):
        committee = self.env["corporate.committee"].create(
            {
                "name": "Audit Committee",
                "committee_type": "audit",
                "company_id": self.company.id,
                "effective_date": fields.Date.today(),
            }
        )
        self.env["corporate.committee.member"].create(
            {
                "committee_id": committee.id,
                "partner_id": self.chair.id,
                "role": "chair",
                "appointment_date": fields.Date.today(),
            }
        )
        self.env["corporate.committee.member"].create(
            {
                "committee_id": committee.id,
                "partner_id": self.partner.id,
                "role": "member",
                "appointment_date": fields.Date.today(),
            }
        )
        committee.invalidate_recordset()
        self.assertTrue(committee.is_active)
        self.assertEqual(committee.chairperson_id, self.chair)
        self.assertEqual(len(committee.member_ids.filtered("is_active")), 2)

    def test_committee_multi_company_isolation(self):
        other = self.env["res.company"].create({"name": "Other Gov Co"})
        foreign = self.env["corporate.committee"].with_company(other).create(
            {
                "name": "Foreign Audit",
                "committee_type": "audit",
                "company_id": other.id,
            }
        )
        # Without other company in allowed companies, foreign should not appear
        # for the current company context.
        self.assertFalse(
            self.env["corporate.committee"].search(
                [("company_id", "=", self.company.id), ("id", "=", foreign.id)]
            )
        )
        self.assertTrue(foreign.exists())
        self.assertTrue(foreign.with_company(other).name)

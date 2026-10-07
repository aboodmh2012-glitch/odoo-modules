# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged("post_install", "-at_install", "masar_hr_yemen")
class TestMasarHrYemenDiscipline(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write(
            {
                "masar_hr_max_deduction_pct": 20.0,
                "masar_hr_discover_days": 15,
                "masar_hr_investigate_days": 30,
                "masar_hr_appeal_days_default": 30,
                "masar_hr_maternity_days": 70,
                "masar_hr_suspension_oral_days": 5,
                "masar_hr_suspension_written_days": 30,
            }
        )
        cls.power_user = new_test_user(
            cls.env,
            login="ye_hr_power",
            groups=(
                "masar_hr_disciplinary.group_disciplinary_hr_officer,"
                "masar_hr_disciplinary.group_disciplinary_investigator,"
                "masar_hr_disciplinary.group_disciplinary_approver,"
                "masar_hr_disciplinary.group_disciplinary_hr_manager"
            ),
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "YE Test Employee",
                "company_id": cls.company.id,
            }
        )
        version = getattr(cls.employee, "version_id", False) or getattr(
            cls.employee, "current_version_id", False
        )
        if version:
            version.sudo().write({"wage": 100000.0})

        cls.sanction_ded = cls.env["hr.discipline.sanction.type"].create(
            {
                "name": "Test Deduction",
                "code": "T_DED",
                "sanction_kind": "deduction",
                "requires_investigation": True,
                "has_financial_impact": True,
                "requires_approval_level": "approver",
                "company_id": cls.company.id,
            }
        )
        cls.sanction_notice = cls.env["hr.discipline.sanction.type"].create(
            {
                "name": "Test Notice",
                "code": "T_NOTICE",
                "sanction_kind": "notice",
                "requires_investigation": False,
                "has_financial_impact": False,
                "requires_approval_level": "officer",
                "company_id": cls.company.id,
            }
        )
        cls.offense = cls.env["hr.discipline.offense.type"].create(
            {
                "name": "Test Offense",
                "code": "T_OFF",
                "requires_investigation": True,
                "allows_appeal": True,
                "appeal_deadline_days": 30,
                "approval_level": "approver",
                "sanction_type_ids": [
                    (6, 0, [cls.sanction_ded.id, cls.sanction_notice.id])
                ],
                "company_id": cls.company.id,
            }
        )

    def _make_case(self, **extra):
        vals = {
            "employee_id": self.employee.id,
            "offense_type_id": self.offense.id,
            "incident_date": fields.Date.today(),
            "discovery_date": fields.Date.today(),
            "incident_summary": "Test incident",
            "company_id": self.company.id,
        }
        vals.update(extra)
        return (
            self.env["hr.disciplinary.case"]
            .with_user(self.power_user)
            .create(vals)
        )

    def test_maternity_default_amended_70(self):
        self.assertEqual(self.company.masar_hr_maternity_days, 70)

    def test_deduction_over_cap_blocked(self):
        case = self._make_case()
        case.action_submit()
        case.action_start_investigation()
        case.write(
            {
                "investigation_notes": "<p>done</p>",
                "employee_statement": "I apologize",
                "recommendation": "Deduct",
                "recommended_sanction_id": self.sanction_ded.id,
                "financial_amount": 50000.0,
                "hr_review_notes": "ok",
            }
        )
        case.action_submit_recommendation()
        case.action_hr_review_done()
        with self.assertRaises(UserError):
            case.action_approve_decision()

    def test_deduction_without_investigation_blocked(self):
        case = self._make_case()
        case.action_submit()
        case._workflow_write({"state": "recommendation"})
        case.write(
            {
                "recommendation": "Deduct",
                "recommended_sanction_id": self.sanction_ded.id,
                "financial_amount": 1000.0,
            }
        )
        with self.assertRaises(UserError):
            case.action_submit_recommendation()

    def test_notice_skips_investigation_even_if_offense_flag(self):
        """Art. 96 gates on sanction ladder, not offense.requires_investigation."""
        case = self._make_case()
        self.assertTrue(case.offense_type_id.requires_investigation)
        self.assertFalse(
            case._sanction_needs_investigation(self.sanction_notice)
        )

    def test_discover_window_blocks_late_investigation(self):
        case = self._make_case(
            discovery_date=fields.Date.today() - timedelta(days=20),
        )
        case.action_submit()
        with self.assertRaises(UserError):
            case.action_start_investigation()

    def test_completion_window_blocks_late_sanction(self):
        case = self._make_case()
        case.action_submit()
        case.action_start_investigation()
        case.write(
            {
                "investigation_notes": "<p>done</p>",
                "employee_statement": "ok",
                "recommendation": "Deduct",
                "recommended_sanction_id": self.sanction_ded.id,
                "financial_amount": 1000.0,
                "hr_review_notes": "ok",
            }
        )
        case.action_submit_recommendation()
        case.action_hr_review_done()
        # Backdate investigation start beyond Art. 97(1)(b) window
        case.write(
            {
                "investigation_started_on": fields.Date.today()
                - timedelta(days=40),
            }
        )
        with self.assertRaises(UserError):
            case.action_approve_decision()

    def test_suspension_written_not_over_30_days(self):
        case = self._make_case()
        case.write(
            {
                "suspension_notice_kind": "written",
                "suspension_start": fields.Date.today(),
                "suspension_end": fields.Date.today() + timedelta(days=40),
                "suspension_reason": "Investigate",
            }
        )
        with self.assertRaises(UserError):
            case.action_set_precautionary_suspension()

    def test_suspension_oral_not_over_5_days(self):
        case = self._make_case()
        case.write(
            {
                "suspension_notice_kind": "oral",
                "suspension_start": fields.Date.today(),
                "suspension_end": fields.Date.today() + timedelta(days=6),
                "suspension_reason": "Verbal hold",
            }
        )
        with self.assertRaises(UserError):
            case.action_set_precautionary_suspension()

    def test_yemen_sanction_seed(self):
        notice = self.env["hr.discipline.sanction.type"].search(
            [("code", "=", "YE_NOTICE")], limit=1
        )
        self.assertTrue(notice)
        self.assertEqual(notice.sanction_kind, "notice")

    def test_legacy_appeal_7_uses_company_default(self):
        """Base offense default 7 must not override company Art. 97(2) 30 days."""
        self.offense.appeal_deadline_days = 7
        self.company.masar_hr_appeal_days_default = 30
        case = self._make_case()
        case.action_submit()
        case.action_start_investigation()
        case.write(
            {
                "investigation_notes": "<p>done</p>",
                "employee_statement": "ok",
                "recommendation": "Deduct",
                "recommended_sanction_id": self.sanction_ded.id,
                "financial_amount": 1000.0,
                "hr_review_notes": "ok",
            }
        )
        case.action_submit_recommendation()
        case.action_hr_review_done()
        case.action_approve_decision()
        if case.state == "awaiting_appeal":
            expected = fields.Date.today() + timedelta(days=30)
            self.assertEqual(case.appeal_deadline, expected)

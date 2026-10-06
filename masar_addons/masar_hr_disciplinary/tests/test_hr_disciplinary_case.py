# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user

@tagged("post_install", "-at_install")
class TestHrDisciplinaryCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.approver = new_test_user(
            cls.env,
            login="disc_approver",
            groups="masar_hr_disciplinary.group_disciplinary_approver",
        )
        cls.officer = new_test_user(
            cls.env,
            login="disc_officer",
            groups="masar_hr_disciplinary.group_disciplinary_hr_officer",
        )
        cls.investigator = new_test_user(
            cls.env,
            login="disc_investigator",
            groups="masar_hr_disciplinary.group_disciplinary_investigator",
        )
        # A second pure investigator — must NOT see cases assigned to another.
        cls.investigator2 = new_test_user(
            cls.env,
            login="disc_investigator2",
            groups="masar_hr_disciplinary.group_disciplinary_investigator",
        )
        cls.emp_user = new_test_user(
            cls.env,
            login="disc_employee",
            groups="base.group_user",
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Disc Employee",
                "user_id": cls.emp_user.id,
                "company_id": cls.company.id,
            }
        )
        cls.sanction = cls.env["hr.discipline.sanction.type"].create(
            {
                "name": "Written Warning",
                "code": "WARN",
                "has_financial_impact": False,
                "requires_approval_level": "manager",
            }
        )
        cls.sanction_fine = cls.env["hr.discipline.sanction.type"].create(
            {
                "name": "Salary Deduction",
                "code": "FINE",
                "has_financial_impact": True,
                "requires_approval_level": "approver",
            }
        )
        cls.offense = cls.env["hr.discipline.offense.type"].create(
            {
                "name": "Late Attendance",
                "code": "LATE",
                "severity": "2",
                "approval_level": "approver",
                "requires_investigation": True,
                "allows_appeal": True,
                "appeal_deadline_days": 7,
                "has_financial_impact": False,
                "sanction_type_ids": [(6, 0, [cls.sanction.id, cls.sanction_fine.id])],
            }
        )
        cls.offense_no_appeal = cls.env["hr.discipline.offense.type"].create(
            {
                "name": "Critical Safety",
                "code": "SAFE",
                "severity": "4",
                "approval_level": "approver",
                "allows_appeal": False,
                "has_financial_impact": True,
                "sanction_type_ids": [(6, 0, [cls.sanction_fine.id])],
            }
        )

    def _create_case(self, offense=None, **extra):
        vals = {
            "employee_id": self.employee.id,
            "offense_type_id": (offense or self.offense).id,
            "incident_summary": "Arrived late without notice",
        }
        vals.update(extra)
        return (
            self.env["hr.disciplinary.case"]
            .with_user(self.officer)
            .create(vals)
        )

    def _advance_to_pending_approval(self, case, sanction=None):
        case.action_submit()
        case.with_user(self.investigator).action_start_investigation()
        case.with_user(self.investigator).action_request_statement()
        case.with_user(self.emp_user).write(
            {"employee_statement": "I apologize for being late."}
        )
        case.with_user(self.emp_user).action_submit_statement()
        case.with_user(self.investigator).write(
            {
                "recommendation": "Issue written warning",
                "recommended_sanction_id": (sanction or self.sanction).id,
            }
        )
        case.with_user(self.investigator).action_submit_recommendation()
        case.with_user(self.officer).action_hr_review_done()
        return case

    def test_happy_path_to_awaiting_appeal(self):
        case = self._create_case()
        self.assertTrue(case.name.startswith("DIS/"))
        self._advance_to_pending_approval(case)
        case.with_user(self.approver).action_approve_decision()
        self.assertEqual(case.state, "awaiting_appeal")
        self.assertEqual(case.decided_sanction_id, self.sanction)
        self.assertFalse(case.payroll_ready)
        self.assertTrue(case.appeal_deadline)

    def test_immutable_after_decision(self):
        case = self._create_case()
        self._advance_to_pending_approval(case)
        case.with_user(self.approver).action_approve_decision()
        with self.assertRaises(UserError):
            case.with_user(self.officer).write({"incident_summary": "tampered"})

    def test_cannot_forge_state_via_write(self):
        case = self._create_case()
        with self.assertRaises(UserError):
            case.with_user(self.emp_user).write({"state": "decided"})
        with self.assertRaises(UserError):
            case.with_user(self.officer).write({"state": "closed"})
        with self.assertRaises(UserError):
            case.with_user(self.officer).write({"payroll_ready": True})

    def test_employee_cannot_write_decision_fields(self):
        case = self._create_case()
        with self.assertRaises(AccessError):
            case.with_user(self.emp_user).write(
                {"recommendation": "forged", "financial_amount": 999}
            )

    def test_financial_deferred_until_close_when_appeal(self):
        case = self._create_case()
        self._advance_to_pending_approval(case, sanction=self.sanction_fine)
        case.write({"financial_amount": 100.0})
        case.with_user(self.approver).action_approve_decision()
        self.assertEqual(case.state, "awaiting_appeal")
        self.assertFalse(case.payroll_ready)
        # Cannot close before appeal deadline
        with self.assertRaises(UserError):
            case.with_user(self.officer).action_close()
        case._workflow_write({"appeal_deadline": fields.Date.today() - timedelta(days=1)})
        case.with_user(self.officer).action_close()
        self.assertEqual(case.state, "closed")
        self.assertTrue(case.payroll_ready)

    def test_investigator_accesses_assigned_or_open_case(self):
        case = self._create_case()
        case.action_submit()
        # A submitted, unassigned case is visible to any investigator to pick up.
        case.with_user(self.investigator).action_start_investigation()
        case.with_user(self.investigator).write(
            {"investigation_notes": "<p>Interviewed witnesses</p>"}
        )
        self.assertEqual(case.state, "investigation")

    def test_investigator_cannot_see_case_assigned_to_another(self):
        """Privacy: once assigned, other pure investigators lose visibility."""
        case = self._create_case()
        case.action_submit()
        case.with_user(self.investigator).action_start_investigation()
        # investigator2 is a pure investigator (no HR officer/manager rights).
        visible = (
            self.env["hr.disciplinary.case"]
            .with_user(self.investigator2)
            .search([("id", "=", case.id)])
        )
        self.assertFalse(visible, "Case assigned to another investigator leaked.")

    def test_financial_immediate_when_no_appeal(self):
        case = self._create_case(offense=self.offense_no_appeal)
        self._advance_to_pending_approval(case, sanction=self.sanction_fine)
        case.write({"financial_amount": 50.0})
        case.with_user(self.approver).action_approve_decision()
        self.assertEqual(case.state, "decided")
        self.assertTrue(case.payroll_ready)

    def test_employee_cannot_approve(self):
        case = self._create_case()
        self._advance_to_pending_approval(case)
        with self.assertRaises(AccessError):
            case.with_user(self.emp_user).action_approve_decision()

    def test_statement_required(self):
        case = self._create_case()
        case.action_submit()
        case.with_user(self.investigator).action_request_statement()
        with self.assertRaises(UserError):
            case.with_user(self.emp_user).action_submit_statement()

    def test_appeal_rejected_sets_payroll(self):
        case = self._create_case()
        self._advance_to_pending_approval(case, sanction=self.sanction_fine)
        case.write({"financial_amount": 80.0})
        case.with_user(self.approver).action_approve_decision()
        case.with_user(self.emp_user).write({"appeal_text": "Please reconsider"})
        case.with_user(self.emp_user).action_submit_appeal()
        case.with_user(self.approver).write(
            {
                "appeal_decision_notes": "Appeal rejected; deduction stands.",
                "appeal_outcome": "rejected",
            }
        )
        case.with_user(self.approver).action_resolve_appeal()
        self.assertEqual(case.state, "closed")
        self.assertTrue(case.payroll_ready)

    def test_appeal_upheld_reopens(self):
        case = self._create_case()
        self._advance_to_pending_approval(case)
        case.with_user(self.approver).action_approve_decision()
        case.with_user(self.emp_user).write({"appeal_text": "Wrong person"})
        case.with_user(self.emp_user).action_submit_appeal()
        case.with_user(self.approver).write(
            {
                "appeal_decision_notes": "Overturned",
                "appeal_outcome": "upheld",
            }
        )
        case.with_user(self.approver).action_resolve_appeal()
        self.assertEqual(case.state, "pending_approval")
        self.assertFalse(case.decided_sanction_id)
        self.assertFalse(case.payroll_ready)

    def test_context_force_write_ignored(self):
        case = self._create_case()
        with self.assertRaises(UserError):
            case.with_user(self.officer).with_context(
                disciplinary_force_write=True
            ).write({"state": "closed"})

    def test_unlink_only_draft(self):
        case = self._create_case()
        case.action_submit()
        with self.assertRaises(UserError):
            case.unlink()

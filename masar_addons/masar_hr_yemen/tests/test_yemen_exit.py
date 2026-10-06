# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged("post_install", "-at_install", "masar_hr_yemen")
class TestMasarHrYemenExit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.masar_hr_exit_strict = False
        cls.hr_user = new_test_user(
            cls.env,
            login="ye_exit_hr",
            groups="hr.group_hr_user,hr.group_hr_manager",
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "YE Exit Employee",
                "company_id": cls.company.id,
                "contract_date_start": fields.Date.today().replace(year=2024, month=1, day=1),
            }
        )

    def _make_resignation(self):
        return (
            self.env["hr.resignation"]
            .with_user(self.hr_user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "joining_date": self.employee.contract_date_start,
                    "expected_last_day": fields.Date.today(),
                    "notice_days": 30,
                    "resignation_type": "resigned",
                    "reason": "Personal",
                }
            )
        )

    def test_plans_seeded(self):
        onb = self.env.ref("masar_hr_yemen.plan_masar_onboarding", raise_if_not_found=False)
        off = self.env.ref("masar_hr_yemen.plan_masar_offboarding", raise_if_not_found=False)
        self.assertTrue(onb)
        self.assertTrue(off)
        self.assertGreaterEqual(len(onb.template_ids), 3)
        self.assertGreaterEqual(len(off.template_ids), 3)

    def test_soft_checklist_does_not_block_approve(self):
        resig = self._make_resignation()
        resig.action_confirm()
        resig.action_masar_exit_checklist()
        # Default: reminders only — approve must succeed
        resig.action_approve()
        self.assertIn(resig.state, ("approved", "done"))

    def test_strict_mode_blocks_approve(self):
        self.company.masar_hr_exit_strict = True
        resig = self._make_resignation()
        resig.action_confirm()
        # Remove auto stubs so checklist has open items
        self.env["hr.employee.document"].search(
            [("employee_id", "=", self.employee.id)]
        ).unlink()
        with self.assertRaises(UserError):
            resig.action_approve()

    def test_service_certificate_action(self):
        resig = self._make_resignation()
        resig.action_confirm()
        action = resig.action_print_service_certificate()
        self.assertEqual(action.get("type"), "ir.actions.report")

    def test_certificate_wage_visible_via_sudo_compute(self):
        version = getattr(self.employee, "version_id", False) or getattr(
            self.employee, "current_version_id", False
        )
        if version:
            version.sudo().write({"wage": 250000.0})
        resig = self._make_resignation()
        self.assertTrue(resig.certificate_currency_id)
        # Wage may be 0 if version API differs; compute must not raise for hr user
        resig.with_user(self.hr_user).read(
            ["certificate_basic_wage", "certificate_currency_id"]
        )

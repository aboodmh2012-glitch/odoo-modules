# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged("post_install", "-at_install")
class TestHrEmployeeTransfer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env, login="tr_mgr", groups="hr.group_hr_manager,base.group_user"
        )
        cls.officer = new_test_user(
            cls.env, login="tr_off", groups="hr.group_hr_user,base.group_user"
        )
        cls.company2 = cls.env["res.company"].create({"name": "Branch B"})
        cls.dept1 = cls.env["hr.department"].create({"name": "Dept A"})
        cls.dept2 = cls.env["hr.department"].create(
            {"name": "Dept B", "company_id": cls.company2.id}
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Transfer Emp",
                "department_id": cls.dept1.id,
                "company_id": cls.env.company.id,
            }
        )

    def test_apply_keeps_same_employee(self):
        tr = (
            self.env["hr.employee.transfer"]
            .with_user(self.manager)
            .create(
                {
                    "employee_id": self.employee.id,
                    "dest_company_id": self.company2.id,
                    "dest_department_id": self.dept2.id,
                }
            )
        )
        emp_id = self.employee.id
        tr.with_user(self.manager).action_confirm()
        self.assertEqual(tr.source_company_id, self.env.company)
        tr.with_user(self.manager).action_apply()
        self.assertEqual(tr.state, "done")
        self.assertEqual(self.employee.id, emp_id)
        self.assertEqual(self.employee.company_id, self.company2)
        self.assertEqual(self.employee.department_id, self.dept2)

    def test_officer_cannot_apply(self):
        tr = (
            self.env["hr.employee.transfer"]
            .with_user(self.manager)
            .create(
                {
                    "employee_id": self.employee.id,
                    "dest_company_id": self.company2.id,
                    "dest_department_id": self.dept2.id,
                }
            )
        )
        with self.assertRaises(AccessError):
            tr.with_user(self.officer).action_confirm()

    def test_cancel_before_apply(self):
        tr = (
            self.env["hr.employee.transfer"]
            .with_user(self.manager)
            .create(
                {
                    "employee_id": self.employee.id,
                    "dest_company_id": self.company2.id,
                    "dest_department_id": self.dept2.id,
                }
            )
        )
        tr.action_confirm()
        company_before = self.employee.company_id
        tr.action_cancel()
        self.assertEqual(tr.state, "cancelled")
        self.assertEqual(self.employee.company_id, company_before)

    def test_done_cannot_unlink(self):
        tr = (
            self.env["hr.employee.transfer"]
            .with_user(self.manager)
            .create(
                {
                    "employee_id": self.employee.id,
                    "dest_company_id": self.company2.id,
                    "dest_department_id": self.dept2.id,
                }
            )
        )
        tr.action_confirm()
        tr.action_apply()
        with self.assertRaises(UserError):
            tr.unlink()

    def test_cannot_forge_state(self):
        tr = (
            self.env["hr.employee.transfer"]
            .with_user(self.manager)
            .create(
                {
                    "employee_id": self.employee.id,
                    "dest_company_id": self.company2.id,
                    "dest_department_id": self.dept2.id,
                }
            )
        )
        with self.assertRaises(UserError):
            tr.with_user(self.manager).write({"state": "done"})


# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged("post_install", "-at_install")
class TestAttendanceRegularization(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.officer = new_test_user(
            cls.env,
            login="att_officer",
            groups="hr_attendance.group_hr_attendance_officer,base.group_user",
        )
        cls.emp_user = new_test_user(cls.env, login="att_emp", groups="base.group_user")
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Att Emp", "user_id": cls.emp_user.id}
        )
        cls.category = cls.env["hr.attendance.regularization.category"].create(
            {"name": "Forgot to punch"}
        )

    def test_same_day_approve(self):
        reg = (
            self.env["hr.attendance.regularization"]
            .with_user(self.emp_user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "category_id": self.category.id,
                    "date_from": datetime(2026, 1, 10, 8, 0, 0),
                    "date_to": datetime(2026, 1, 10, 17, 0, 0),
                    "reason": "Missed punch",
                }
            )
        )
        reg.action_submit()
        reg.with_user(self.officer).action_approve()
        self.assertEqual(reg.state, "approved")
        self.assertEqual(len(reg.attendance_ids), 1)
        self.assertEqual(reg.attendance_ids.regularization_id, reg)

    def test_multi_day_split(self):
        reg = self.env["hr.attendance.regularization"].create(
            {
                "employee_id": self.employee.id,
                "category_id": self.category.id,
                "date_from": datetime(2026, 1, 10, 8, 0, 0),
                "date_to": datetime(2026, 1, 12, 17, 0, 0),
                "reason": "Travel",
            }
        )
        reg.action_submit()
        reg.with_user(self.officer).action_approve()
        self.assertEqual(len(reg.attendance_ids), 3)

    def test_overlap_blocked(self):
        self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime(2026, 1, 10, 9, 0, 0),
                "check_out": datetime(2026, 1, 10, 12, 0, 0),
            }
        )
        reg = self.env["hr.attendance.regularization"].create(
            {
                "employee_id": self.employee.id,
                "category_id": self.category.id,
                "date_from": datetime(2026, 1, 10, 8, 0, 0),
                "date_to": datetime(2026, 1, 10, 17, 0, 0),
                "reason": "Overlap",
            }
        )
        reg.action_submit()
        with self.assertRaises(UserError):
            reg.with_user(self.officer).action_approve()

    def test_employee_cannot_approve(self):
        reg = (
            self.env["hr.attendance.regularization"]
            .with_user(self.emp_user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "category_id": self.category.id,
                    "date_from": datetime(2026, 2, 1, 8, 0, 0),
                    "date_to": datetime(2026, 2, 1, 17, 0, 0),
                    "reason": "X",
                }
            )
        )
        reg.action_submit()
        with self.assertRaises(AccessError):
            reg.with_user(self.emp_user).action_approve()

    def test_cannot_forge_state(self):
        reg = (
            self.env["hr.attendance.regularization"]
            .with_user(self.emp_user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "category_id": self.category.id,
                    "date_from": datetime(2026, 3, 1, 8, 0, 0),
                    "date_to": datetime(2026, 3, 1, 17, 0, 0),
                    "reason": "Forge",
                }
            )
        )
        with self.assertRaises(UserError):
            reg.with_user(self.emp_user).write({"state": "approved"})

    def test_open_checkout_overlap(self):
        self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime(2026, 1, 10, 9, 0, 0),
                "check_out": False,
            }
        )
        reg = self.env["hr.attendance.regularization"].create(
            {
                "employee_id": self.employee.id,
                "category_id": self.category.id,
                "date_from": datetime(2026, 1, 10, 8, 0, 0),
                "date_to": datetime(2026, 1, 10, 17, 0, 0),
                "reason": "Overlap open",
            }
        )
        reg.action_submit()
        with self.assertRaises(UserError):
            reg.with_user(self.officer).action_approve()

# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged("post_install", "-at_install")
class TestHrResignation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hr_user = new_test_user(
            cls.env, login="resign_hr", groups="hr.group_hr_user,base.group_user"
        )
        cls.emp_user = new_test_user(
            cls.env, login="resign_emp", groups="base.group_user"
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Resign Emp",
                "user_id": cls.emp_user.id,
                "date_version": fields.Date.today() - timedelta(days=400),
            }
        )

    def test_confirm_approve_future_keeps_active(self):
        last = fields.Date.today() + timedelta(days=20)
        res = (
            self.env["hr.resignation"]
            .with_user(self.emp_user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "joining_date": fields.Date.today() - timedelta(days=400),
                    "expected_last_day": last,
                    "reason": "Personal",
                    "notice_days": 0,
                }
            )
        )
        res.with_user(self.emp_user).action_confirm()
        res.with_user(self.hr_user).action_approve()
        self.assertEqual(res.state, "approved")
        self.assertTrue(self.employee.active)

    def test_cron_archives_when_due(self):
        last = fields.Date.today()
        res = self.env["hr.resignation"].create(
            {
                "employee_id": self.employee.id,
                "joining_date": fields.Date.today() - timedelta(days=400),
                "expected_last_day": last,
                "reason": "Done",
                "notice_days": 0,
            }
        )
        res.action_confirm()
        res.with_user(self.hr_user).action_approve()
        self.assertFalse(self.employee.active)
        self.assertEqual(res.state, "done")
        if "hr.employee.departure" in self.env:
            departure = self.env["hr.employee.departure"].search(
                [("employee_id", "=", self.employee.id)], limit=1
            )
            self.assertTrue(departure)
            self.assertEqual(departure.departure_date, last)

    def test_employee_cannot_approve(self):
        res = (
            self.env["hr.resignation"]
            .with_user(self.emp_user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "joining_date": fields.Date.today() - timedelta(days=400),
                    "expected_last_day": fields.Date.today() + timedelta(days=10),
                    "reason": "X",
                }
            )
        )
        res.with_user(self.emp_user).action_confirm()
        with self.assertRaises(AccessError):
            res.with_user(self.emp_user).action_approve()

    def test_duplicate_open_blocked(self):
        vals = {
            "employee_id": self.employee.id,
            "joining_date": fields.Date.today() - timedelta(days=400),
            "expected_last_day": fields.Date.today() + timedelta(days=5),
            "reason": "A",
        }
        r1 = self.env["hr.resignation"].create(vals)
        r1.action_confirm()
        r2 = self.env["hr.resignation"].create(dict(vals, reason="B"))
        with self.assertRaises(Exception):
            r2.action_confirm()

    def test_cannot_forge_state(self):
        res = (
            self.env["hr.resignation"]
            .with_user(self.emp_user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "joining_date": fields.Date.today() - timedelta(days=400),
                    "expected_last_day": fields.Date.today() + timedelta(days=10),
                    "reason": "X",
                }
            )
        )
        with self.assertRaises(UserError):
            res.with_user(self.emp_user).write({"state": "approved"})
        with self.assertRaises(UserError):
            res.with_user(self.hr_user).write({"state": "done"})

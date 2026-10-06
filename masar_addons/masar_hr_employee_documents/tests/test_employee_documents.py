# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged("post_install", "-at_install")
class TestEmployeeDocuments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Doc Emp"})
        cls.dtype = cls.env["hr.employee.document.type"].create(
            {
                "name": "Passport",
                "code": "PASS",
                "checklist_kind": "entry",
                "requires_expiry": True,
            }
        )
        cls.dtype2 = cls.env["hr.employee.document.type"].create(
            {
                "name": "ID Card",
                "code": "ID",
                "checklist_kind": "entry",
            }
        )

    def test_state_and_checklist(self):
        today = fields.Date.today()
        doc = self.env["hr.employee.document"].create(
            {
                "name": "P-1",
                "employee_id": self.employee.id,
                "document_type_id": self.dtype.id,
                "expiry_date": today + timedelta(days=5),
                "before_days": 10,
                "notification_type": "before_days",
            }
        )
        self.assertEqual(doc.state, "expiring_soon")
        self.employee.invalidate_recordset()
        self.assertEqual(self.employee.document_count, 1)
        self.assertAlmostEqual(self.employee.entry_checklist_progress, 50.0)

    def test_daily_after_not_before_expiry(self):
        today = fields.Date.today()
        doc = self.env["hr.employee.document"].create(
            {
                "name": "P-2",
                "employee_id": self.employee.id,
                "document_type_id": self.dtype.id,
                "expiry_date": today + timedelta(days=3),
                "before_days": 5,
                "notification_type": "daily_after",
            }
        )
        self.assertFalse(doc._should_notify_today())

    def test_cron_idempotent(self):
        today = fields.Date.today()
        doc = self.env["hr.employee.document"].create(
            {
                "name": "P-3",
                "employee_id": self.employee.id,
                "document_type_id": self.dtype.id,
                "expiry_date": today,
                "notification_type": "on_expiry",
            }
        )
        self.env["hr.employee.document"]._cron_document_expiry_reminders()
        self.assertEqual(doc.last_reminder_date, today)
        self.env["hr.employee.document"]._cron_document_expiry_reminders()
        self.assertEqual(doc.last_reminder_date, today)

    def test_past_expiry_allowed(self):
        today = fields.Date.today()
        doc = self.env["hr.employee.document"].create(
            {
                "name": "OLD",
                "employee_id": self.employee.id,
                "document_type_id": self.dtype.id,
                "expiry_date": today - timedelta(days=10),
                "notification_type": "none",
            }
        )
        self.assertEqual(doc.state, "expired")

    def test_confidential_default_from_type(self):
        conf_type = self.env["hr.employee.document.type"].create(
            {"name": "Disciplinary Letter", "code": "DISC", "confidential_default": True}
        )
        doc = self.env["hr.employee.document"].create(
            {
                "name": "D-1",
                "employee_id": self.employee.id,
                "document_type_id": conf_type.id,
                "notification_type": "none",
            }
        )
        self.assertTrue(doc.is_confidential)

    def test_employee_cannot_see_confidential_own_document(self):
        """Privacy: the employee must not see HR-only documents filed under them."""
        emp_user = new_test_user(
            self.env, login="doc_emp_user", groups="base.group_user"
        )
        employee = self.env["hr.employee"].create(
            {"name": "Portal Emp", "user_id": emp_user.id}
        )
        visible_doc = self.env["hr.employee.document"].create(
            {
                "name": "V-1",
                "employee_id": employee.id,
                "document_type_id": self.dtype2.id,
                "notification_type": "none",
            }
        )
        secret_doc = self.env["hr.employee.document"].create(
            {
                "name": "S-1",
                "employee_id": employee.id,
                "document_type_id": self.dtype2.id,
                "is_confidential": True,
                "notification_type": "none",
            }
        )
        seen = (
            self.env["hr.employee.document"]
            .with_user(emp_user)
            .search([("employee_id", "=", employee.id)])
        )
        self.assertIn(visible_doc, seen)
        self.assertNotIn(secret_doc, seen)

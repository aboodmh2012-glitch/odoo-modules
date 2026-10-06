# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo.tests import Form

from .common import TestPayslipBase


class TestWorkedDays(TestPayslipBase):
    def setUp(self):
        super().setUp()

        self.LeaveRequest = self.env["hr.leave"]
        WorkEntryType = self.env["hr.work.entry.type"]
        wet_vals = {
            "name": "TestLeaveType",
            "code": "GLOBAL",
            "count_as": "absence",
        }
        if "requires_allocation" in WorkEntryType._fields:
            wet_vals["requires_allocation"] = False
        if "time_off_selectable" in WorkEntryType._fields:
            wet_vals["time_off_selectable"] = True
        self.holiday_type = WorkEntryType.search(
            [("code", "=", "GLOBAL")], limit=1
        ) or WorkEntryType.create(wet_vals)

        self.full_calendar = self.ResourceCalendar.create(
            {
                "name": "56 Hrs a week",
            }
        )
        # Create a full 7-day week sor our tests don't fail on Sat. and Sun.
        for day in ["0", "1", "2", "3", "4", "5", "6"]:
            self.CalendarAttendance.create(
                {
                    "calendar_id": self.full_calendar.id,
                    "dayofweek": day,
                    "name": "Morning",
                    "day_period": "morning",
                    "hour_from": 8,
                    "hour_to": 12,
                }
            )
            self.CalendarAttendance.create(
                {
                    "calendar_id": self.full_calendar.id,
                    "dayofweek": day,
                    "name": "Afternoon",
                    "day_period": "afternoon",
                    "hour_from": 13,
                    "hour_to": 17,
                }
            )

    def _common_contract_leave_setup(self):
        self.richard_emp.resource_id.calendar_id = self.full_calendar
        self.richard_emp.version_ids.resource_calendar_id = self.full_calendar

        # I put all eligible contracts (including Richard's) in an "open" state
        self.apply_contract_cron()

        leave = self.LeaveRequest.create(
            {
                "name": "Hol11",
                "employee_id": self.richard_emp.id,
                "work_entry_type_id": self.holiday_type.id,
                "request_date_from": date.today(),
                "request_date_to": date.today(),
            }
        )
        if leave.state != "validate":
            if hasattr(leave, "action_validate"):
                leave.sudo().action_validate()
            else:
                leave.sudo().write({"state": "validate"})

    def test_worked_days_negative(self):
        self._common_contract_leave_setup()

        # Set system parameter
        self.env["ir.config_parameter"].sudo().set_str(
            "payroll.leaves_positive", "False"
        )

        # I create an employee Payslip
        frm = Form(self.Payslip)
        frm.employee_id = self.richard_emp
        richard_payslip = frm.save()

        worked_days_codes = richard_payslip.worked_days_line_ids.mapped("code")
        self.assertIn(
            "GLOBAL", worked_days_codes, "The leave is in the 'Worked Days' list"
        )
        wdl_ids = richard_payslip.worked_days_line_ids.filtered(
            lambda x: x.code == "GLOBAL"
        )
        self.assertEqual(len(wdl_ids), 1, "There is only one line matching the leave")
        self.assertEqual(
            wdl_ids[0].number_of_days,
            -1.0,
            "The days worked value is a NEGATIVE number",
        )
        self.assertEqual(
            wdl_ids[0].number_of_hours,
            -8.0,
            "The hours worked value is a NEGATIVE number",
        )

    def test_leaves_positive(self):
        self._common_contract_leave_setup()

        # Set system parameter
        self.env["ir.config_parameter"].sudo().set_str(
            "payroll.leaves_positive", "True"
        )

        # I create an employee Payslip
        frm = Form(self.Payslip)
        frm.employee_id = self.richard_emp
        richard_payslip = frm.save()

        worked_days_codes = richard_payslip.worked_days_line_ids.mapped("code")
        self.assertIn(
            "GLOBAL", worked_days_codes, "The leave is in the 'Worked Days' list"
        )
        wdl_ids = richard_payslip.worked_days_line_ids.filtered(
            lambda x: x.code == "GLOBAL"
        )
        self.assertEqual(len(wdl_ids), 1, "There is only one line matching the leave")
        self.assertEqual(
            wdl_ids[0].number_of_days, 1.0, "The days worked value is a POSITIVE number"
        )
        self.assertEqual(
            wdl_ids[0].number_of_hours,
            8.0,
            "The hours worked value is a POSITIVE number",
        )

# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


WORKFLOW_PROTECTED = frozenset({"state"})
CHATTER_FIELDS = frozenset(
    {"message_main_attachment_id", "message_follower_ids", "activity_ids"}
)
EMPLOYEE_DRAFT_FIELDS = frozenset(
    {
        "category_id",
        "date_from",
        "date_to",
        "reason",
        "employee_id",
    }
)


class HrAttendanceRegularization(models.Model):
    _name = "hr.attendance.regularization"
    _description = "Attendance Regularization"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(
        required=True, copy=False, readonly=True, default=lambda self: _("New")
    )
    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        tracking=True,
        default=lambda self: self.env.user.employee_id,
        check_company=True,
    )
    company_id = fields.Many2one(
        related="employee_id.company_id", store=True, index=True
    )
    category_id = fields.Many2one(
        "hr.attendance.regularization.category", required=True
    )
    date_from = fields.Datetime(required=True, tracking=True)
    date_to = fields.Datetime(required=True, tracking=True)
    reason = fields.Text(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
        copy=False,
        index=True,
    )
    attendance_ids = fields.One2many(
        "hr.attendance", "regularization_id", string="Created Attendances"
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from >= rec.date_to:
                raise ValidationError(_("Check-out must be after check-in."))

    def _is_officer(self):
        return self.env.user.has_group("hr_attendance.group_hr_attendance_officer")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("hr.attendance.regularization")
                    or _("New")
                )
            if vals.get("state") and vals["state"] != "draft":
                raise UserError(_("New regularizations must start in draft."))
            if not self._is_officer():
                emp = self.env.user.employee_id
                if vals.get("employee_id") and emp and vals["employee_id"] != emp.id:
                    raise AccessError(_("You can only create requests for yourself."))
                if emp:
                    vals["employee_id"] = vals.get("employee_id") or emp.id
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & WORKFLOW_PROTECTED:
            raise UserError(
                _("State can only be changed through workflow actions.")
            )
        is_officer = self._is_officer()
        for rec in self:
            if not is_officer:
                if rec.state != "draft":
                    raise AccessError(_("You can only edit draft requests."))
                forbidden = set(vals) - EMPLOYEE_DRAFT_FIELDS - CHATTER_FIELDS
                if forbidden:
                    raise AccessError(
                        _("You cannot modify: %s") % ", ".join(sorted(forbidden))
                    )
            elif rec.state == "approved" and set(vals) - CHATTER_FIELDS:
                raise UserError(_("Approved regularizations cannot be edited."))
        return super().write(vals)

    def _workflow_write(self, vals):
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == "approved":
                raise UserError(_("Approved regularizations cannot be deleted."))
        return super().unlink()

    def _assert_state(self, allowed):
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_("Invalid transition from %s") % rec.state)

    def action_submit(self):
        self._assert_state({"draft"})
        self._workflow_write({"state": "submitted"})
        return True

    def action_reject(self):
        if not self._is_officer():
            raise AccessError(_("Only attendance officers can reject requests."))
        self._assert_state({"submitted"})
        self._workflow_write({"state": "rejected"})
        return True

    def _iter_day_spans(self):
        """Split datetime range into per-calendar-day check_in/check_out pairs."""
        self.ensure_one()
        start = fields.Datetime.to_datetime(self.date_from)
        end = fields.Datetime.to_datetime(self.date_to)
        day = start.date()
        last = end.date()
        while day <= last:
            day_start = datetime.combine(day, time.min)
            # Avoid time.max microseconds which confuse attendance math
            day_end = datetime.combine(day, time(23, 59, 59))
            check_in = max(start, day_start)
            check_out = min(end, day_end)
            if check_in < check_out:
                yield check_in, check_out
            day = day + timedelta(days=1)

    def action_approve(self):
        if not self._is_officer():
            raise AccessError(_("Only attendance officers can approve requests."))
        self._assert_state({"submitted"})
        Attendance = self.env["hr.attendance"]
        for rec in self:
            created = Attendance.browse()
            for check_in, check_out in rec._iter_day_spans():
                overlap = Attendance.search(
                    [
                        ("employee_id", "=", rec.employee_id.id),
                        ("check_in", "<", fields.Datetime.to_string(check_out)),
                        "|",
                        ("check_out", "=", False),
                        ("check_out", ">", fields.Datetime.to_string(check_in)),
                    ],
                    limit=1,
                )
                if overlap:
                    raise UserError(
                        _(
                            "Overlapping attendance exists for %(employee)s "
                            "(%(existing)s).",
                            employee=rec.employee_id.name,
                            existing=overlap.display_name,
                        )
                    )
                created |= Attendance.create(
                    {
                        "employee_id": rec.employee_id.id,
                        "check_in": check_in,
                        "check_out": check_out,
                        "regularization_id": rec.id,
                    }
                )
            rec._workflow_write({"state": "approved"})
            rec.message_post(
                body=_("Created %s attendance record(s).") % len(created)
            )
        return True

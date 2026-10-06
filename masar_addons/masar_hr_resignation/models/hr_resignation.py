# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


WORKFLOW_PROTECTED = frozenset(
    {"state", "confirm_date", "approved_last_day", "archived_on"}
)
CHATTER_FIELDS = frozenset(
    {"message_main_attachment_id", "message_follower_ids", "activity_ids"}
)
EMPLOYEE_DRAFT_FIELDS = frozenset(
    {
        "expected_last_day",
        "reason",
        "notice_days",
        "resignation_type",
        "joining_date",
        "employee_id",
    }
)


class HrResignation(models.Model):
    _name = "hr.resignation"
    _description = "Employee Resignation"
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
    department_id = fields.Many2one(
        related="employee_id.department_id", store=True
    )
    company_id = fields.Many2one(
        "res.company",
        related="employee_id.company_id",
        store=True,
        index=True,
    )
    joining_date = fields.Date(
        help="Employment start date (set manually or defaulted on create).",
    )
    expected_last_day = fields.Date(required=True, tracking=True)
    confirm_date = fields.Date(copy=False)
    approved_last_day = fields.Date(copy=False, tracking=True)
    notice_days = fields.Integer(default=30)
    resignation_type = fields.Selection(
        [
            ("resigned", "Resignation"),
            ("terminated", "Termination"),
        ],
        required=True,
        default="resigned",
        tracking=True,
    )
    reason = fields.Text(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("done", "Processed"),
        ],
        default="draft",
        tracking=True,
        copy=False,
        index=True,
    )
    archived_on = fields.Date(copy=False)

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id and not rec.joining_date:
                emp = rec.employee_id
                joining = False
                if "contract_date_start" in emp._fields and emp.contract_date_start:
                    joining = emp.contract_date_start
                elif emp.create_date:
                    joining = fields.Date.to_date(emp.create_date)
                rec.joining_date = joining

    @api.constrains("employee_id", "state")
    def _check_open_request(self):
        for rec in self:
            if rec.state not in ("confirmed", "approved"):
                continue
            others = self.search_count(
                [
                    ("employee_id", "=", rec.employee_id.id),
                    ("state", "in", ("confirmed", "approved")),
                    ("id", "!=", rec.id),
                ]
            )
            if others:
                raise ValidationError(
                    _("There is already an open resignation for this employee.")
                )

    def _is_hr(self):
        return self.env.user.has_group("hr.group_hr_user")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("hr.resignation") or _("New")
                )
            if set(vals) & (WORKFLOW_PROTECTED - {"state"}):
                raise UserError(_("Cannot set workflow fields on create."))
            if vals.get("state") and vals["state"] != "draft":
                raise UserError(_("New resignations must start in draft."))
            if not self._is_hr():
                emp = self.env.user.employee_id
                if not emp:
                    raise AccessError(_("No employee linked to your user."))
                if vals.get("employee_id") and vals["employee_id"] != emp.id:
                    raise AccessError(
                        _("You can only create a resignation for yourself.")
                    )
                vals["employee_id"] = emp.id
        return super().create(vals_list)

    def write(self, vals):
        protected = set(vals) & WORKFLOW_PROTECTED
        if protected:
            raise UserError(
                _(
                    "Field(s) %(fields)s can only be changed through workflow actions.",
                    fields=", ".join(sorted(protected)),
                )
            )
        is_hr = self._is_hr()
        for rec in self:
            if not is_hr:
                if rec.state != "draft":
                    raise AccessError(
                        _("Employees can only edit resignations in draft.")
                    )
                forbidden = set(vals) - EMPLOYEE_DRAFT_FIELDS - CHATTER_FIELDS
                if forbidden:
                    raise AccessError(
                        _("You cannot modify: %s") % ", ".join(sorted(forbidden))
                    )
            elif rec.state in ("approved", "done"):
                if set(vals) - CHATTER_FIELDS:
                    raise UserError(
                        _("Approved/processed resignations cannot be edited directly.")
                    )
        return super().write(vals)

    def _workflow_write(self, vals):
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state not in ("draft", "cancelled", "rejected"):
                raise UserError(
                    _("Only draft/cancelled/rejected resignations can be deleted.")
                )
        return super().unlink()

    def _assert_state(self, allowed):
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_("Invalid transition from state %s.") % rec.state)

    def action_confirm(self):
        self._assert_state({"draft"})
        for rec in self:
            if not rec.joining_date:
                raise UserError(_("Please set the employee joining date."))
            if rec.expected_last_day <= rec.joining_date:
                raise UserError(_("Last day must be after joining date."))
        self._workflow_write(
            {
                "state": "confirmed",
                "confirm_date": fields.Date.context_today(self),
            }
        )
        return True

    def action_approve(self):
        if not self._is_hr():
            raise AccessError(_("Only HR can approve resignations."))
        self._assert_state({"confirmed"})
        for rec in self:
            last_day = rec.expected_last_day
            if rec.notice_days and rec.confirm_date:
                planned = rec.confirm_date + timedelta(days=rec.notice_days)
                if planned > last_day:
                    last_day = planned
            rec._workflow_write({"state": "approved", "approved_last_day": last_day})
            if last_day <= fields.Date.context_today(rec):
                rec._process_archive()
        return True

    def action_reject(self):
        if not self._is_hr():
            raise AccessError(_("Only HR can reject resignations."))
        self._assert_state({"confirmed"})
        self._workflow_write({"state": "rejected"})
        return True

    def action_cancel(self):
        self._assert_state({"draft", "confirmed"})
        self._workflow_write({"state": "cancelled"})
        return True

    def action_reset_draft(self):
        if not self.env.user.has_group("hr.group_hr_manager"):
            raise AccessError(_("Only HR managers can reset resignations."))
        self._assert_state({"rejected", "cancelled"})
        self._workflow_write(
            {"state": "draft", "confirm_date": False, "approved_last_day": False}
        )
        return True

    def _close_employee_versions(self, employee, last_day):
        """End open contract versions using Odoo 19 writable fields."""
        if "hr.version" not in self.env:
            return
        Version = self.env["hr.version"]
        domain = [("employee_id", "=", employee.id)]
        versions = Version.search(domain)
        for ver in versions:
            # Prefer contract_date_end (writable); skip if already ended before last_day
            if "contract_date_end" in ver._fields:
                if not ver.contract_date_end or ver.contract_date_end > last_day:
                    # Only close current/open versions
                    is_current = True
                    if "is_current" in ver._fields:
                        is_current = ver.is_current
                    elif "contract_date_start" in ver._fields and ver.contract_date_start:
                        is_current = ver.contract_date_start <= last_day
                    if is_current:
                        ver.contract_date_end = last_day
            if "departure_date" in ver._fields and not ver._fields["departure_date"].related:
                if not ver.departure_date:
                    ver.departure_date = last_day

    def _process_archive(self):
        """Archive employee safely without cloning or unlinking users by default."""
        deactivate_user = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_bool("masar_hr_resignation.deactivate_user")
        )
        for rec in self:
            employee = rec.employee_id
            if not employee.active:
                rec._workflow_write(
                    {"state": "done", "archived_on": fields.Date.context_today(rec)}
                )
                continue
            last_day = rec.approved_last_day
            # Native departure fields on employee when present
            emp_vals = {}
            if (
                "departure_date" in employee._fields
                and not employee._fields["departure_date"].related
            ):
                emp_vals["departure_date"] = last_day
            if emp_vals:
                employee.write(emp_vals)
            self._close_employee_versions(employee, last_day)
            employee.action_archive()
            if deactivate_user and employee.user_id:
                employee.user_id.active = False
            rec._workflow_write(
                {
                    "state": "done",
                    "archived_on": fields.Date.context_today(rec),
                }
            )
            rec.message_post(
                body=_("Employee archived as of %s") % rec.approved_last_day
            )

    @api.model
    def _cron_process_due_resignations(self):
        today = fields.Date.context_today(self)
        due = self.search(
            [
                ("state", "=", "approved"),
                ("approved_last_day", "<=", today),
            ]
        )
        due._process_archive()
        return True

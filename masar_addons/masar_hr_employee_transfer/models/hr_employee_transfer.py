# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


WORKFLOW_PROTECTED = frozenset(
    {
        "state",
        "source_company_id",
        "source_department_id",
        "source_job_id",
        "source_parent_id",
        "source_coach_id",
        "source_work_location_id",
    }
)
CHATTER_FIELDS = frozenset(
    {"message_main_attachment_id", "message_follower_ids", "activity_ids"}
)


class HrEmployeeTransfer(models.Model):
    """Audit record for moving the SAME employee (no clone/archive)."""

    _name = "hr.employee.transfer"
    _description = "Employee Transfer"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(
        required=True, copy=False, readonly=True, default=lambda self: _("New")
    )
    employee_id = fields.Many2one(
        "hr.employee", required=True, tracking=True, index=True
    )
    transfer_date = fields.Date(
        required=True, default=fields.Date.context_today, tracking=True
    )
    responsible_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, required=True
    )
    note = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        string="Source Company (stored)",
        related="source_company_id",
        store=True,
        index=True,
    )

    source_company_id = fields.Many2one("res.company", copy=False)
    source_department_id = fields.Many2one("hr.department", copy=False)
    source_job_id = fields.Many2one("hr.job", copy=False)
    source_parent_id = fields.Many2one(
        "hr.employee", string="Source Manager", copy=False
    )
    source_coach_id = fields.Many2one("hr.employee", copy=False)
    source_work_location_id = fields.Many2one("hr.work.location", copy=False)

    dest_company_id = fields.Many2one("res.company", required=True, tracking=True)
    dest_department_id = fields.Many2one(
        "hr.department", tracking=True, check_company=False
    )
    dest_job_id = fields.Many2one("hr.job", tracking=True, check_company=False)
    dest_parent_id = fields.Many2one(
        "hr.employee", string="Destination Manager", tracking=True
    )
    dest_coach_id = fields.Many2one("hr.employee", tracking=True)
    dest_work_location_id = fields.Many2one("hr.work.location", tracking=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
        copy=False,
        index=True,
    )

    @api.constrains(
        "dest_company_id",
        "dest_department_id",
        "dest_job_id",
        "dest_parent_id",
        "dest_work_location_id",
    )
    def _check_dest_company_consistency(self):
        for rec in self:
            company = rec.dest_company_id
            if not company:
                continue
            if (
                rec.dest_department_id
                and rec.dest_department_id.company_id
                and rec.dest_department_id.company_id != company
            ):
                raise ValidationError(
                    _("Destination department must belong to the destination company.")
                )
            if (
                rec.dest_job_id
                and rec.dest_job_id.company_id
                and rec.dest_job_id.company_id != company
            ):
                raise ValidationError(
                    _("Destination job must belong to the destination company.")
                )
            if (
                rec.dest_parent_id
                and rec.dest_parent_id.company_id
                and rec.dest_parent_id.company_id != company
            ):
                raise ValidationError(
                    _("Destination manager must belong to the destination company.")
                )
            if (
                rec.dest_work_location_id
                and "company_id" in rec.dest_work_location_id._fields
                and rec.dest_work_location_id.company_id
                and rec.dest_work_location_id.company_id != company
            ):
                raise ValidationError(
                    _("Destination work location must belong to the destination company.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("hr.employee.transfer")
                    or _("New")
                )
            if vals.get("state") and vals["state"] != "draft":
                raise UserError(_("New transfers must start in draft."))
            if set(vals) & (WORKFLOW_PROTECTED - {"state"}):
                raise UserError(_("Cannot set source snapshot fields on create."))
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & WORKFLOW_PROTECTED:
            raise UserError(
                _(
                    "Field(s) %(fields)s can only be changed through workflow actions.",
                    fields=", ".join(sorted(set(vals) & WORKFLOW_PROTECTED)),
                )
            )
        for rec in self:
            if rec.state in ("done", "cancelled") and set(vals) - CHATTER_FIELDS:
                raise UserError(
                    _("Done/cancelled transfers cannot be edited directly.")
                )
            if rec.state == "confirmed":
                # After confirm, destination is frozen except note via chatter
                dest_fields = {
                    "employee_id",
                    "dest_company_id",
                    "dest_department_id",
                    "dest_job_id",
                    "dest_parent_id",
                    "dest_coach_id",
                    "dest_work_location_id",
                    "transfer_date",
                }
                if set(vals) & dest_fields:
                    raise UserError(
                        _("Confirmed transfers cannot change destination fields.")
                    )
        return super().write(vals)

    def _workflow_write(self, vals):
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == "done":
                raise UserError(_("Applied transfers cannot be deleted."))
        return super().unlink()

    def _assert_state(self, allowed):
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_("Invalid transition from %s") % rec.state)

    def _require_hr_manager(self):
        if not self.env.user.has_group("hr.group_hr_manager"):
            raise AccessError(_("Only HR managers can perform this action."))

    def action_confirm(self):
        self._require_hr_manager()
        self._assert_state({"draft"})
        for rec in self:
            emp = rec.employee_id
            if rec.dest_company_id == emp.company_id and not any(
                [
                    rec.dest_department_id
                    and rec.dest_department_id != emp.department_id,
                    rec.dest_job_id and rec.dest_job_id != emp.job_id,
                    rec.dest_parent_id and rec.dest_parent_id != emp.parent_id,
                    rec.dest_work_location_id
                    and "work_location_id" in emp._fields
                    and rec.dest_work_location_id != emp.work_location_id,
                ]
            ):
                if (
                    (
                        not rec.dest_department_id
                        or rec.dest_department_id == emp.department_id
                    )
                    and (not rec.dest_job_id or rec.dest_job_id == emp.job_id)
                    and (not rec.dest_parent_id or rec.dest_parent_id == emp.parent_id)
                ):
                    raise ValidationError(
                        _("Destination must differ from the current assignment.")
                    )
            vals = {
                "source_company_id": emp.company_id.id,
                "source_department_id": emp.department_id.id,
                "source_job_id": emp.job_id.id,
                "source_parent_id": emp.parent_id.id,
                "source_coach_id": emp.coach_id.id
                if "coach_id" in emp._fields
                else False,
                "state": "confirmed",
            }
            if "work_location_id" in emp._fields:
                vals["source_work_location_id"] = emp.work_location_id.id
            rec._workflow_write(vals)
        return True

    def action_apply(self):
        self._require_hr_manager()
        self._assert_state({"confirmed"})
        for rec in self:
            emp = rec.employee_id
            emp_id_before = emp.id
            write_vals = {"company_id": rec.dest_company_id.id}
            if rec.dest_department_id:
                write_vals["department_id"] = rec.dest_department_id.id
            if rec.dest_job_id:
                write_vals["job_id"] = rec.dest_job_id.id
            if rec.dest_parent_id:
                write_vals["parent_id"] = rec.dest_parent_id.id
            if rec.dest_coach_id and "coach_id" in emp._fields:
                write_vals["coach_id"] = rec.dest_coach_id.id
            if rec.dest_work_location_id and "work_location_id" in emp._fields:
                write_vals["work_location_id"] = rec.dest_work_location_id.id
            emp.write(write_vals)
            if emp.user_id and rec.dest_company_id:
                emp.user_id.sudo().write(
                    {
                        "company_ids": [(4, rec.dest_company_id.id)],
                        "company_id": rec.dest_company_id.id,
                    }
                )
            if emp.id != emp_id_before:
                raise UserError(_("Transfer must keep the same employee record."))
            rec._workflow_write({"state": "done"})
            rec.message_post(
                body=_(
                    "Applied transfer for %(employee)s from %(src)s to %(dest)s.",
                    employee=emp.name,
                    src=rec.source_company_id.display_name,
                    dest=rec.dest_company_id.display_name,
                )
            )
        return True

    def action_cancel(self):
        self._require_hr_manager()
        self._assert_state({"draft", "confirmed"})
        self._workflow_write({"state": "cancelled"})
        return True

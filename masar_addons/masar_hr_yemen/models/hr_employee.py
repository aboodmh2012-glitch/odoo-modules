# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # --- Unified employee lifecycle (simple, on-the-fly view) ---
    masar_lifecycle_stage = fields.Selection(
        [
            ("probation", "Probation"),
            ("active", "Active"),
            ("notice", "Notice / Offboarding"),
            ("archived", "Archived"),
        ],
        string="Lifecycle Stage",
        compute="_compute_masar_lifecycle_stage",
        help="Where the employee is in the lifecycle: probation → active → "
        "notice → archived. Derived from trial end, any open resignation, "
        "and active state.",
    )
    masar_resignation_count = fields.Integer(compute="_compute_masar_hr_counts")
    masar_transfer_count = fields.Integer(compute="_compute_masar_hr_counts")

    def _compute_masar_lifecycle_stage(self):
        today = fields.Date.context_today(self)
        open_by_emp = {}
        if "hr.resignation" in self.env and self.ids:
            for employee, count in self.env["hr.resignation"]._read_group(
                [
                    ("employee_id", "in", self.ids),
                    ("state", "in", ("confirmed", "approved")),
                ],
                ["employee_id"],
                ["__count"],
            ):
                open_by_emp[employee.id] = count
        for emp in self:
            if not emp.active:
                emp.masar_lifecycle_stage = "archived"
            elif open_by_emp.get(emp.id):
                emp.masar_lifecycle_stage = "notice"
            elif emp.trial_date_end and emp.trial_date_end >= today:
                emp.masar_lifecycle_stage = "probation"
            else:
                emp.masar_lifecycle_stage = "active"

    def _compute_masar_hr_counts(self):
        res_map = {}
        tr_map = {}
        if "hr.resignation" in self.env and self.ids:
            for employee, count in self.env["hr.resignation"]._read_group(
                [("employee_id", "in", self.ids)], ["employee_id"], ["__count"]
            ):
                res_map[employee.id] = count
        if "hr.employee.transfer" in self.env and self.ids:
            for employee, count in self.env["hr.employee.transfer"]._read_group(
                [("employee_id", "in", self.ids)], ["employee_id"], ["__count"]
            ):
                tr_map[employee.id] = count
        for emp in self:
            emp.masar_resignation_count = res_map.get(emp.id, 0)
            emp.masar_transfer_count = tr_map.get(emp.id, 0)

    def action_masar_lifecycle(self):
        # Stage badge button is informational only.
        return False

    def action_masar_view_resignations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Resignations"),
            "res_model": "hr.resignation",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }

    def action_masar_view_transfers(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Transfers"),
            "res_model": "hr.employee.transfer",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }

    @api.constrains("trial_date_end", "contract_date_start")
    def _check_masar_probation_max(self):
        for emp in self:
            company = emp.company_id
            max_days = company.masar_hr_probation_max_days or 180
            start = emp.contract_date_start
            trial_end = emp.trial_date_end
            if start and trial_end:
                if (trial_end - start).days > max_days:
                    raise ValidationError(
                        _(
                            "Probation for %(emp)s exceeds %(days)s days "
                            "(Labor Law Art. 28 — max six months).",
                            emp=emp.display_name,
                            days=max_days,
                        )
                    )

    @api.model
    def _cron_probation_ending_reminder(self):
        today = fields.Date.context_today(self)
        ActivityType = self.env.ref(
            "masar_hr_yemen.mail_act_probation_ending", raise_if_not_found=False
        )
        if not ActivityType:
            return True
        for company in self.env["res.company"].search([]):
            warn = company.masar_hr_probation_warn_days or 14
            horizon = today + timedelta(days=warn)
            employees = self.search(
                [
                    ("company_id", "=", company.id),
                    ("trial_date_end", "!=", False),
                    ("trial_date_end", ">=", today),
                    ("trial_date_end", "<=", horizon),
                    ("active", "=", True),
                ]
            )
            hr_group = self.env.ref(
                "hr.group_hr_user", raise_if_not_found=False
            )
            hr_users = hr_group.users if hr_group else self.env["res.users"]
            for emp in employees:
                existing = emp.activity_ids.filtered(
                    lambda a, t=ActivityType: a.activity_type_id == t
                )
                if existing:
                    continue
                user = emp.parent_id.user_id or (hr_users[:1] and hr_users[0])
                if not user:
                    continue
                emp.activity_schedule(
                    "masar_hr_yemen.mail_act_probation_ending",
                    date_deadline=emp.trial_date_end,
                    user_id=user.id,
                    summary=_("Probation ending: %s") % emp.name,
                    note=_(
                        "Trial end %(date)s (company max %(max)s days — Art. 28).",
                        date=emp.trial_date_end,
                        max=company.masar_hr_probation_max_days or 180,
                    ),
                )
        return True

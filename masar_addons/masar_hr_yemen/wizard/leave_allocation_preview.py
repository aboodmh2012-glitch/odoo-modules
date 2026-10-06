# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class MasarLeaveAllocationPreview(models.TransientModel):
    _name = "masar.leave.allocation.preview"
    _description = "Leave Allocation Preview (no create)"

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    as_of_date = fields.Date(
        required=True, default=fields.Date.context_today
    )
    line_ids = fields.One2many(
        "masar.leave.allocation.preview.line", "preview_id", string="Preview lines"
    )
    note = fields.Html(
        default=lambda self: _(
            "<p>Preview only — <b>does not create</b> allocations. "
            "Annual estimate = max(company annual days, months of service × "
            "monthly accrual) per Art. 79. Review then allocate manually or "
            "via standard Time Off allocation.</p>"
        )
    )

    def action_compute(self):
        self.ensure_one()
        self.line_ids.unlink()
        company = self.company_id
        annual = company.masar_hr_annual_leave_days or 30.0
        per_month = company.masar_hr_annual_leave_per_month or 2.5
        casual = company.masar_hr_casual_leave_days or 10.0
        lines = []
        employees = self.env["hr.employee"].search(
            [("company_id", "=", company.id), ("active", "=", True)]
        )
        for emp in employees:
            start = emp.contract_date_start
            months = 0
            if start:
                rd = relativedelta(self.as_of_date, start)
                months = max(0, rd.years * 12 + rd.months)
            # Art. 79: ≥2.5 days/month; full year floor = company annual days (default 30)
            if months >= 12:
                suggested = annual
            else:
                suggested = months * per_month
            lines.append(
                {
                    "preview_id": self.id,
                    "employee_id": emp.id,
                    "contract_date_start": start,
                    "service_months": months,
                    "suggested_annual_days": suggested,
                    "suggested_casual_days": casual,
                    "missing_contract_start": not bool(start),
                }
            )
        self.env["masar.leave.allocation.preview.line"].create(lines)
        return {
            "type": "ir.actions.act_window",
            "res_model": "masar.leave.allocation.preview",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }


class MasarLeaveAllocationPreviewLine(models.TransientModel):
    _name = "masar.leave.allocation.preview.line"
    _description = "Leave Allocation Preview Line"

    preview_id = fields.Many2one(
        "masar.leave.allocation.preview", required=True, ondelete="cascade"
    )
    employee_id = fields.Many2one("hr.employee", required=True)
    contract_date_start = fields.Date()
    service_months = fields.Integer()
    suggested_annual_days = fields.Float()
    suggested_casual_days = fields.Float()
    missing_contract_start = fields.Boolean()

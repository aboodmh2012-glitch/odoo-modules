# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    disciplinary_case_ids = fields.One2many(
        "hr.disciplinary.case",
        "employee_id",
        string="Disciplinary Cases",
    )
    disciplinary_case_count = fields.Integer(
        compute="_compute_disciplinary_case_count",
    )

    def _compute_disciplinary_case_count(self):
        data = self.env["hr.disciplinary.case"]._read_group(
            [("employee_id", "in", self.ids)],
            ["employee_id"],
            ["__count"],
        )
        mapped = {employee.id: count for employee, count in data}
        for employee in self:
            employee.disciplinary_case_count = mapped.get(employee.id, 0)

    def action_view_disciplinary_cases(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Disciplinary Cases",
            "res_model": "hr.disciplinary.case",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }

# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrDisciplineOffenseType(models.Model):
    _inherit = "hr.discipline.offense.type"

    legal_reference = fields.Char(
        string="Legal / policy reference",
        help="e.g. Labor Law Art. 93 / company discipline schedule clause.",
    )
    appeal_deadline_days = fields.Integer(
        default=lambda self: self.env.company.masar_hr_appeal_days_default or 30,
    )

    @api.model_create_multi
    def create(self, vals_list):
        default_days = self.env.company.masar_hr_appeal_days_default or 30
        for vals in vals_list:
            vals.setdefault("appeal_deadline_days", default_days)
        return super().create(vals_list)

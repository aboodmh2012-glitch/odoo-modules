# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrDisciplineSanctionType(models.Model):
    """Catalog of sanctions that can be applied to a disciplinary case."""

    _name = "hr.discipline.sanction.type"
    _description = "Disciplinary Sanction Type"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        index=True,
    )
    description = fields.Text(translate=True)
    has_financial_impact = fields.Boolean(
        help="Selecting this sanction requires a financial amount on the case.",
    )
    requires_approval_level = fields.Selection(
        [
            ("officer", "HR Officer"),
            ("manager", "HR Manager"),
            ("approver", "Disciplinary Approver"),
        ],
        default="manager",
        required=True,
    )
    _code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "Sanction code must be unique per company.",
    )

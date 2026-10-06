# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrDisciplineSanctionType(models.Model):
    _inherit = "hr.discipline.sanction.type"

    sanction_kind = fields.Selection(
        [
            ("notice", "Written notice (لفت نظر)"),
            ("warning", "Written warning (إنذار)"),
            ("deduction", "Wage deduction (خصم)"),
            ("dismissal", "Dismissal (فصل)"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
        help="Maps to Labor Law Art. 93 ladder. Suspension is NOT a sanction — "
        "use precautionary suspension on the case.",
    )
    requires_investigation = fields.Boolean(
        default=False,
        help="Art. 94/96: required for deduction and dismissal.",
    )

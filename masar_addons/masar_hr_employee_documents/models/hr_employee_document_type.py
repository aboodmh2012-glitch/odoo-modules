# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployeeDocumentType(models.Model):
    _name = "hr.employee.document.type"
    _description = "Employee Document Type"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, index=True
    )
    checklist_kind = fields.Selection(
        [
            ("entry", "Entry / Onboarding"),
            ("exit", "Exit / Offboarding"),
            ("compliance", "Compliance"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
    )
    requires_expiry = fields.Boolean(
        default=False,
        help="If set, documents of this type must carry an expiry date. "
        "Off by default — many documents (ID copy, signed NDA, contract) "
        "do not expire.",
    )
    confidential_default = fields.Boolean(
        string="Confidential by default",
        default=False,
        help="New documents of this type are hidden from the employee's own "
        "portal (HR-only). Use for disciplinary, medical or investigation files.",
    )
    default_notify_days = fields.Integer(default=30)
    _code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "Document type code must be unique per company.",
    )

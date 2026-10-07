# Copyright 2026 MASAR
# License LGPL-3.0 or later.
from odoo import fields, models


class DocumentPage(models.Model):
    _inherit = "document.page"

    masar_owner_dept_id = fields.Many2one(
        "hr.department", string="Owner department", tracking=True,
        help="The department accountable for this document.",
    )
    masar_owner_uid = fields.Many2one(
        "res.users", string="Document owner", tracking=True,
        help="The person accountable for keeping this document current.",
    )
    masar_doc_code = fields.Char(
        string="Document code", copy=False,
        help="Formal reference code, e.g. MASAR-SEC-POL-001.",
    )
    masar_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Classification", default="internal", tracking=True,
    )
    masar_effective_date = fields.Date(string="Effective date")
    masar_review_date = fields.Date(
        string="Next review", help="Date the document is next due for review.",
    )
    masar_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("under_review", "Under review"),
            ("retired", "Retired"),
        ],
        string="Lifecycle status", default="active", tracking=True,
    )
    masar_tag_ids = fields.Many2many(
        "masar.knowledge.tag", string="Tags",
        help="Cross-cutting topics that span several manuals.",
    )

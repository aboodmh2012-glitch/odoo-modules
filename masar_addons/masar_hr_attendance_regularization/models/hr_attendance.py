# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    regularization_id = fields.Many2one(
        "hr.attendance.regularization",
        string="Regularization Request",
        index=True,
        copy=False,
        ondelete="set null",
    )

# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAttendanceRegularizationCategory(models.Model):
    _name = "hr.attendance.regularization.category"
    _description = "Attendance Regularization Category"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)

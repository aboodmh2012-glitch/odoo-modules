# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    resignation_ids = fields.One2many("hr.resignation", "employee_id")

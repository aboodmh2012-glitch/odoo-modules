# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployeeTransfer(models.Model):
    _inherit = "hr.employee.transfer"

    change_kind = fields.Selection(
        [
            ("transfer", "Transfer"),
            ("promotion", "Promotion"),
            ("job", "Job change"),
            ("department", "Department change"),
            ("manager", "Manager change"),
            ("location", "Location change"),
            ("schedule", "Work schedule change"),
            ("acting", "Acting / temporary assignment"),
            ("other", "Other employment change"),
        ],
        default="transfer",
        required=True,
        tracking=True,
        help="Documents the nature of the change. Salary changes should still be "
        "applied on hr.version after approval — this record is the audit trail.",
    )

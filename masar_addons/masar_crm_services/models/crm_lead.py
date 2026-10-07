from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    masar_requested_service = fields.Selection(
        selection=[
            ("payment_gateway", "Payment Gateway"),
            ("pos_solutions", "POS Solutions"),
            ("accounts_cards", "Accounts & Cards"),
            ("bulk_payments", "Bulk Payments"),
            ("bill_payments", "Bill Payments"),
            ("atms_cash", "ATMs & Cash"),
        ],
        string="Requested Service",
        tracking=True,
        index=True,
        help="MASAR service requested by the prospect or customer.",
    )
    masar_source_page = fields.Char(
        string="Source Page",
        tracking=True,
        help="Website page or external landing page that generated the request.",
    )

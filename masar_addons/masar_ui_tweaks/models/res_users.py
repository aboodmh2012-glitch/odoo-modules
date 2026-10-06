# Copyright 2026 MASAR
# License LGPL-3.0 or later.
from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _masar_quiet_first_run(self):
        """Disable first-run tours and public signup leftover."""
        self.sudo().search([("share", "=", False), ("tour_enabled", "=", True)]).write(
            {"tour_enabled": False}
        )
        params = self.env["ir.config_parameter"].sudo()
        # Odoo 20: set_param/get_param were removed; use typed setters.
        if params.get_str("auth_signup.invitation_scope") == "b2c":
            params.set_str("auth_signup.invitation_scope", "b2b")


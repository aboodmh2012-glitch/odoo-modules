# Copyright 2026 MASAR
# License LGPL-3.0 or later.
from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            "apps_menu_search_type",
            "apps_menu_theme",
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            "apps_menu_search_type",
            "apps_menu_theme",
        ]

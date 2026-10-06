# Copyright 2026 MASAR
# License LGPL-3.0 or later.
# Intentionally empty — preferences fields lived on web_responsive and are gone.
from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

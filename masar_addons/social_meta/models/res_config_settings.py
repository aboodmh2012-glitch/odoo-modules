# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    social_meta_app_id = fields.Char(
        string="Meta App ID",
        config_parameter="social.meta_app_id",
        help="Facebook / Instagram app ID used for Link account (OAuth).",
    )
    social_meta_app_secret = fields.Char(
        string="Meta App Secret",
        config_parameter="social.meta_app_secret",
        help="Stored as a system parameter. Prefer SOCIAL_META_APP_SECRET on the server in production.",
    )
    social_meta_config_id = fields.Char(
        string="Login for Business configuration ID",
        config_parameter="social.meta_config_id",
        help="Optional Meta configuration_id. When set, OAuth uses Facebook Login for Business "
        "config_id instead of a raw permission scope list.",
    )

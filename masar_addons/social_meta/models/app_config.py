# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
"""One-shot Meta App credentials — opened only from Connect Facebook when needed."""
import os
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


def normalize_meta_app_id(value):
    """Keep digits only — Meta App IDs are numeric (Settings → Basic)."""
    return re.sub(r"\D", "", (value or "").strip())


class SocialMetaAppConfig(models.TransientModel):
    _name = "social.meta.app.config"
    _description = "Connect Facebook · Meta App"

    app_id = fields.Char(
        string="App ID",
        required=True,
        help="Digits only from Meta → Settings → Basic (not the app name).",
    )
    app_secret = fields.Char(string="App Secret", required=True)
    config_id = fields.Char(
        string="Configuration ID (optional)",
        help="From Facebook Login for Business → Configurations.",
    )
    redirect_uri = fields.Char(string="Copy this into Meta → Valid OAuth Redirect URIs", readonly=True)
    media_type = fields.Selection(
        [("facebook", "Facebook"), ("instagram", "Instagram")],
        default="facebook",
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ICP = self.env["ir.config_parameter"].sudo()
        res["app_id"] = normalize_meta_app_id(
            ICP.get_param("social.meta_app_id") or os.environ.get("SOCIAL_META_APP_ID") or ""
        )
        res["app_secret"] = (ICP.get_param("social.meta_app_secret") or "").strip()
        res["config_id"] = (
            ICP.get_param("social.meta_config_id") or os.environ.get("SOCIAL_META_CONFIG_ID") or ""
        ).strip()
        base = (ICP.get_param("web.base.url") or "").rstrip("/")
        res["redirect_uri"] = f"{base}/social/meta/oauth/callback" if base else ""
        if not res.get("media_type"):
            res["media_type"] = "facebook"
        return res

    def _store_credentials(self):
        self.ensure_one()
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can configure the Meta app."))
        app_id = normalize_meta_app_id(self.app_id)
        secret = (self.app_secret or "").strip()
        if not app_id or not secret:
            raise UserError(_("Enter both App ID and App Secret from Meta → Settings → Basic."))
        if len(app_id) < 6:
            raise UserError(
                _(
                    "App ID is numbers only (example 123456789012345). "
                    "Open developers.facebook.com → your app → Settings → Basic — copy App ID, not the app name."
                )
            )
        if not self.redirect_uri:
            raise UserError(_("Set web.base.url first (Settings → System Parameters)."))
        self.app_id = app_id
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("social.meta_app_id", app_id)
        ICP.set_param("social.meta_app_secret", secret)
        ICP.set_param("social.meta_config_id", (self.config_id or "").strip())

    def action_save_and_link(self):
        """Single CTA: save credentials → open Facebook Login."""
        self.ensure_one()
        self._store_credentials()
        return self.env["social.meta.oauth"].action_start(self.media_type or "facebook")

    @api.model
    def action_open(self, media_type=None):
        wiz = self.create({"media_type": media_type or "facebook"})
        return {
            "type": "ir.actions.act_window",
            "name": _("Connect Facebook · one-time setup"),
            "res_model": "social.meta.app.config",
            "res_id": wiz.id,
            "view_mode": "form",
            "target": "new",
        }

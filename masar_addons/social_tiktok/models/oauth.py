# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import timedelta
from urllib.parse import urlencode

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

from . import api as tt_api

_logger = logging.getLogger(__name__)


class SocialTiktokOauth(models.TransientModel):
    _name = "social.tiktok.oauth"
    _description = "TikTok OAuth Link Helper"

    @api.model
    def _app_credentials(self):
        ICP = self.env["ir.config_parameter"].sudo()
        client_key = (os.environ.get("SOCIAL_TIKTOK_CLIENT_KEY") or "").strip() or (
            ICP.get_str("social.tiktok_client_key") or ""
        ).strip()
        client_secret = (os.environ.get("SOCIAL_TIKTOK_CLIENT_SECRET") or "").strip() or (
            ICP.get_str("social.tiktok_client_secret") or ""
        ).strip()
        if not client_key or not client_secret:
            raise UserError(
                _(
                    "TikTok is not configured on this server yet.\n\n"
                    "An administrator must set SOCIAL_TIKTOK_CLIENT_KEY and "
                    "SOCIAL_TIKTOK_CLIENT_SECRET once (TikTok for Developers app with the "
                    "Content Posting API and a passed app audit for public posts). After "
                    "that, Link account opens TikTok directly."
                )
            )
        return client_key, client_secret

    @api.model
    def _credentials_configured(self):
        try:
            self._app_credentials()
            return True
        except UserError:
            return False

    @api.model
    def _redirect_uri(self):
        base = self.env["ir.config_parameter"].sudo().get_str("web.base.url")
        if not base:
            raise UserError(_("Set web.base.url before linking TikTok accounts."))
        return base.rstrip("/") + "/social/tiktok/oauth/callback"

    @api.model
    def _sign_state(self, payload):
        _key, secret = self._app_credentials()
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        return f"{sig}.{body}"

    @api.model
    def _parse_state(self, state):
        if not state or "." not in state:
            raise UserError(_("Invalid OAuth state."))
        sig, body = state.split(".", 1)
        _key, secret = self._app_credentials()
        expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise UserError(_("OAuth state signature mismatch."))
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as err:
            raise UserError(_("Invalid OAuth state.")) from err
        if payload.get("uid") != self.env.uid:
            raise AccessError(_("OAuth session belongs to another user."))
        if time.time() - float(payload.get("ts") or 0) > 900:
            raise UserError(_("OAuth session expired. Click Link account again."))
        return payload

    @api.model
    def action_start(self):
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can link TikTok accounts."))
        client_key, _secret = self._app_credentials()
        state = self._sign_state(
            {
                "uid": self.env.uid,
                "company_id": self.env.company.id,
                "ts": int(time.time()),
                "nonce": secrets.token_hex(8),
            }
        )
        params = {
            "client_key": client_key,
            "response_type": "code",
            "scope": tt_api.SCOPES,
            "redirect_uri": self._redirect_uri(),
            "state": state,
        }
        url = f"{tt_api.AUTH_URL}?{urlencode(params)}"
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    @api.model
    def exchange_code(self, code):
        client_key, client_secret = self._app_credentials()
        try:
            token_data = tt_api.exchange_token(client_key, client_secret, code, self._redirect_uri())
        except Exception as err:
            raise UserError(_("TikTok did not return an access token. Try again.")) from err
        access = token_data.get("access_token")
        refresh = token_data.get("refresh_token")
        open_id = token_data.get("open_id")
        if not access or not open_id:
            raise UserError(_("TikTok did not return a valid account token."))
        if not refresh:
            raise UserError(_("TikTok did not return a refresh token. Link account again."))
        expires_in = int(token_data.get("expires_in") or 86400)
        name = open_id
        try:
            user = tt_api.get_user_info(access)
            name = user.get("display_name") or open_id
        except Exception:
            _logger.info("TikTok user info lookup failed; using open_id as name.")
        return access, refresh, expires_in, [{"external_id": open_id, "name": name}]

    @api.model
    def open_page_wizard(self, access, refresh, expires_in, rows):
        wiz = self.env["social.tiktok.link.wizard"].create(
            {
                "access_token": access,
                "refresh_token": refresh,
                "expires_in": expires_in,
                "line_ids": [
                    fields.Command.create({"name": r["name"], "external_id": r["external_id"]})
                    for r in rows
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Confirm TikTok account"),
            "res_model": "social.tiktok.link.wizard",
            "res_id": wiz.id,
            "view_mode": "form",
            "target": "new",
        }


class SocialTiktokLinkWizard(models.TransientModel):
    _name = "social.tiktok.link.wizard"
    _description = "Link TikTok Account"

    access_token = fields.Char(required=True, groups="social.group_social_admin")
    refresh_token = fields.Char(required=True, groups="social.group_social_admin")
    expires_in = fields.Integer()
    line_ids = fields.One2many("social.tiktok.link.wizard.line", "wizard_id", string="Accounts")

    def _link_line(self, line):
        self.ensure_one()
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can link TikTok accounts."))
        if not line or line.wizard_id != self:
            raise UserError(_("Select the account."))
        Account = self.env["social.account"]
        existing = Account.search(
            [
                ("company_id", "=", self.env.company.id),
                ("platform", "=", "tiktok"),
                ("external_account_id", "=", line.external_id),
            ],
            limit=1,
        )
        token_expiry = fields.Datetime.now() + timedelta(seconds=self.expires_in or 86400)
        values = {
            "name": line.name,
            "platform": "tiktok",
            "external_account_id": line.external_id,
            "access_token": self.access_token,
            "tiktok_refresh_token": self.refresh_token,
            "credential_env": False,
            "token_expiry": token_expiry,
            "granted_scopes": tt_api.SCOPES,
            "connection_status": "connected",
            "last_sync_at": fields.Datetime.now(),
            "publishing_enabled": True,
            "messaging_enabled": False,  # TikTok has no public comment/DM API
            "active": True,
            "user_ids": [fields.Command.link(self.env.uid)],
        }
        if existing:
            existing.write(values)
            account = existing
        else:
            values["webhook_key"] = secrets.token_urlsafe(24)[:64]
            account = Account.create(values)
        return {
            "type": "ir.actions.act_window",
            "name": _("Connected"),
            "res_model": "social.account",
            "res_id": account.id,
            "view_mode": "form",
            "target": "current",
        }


class SocialTiktokLinkWizardLine(models.TransientModel):
    _name = "social.tiktok.link.wizard.line"
    _description = "TikTok account choice"

    wizard_id = fields.Many2one("social.tiktok.link.wizard", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    external_id = fields.Char(required=True)

    def action_select(self):
        self.ensure_one()
        return self.wizard_id._link_line(self)

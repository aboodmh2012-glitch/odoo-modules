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

from . import api as li_api

_logger = logging.getLogger(__name__)


class SocialLinkedinOauth(models.TransientModel):
    _name = "social.linkedin.oauth"
    _description = "LinkedIn OAuth Link Helper"

    # ---- server-owned app credentials (operators never enter these) ----------
    @api.model
    def _app_credentials(self):
        ICP = self.env["ir.config_parameter"].sudo()
        client_id = (os.environ.get("SOCIAL_LINKEDIN_CLIENT_ID") or "").strip() or (
            ICP.get_str("social.linkedin_client_id") or ""
        ).strip()
        client_secret = (os.environ.get("SOCIAL_LINKEDIN_CLIENT_SECRET") or "").strip() or (
            ICP.get_str("social.linkedin_client_secret") or ""
        ).strip()
        if not client_id or not client_secret:
            raise UserError(
                _(
                    "LinkedIn is not configured on this server yet.\n\n"
                    "An administrator must set SOCIAL_LINKEDIN_CLIENT_ID and "
                    "SOCIAL_LINKEDIN_CLIENT_SECRET once (LinkedIn Developer app with the "
                    "Community Management API product). After that, Link account opens "
                    "LinkedIn directly — users never enter client id or secret."
                )
            )
        return client_id, client_secret

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
            raise UserError(_("Set web.base.url before linking LinkedIn accounts."))
        return base.rstrip("/") + "/social/linkedin/oauth/callback"

    # ---- signed state (HMAC with client secret, bound to user, 15-min TTL) ----
    @api.model
    def _sign_state(self, payload):
        _cid, secret = self._app_credentials()
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        return f"{sig}.{body}"

    @api.model
    def _parse_state(self, state):
        if not state or "." not in state:
            raise UserError(_("Invalid OAuth state."))
        sig, body = state.split(".", 1)
        _cid, secret = self._app_credentials()
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

    # ---- step 1: open LinkedIn authorization ---------------------------------
    @api.model
    def action_start(self):
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can link LinkedIn accounts."))
        client_id, _secret = self._app_credentials()
        state = self._sign_state(
            {
                "uid": self.env.uid,
                "company_id": self.env.company.id,
                "ts": int(time.time()),
                "nonce": secrets.token_hex(8),
            }
        )
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": self._redirect_uri(),
            "state": state,
            "scope": li_api.SCOPES,
        }
        url = f"{li_api.AUTH_BASE}/authorization?{urlencode(params)}"
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    # ---- step 2: exchange code + list administered organizations --------------
    @api.model
    def exchange_code(self, code):
        client_id, client_secret = self._app_credentials()
        try:
            token_data = li_api.exchange_token(client_id, client_secret, code, self._redirect_uri())
        except Exception as err:
            raise UserError(_("LinkedIn did not return an access token. Try again.")) from err
        token = token_data.get("access_token")
        if not token:
            raise UserError(_("LinkedIn did not return an access token."))
        expires_in = int(token_data.get("expires_in") or 0)
        version = li_api.api_version(self.env)
        rows = self._list_organizations(token, version)
        if not rows:
            raise UserError(
                _(
                    "No LinkedIn organizations where you are an approved ADMINISTRATOR "
                    "were found for this account."
                )
            )
        return token, expires_in, rows

    @api.model
    def _list_organizations(self, token, version):
        try:
            resp = li_api.rest_request(
                "GET",
                "organizationAcls",
                token,
                version,
                params={
                    "q": "roleAssignee",
                    "role": "ADMINISTRATOR",
                    "state": "APPROVED",
                },
            )
            elements = (resp.json() or {}).get("elements") or []
        except Exception as err:
            raise UserError(_("Could not load your LinkedIn organizations. Try again.")) from err
        rows = []
        for el in elements:
            org_urn = el.get("organization") or ""
            org_id = org_urn.rsplit(":", 1)[-1] if org_urn else ""
            if not org_id:
                continue
            name = org_id
            try:
                oresp = li_api.rest_request(
                    "GET", f"organizations/{org_id}", token, version,
                    params={"fields": "id,localizedName,vanityName"},
                )
                odata = oresp.json() or {}
                name = odata.get("localizedName") or odata.get("vanityName") or org_id
            except Exception:
                _logger.info("LinkedIn org name lookup failed for %s", org_id)
            rows.append({"external_id": org_id, "name": name})
        return rows

    @api.model
    def open_page_wizard(self, token, expires_in, rows):
        wiz = self.env["social.linkedin.link.wizard"].create(
            {
                "access_token": token,
                "expires_in": expires_in,
                "line_ids": [
                    fields.Command.create({"name": r["name"], "external_id": r["external_id"]})
                    for r in rows
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Choose a LinkedIn organization"),
            "res_model": "social.linkedin.link.wizard",
            "res_id": wiz.id,
            "view_mode": "form",
            "target": "new",
        }


class SocialLinkedinLinkWizard(models.TransientModel):
    _name = "social.linkedin.link.wizard"
    _description = "Link LinkedIn Organization"

    access_token = fields.Char(required=True, groups="social.group_social_admin")
    expires_in = fields.Integer()
    line_ids = fields.One2many("social.linkedin.link.wizard.line", "wizard_id", string="Organizations")

    def _link_line(self, line):
        self.ensure_one()
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can link LinkedIn accounts."))
        if not line or line.wizard_id != self:
            raise UserError(_("Select an organization."))
        Account = self.env["social.account"]
        existing = Account.search(
            [
                ("company_id", "=", self.env.company.id),
                ("platform", "=", "linkedin"),
                ("external_account_id", "=", line.external_id),
            ],
            limit=1,
        )
        token_expiry = False
        if self.expires_in:
            token_expiry = fields.Datetime.now() + timedelta(seconds=self.expires_in)
        values = {
            "name": line.name,
            "platform": "linkedin",
            "external_account_id": line.external_id,
            "access_token": self.access_token,
            "credential_env": False,
            "token_expiry": token_expiry,
            "granted_scopes": li_api.SCOPES,
            "connection_status": "connected",
            "last_sync_at": fields.Datetime.now(),
            "publishing_enabled": True,
            "messaging_enabled": True,  # comment replies (no DMs on LinkedIn)
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


class SocialLinkedinLinkWizardLine(models.TransientModel):
    _name = "social.linkedin.link.wizard.line"
    _description = "LinkedIn organization choice"

    wizard_id = fields.Many2one("social.linkedin.link.wizard", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    external_id = fields.Char(required=True)

    def action_select(self):
        self.ensure_one()
        return self.wizard_id._link_line(self)

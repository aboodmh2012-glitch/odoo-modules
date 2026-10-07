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

from . import api as yt_api

_logger = logging.getLogger(__name__)


class SocialYoutubeOauth(models.TransientModel):
    _name = "social.youtube.oauth"
    _description = "YouTube OAuth Link Helper"

    @api.model
    def _app_credentials(self):
        ICP = self.env["ir.config_parameter"].sudo()
        client_id = (os.environ.get("SOCIAL_YOUTUBE_CLIENT_ID") or "").strip() or (
            ICP.get_str("social.youtube_client_id") or ""
        ).strip()
        client_secret = (os.environ.get("SOCIAL_YOUTUBE_CLIENT_SECRET") or "").strip() or (
            ICP.get_str("social.youtube_client_secret") or ""
        ).strip()
        if not client_id or not client_secret:
            raise UserError(
                _(
                    "YouTube is not configured on this server yet.\n\n"
                    "An administrator must set SOCIAL_YOUTUBE_CLIENT_ID and "
                    "SOCIAL_YOUTUBE_CLIENT_SECRET once (Google Cloud project with the "
                    "YouTube Data API v3 enabled and an OAuth client). After that, Link "
                    "account opens Google directly — users never enter client id or secret."
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
            raise UserError(_("Set web.base.url before linking YouTube accounts."))
        return base.rstrip("/") + "/social/youtube/oauth/callback"

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

    @api.model
    def action_start(self):
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can link YouTube accounts."))
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
            "scope": yt_api.SCOPES,
            "state": state,
            "access_type": "offline",   # request a refresh token
            "prompt": "consent",        # ensure refresh token is returned on re-link
            "include_granted_scopes": "true",
        }
        url = f"{yt_api.AUTH_URL}?{urlencode(params)}"
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    @api.model
    def exchange_code(self, code):
        client_id, client_secret = self._app_credentials()
        try:
            token_data = yt_api.exchange_token(client_id, client_secret, code, self._redirect_uri())
        except Exception as err:
            raise UserError(_("Google did not return an access token. Try again.")) from err
        access = token_data.get("access_token")
        refresh = token_data.get("refresh_token")
        if not access:
            raise UserError(_("Google did not return an access token."))
        if not refresh:
            raise UserError(
                _(
                    "Google did not return a refresh token. Remove the app's access in your "
                    "Google account, then Link account again to grant offline access."
                )
            )
        expires_in = int(token_data.get("expires_in") or 3600)
        rows = self._list_channels(access)
        if not rows:
            raise UserError(_("No YouTube channel was found for this Google account."))
        return access, refresh, expires_in, rows

    @api.model
    def _list_channels(self, access):
        try:
            resp = yt_api.data_request(
                "GET", "channels", access, params={"part": "snippet", "mine": "true"}
            )
            items = (resp.json() or {}).get("items") or []
        except Exception as err:
            raise UserError(_("Could not load your YouTube channels. Try again.")) from err
        rows = []
        for it in items:
            cid = it.get("id")
            if not cid:
                continue
            title = ((it.get("snippet") or {}).get("title")) or cid
            rows.append({"external_id": cid, "name": title})
        return rows

    @api.model
    def open_page_wizard(self, access, refresh, expires_in, rows):
        wiz = self.env["social.youtube.link.wizard"].create(
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
            "name": _("Choose a YouTube channel"),
            "res_model": "social.youtube.link.wizard",
            "res_id": wiz.id,
            "view_mode": "form",
            "target": "new",
        }


class SocialYoutubeLinkWizard(models.TransientModel):
    _name = "social.youtube.link.wizard"
    _description = "Link YouTube Channel"

    access_token = fields.Char(required=True, groups="social.group_social_admin")
    refresh_token = fields.Char(required=True, groups="social.group_social_admin")
    expires_in = fields.Integer()
    line_ids = fields.One2many("social.youtube.link.wizard.line", "wizard_id", string="Channels")

    def _link_line(self, line):
        self.ensure_one()
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can link YouTube accounts."))
        if not line or line.wizard_id != self:
            raise UserError(_("Select a channel."))
        Account = self.env["social.account"]
        existing = Account.search(
            [
                ("company_id", "=", self.env.company.id),
                ("platform", "=", "youtube"),
                ("external_account_id", "=", line.external_id),
            ],
            limit=1,
        )
        token_expiry = fields.Datetime.now() + timedelta(seconds=self.expires_in or 3600)
        values = {
            "name": line.name,
            "platform": "youtube",
            "external_account_id": line.external_id,
            "access_token": self.access_token,
            "google_refresh_token": self.refresh_token,
            "credential_env": False,
            "token_expiry": token_expiry,
            "granted_scopes": yt_api.SCOPES,
            "connection_status": "connected",
            "last_sync_at": fields.Datetime.now(),
            "publishing_enabled": True,
            "messaging_enabled": True,  # comment replies (no DMs on YouTube)
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


class SocialYoutubeLinkWizardLine(models.TransientModel):
    _name = "social.youtube.link.wizard.line"
    _description = "YouTube channel choice"

    wizard_id = fields.Many2one("social.youtube.link.wizard", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    external_id = fields.Char(required=True)

    def action_select(self):
        self.ensure_one()
        return self.wizard_id._link_line(self)

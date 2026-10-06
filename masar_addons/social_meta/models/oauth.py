# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import hashlib
import hmac
import json
import logging
import secrets
import time
from urllib.parse import urlencode

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

from .account import GRAPH_VERSION
from .app_config import normalize_meta_app_id
from .connectors import facebook_login_params, page_can_publish
from .sdk import (
    build_api,
    graph_call,
    list_user_pages,
    sdk_available,
)
from odoo.addons.social.models.errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain

_logger = logging.getLogger(__name__)

# BrightBean-aligned Page connect set + Messenger (pages_messaging).
FACEBOOK_SCOPES = (
    "pages_show_list,"
    "pages_read_engagement,"
    "pages_manage_posts,"
    "pages_manage_engagement,"
    "pages_manage_metadata,"
    "pages_messaging,"
    "read_insights,"
    "business_management"
)
INSTAGRAM_SCOPES = (
    FACEBOOK_SCOPES
    + ",instagram_basic,instagram_content_publish,instagram_manage_comments,pages_read_user_content"
)


class SocialMetaOauth(models.TransientModel):
    _name = "social.meta.oauth"
    _description = "Meta OAuth Link Helper"

    @api.model
    def _credentials_configured(self):
        try:
            self._app_credentials()
            return True
        except UserError:
            return False

    @api.model
    def _app_credentials(self):
        """Meta app owned by the server (Zoho-style) — never asked from operators.

        Prefer Railway / process env, then optional ICP set by a system admin.
        """
        import os

        ICP = self.env["ir.config_parameter"].sudo()
        app_id = normalize_meta_app_id(os.environ.get("SOCIAL_META_APP_ID") or "") or normalize_meta_app_id(
            ICP.get_param("social.meta_app_id") or ""
        )
        app_secret = (os.environ.get("SOCIAL_META_APP_SECRET") or "").strip() or (
            ICP.get_param("social.meta_app_secret") or ""
        ).strip()
        if not app_id or not app_secret:
            raise UserError(
                _(
                    "Facebook Login is not ready on this server yet.\n\n"
                    "An administrator must set SOCIAL_META_APP_ID and SOCIAL_META_APP_SECRET "
                    "once in Railway (Meta → Settings → Basic). After that, Link account "
                    "opens Facebook directly — users never enter App ID or Secret."
                )
            )
        if len(app_id) < 6:
            raise UserError(
                _(
                    "SOCIAL_META_APP_ID on the server is invalid. It must be the numeric "
                    "App ID from Meta → Settings → Basic (not the app name)."
                )
            )
        return app_id, app_secret

    @api.model
    def _redirect_uri(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        if not base:
            raise UserError(_("Set web.base.url before linking Meta accounts."))
        return base.rstrip("/") + "/social/meta/oauth/callback"

    @api.model
    def _sign_state(self, payload):
        app_id, app_secret = self._app_credentials()
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        sig = hmac.new(app_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        return f"{sig}.{body}"

    @api.model
    def _parse_state(self, state):
        if not state or "." not in state:
            raise UserError(_("Invalid OAuth state."))
        sig, body = state.split(".", 1)
        _app_id, app_secret = self._app_credentials()
        expected = hmac.new(app_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
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
    def action_start(self, media_type):
        """Open Facebook Login; first time only, ask admin for App ID/Secret once."""
        if media_type not in ("facebook", "instagram"):
            raise UserError(_("Unsupported Meta platform."))
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can link Meta accounts."))
        if not self._credentials_configured():
            return self.env["social.meta.app.config"].action_open(media_type)
        app_id, _secret = self._app_credentials()
        state = self._sign_state(
            {
                "uid": self.env.uid,
                "company_id": self.env.company.id,
                "media_type": media_type,
                "ts": int(time.time()),
                "nonce": secrets.token_hex(8),
            }
        )
        import os

        ICP = self.env["ir.config_parameter"].sudo()
        config_id = (os.environ.get("SOCIAL_META_CONFIG_ID") or "").strip() or (
            ICP.get_param("social.meta_config_id") or ""
        ).strip()
        scopes = INSTAGRAM_SCOPES if media_type == "instagram" else FACEBOOK_SCOPES
        params = facebook_login_params(
            client_id=app_id,
            redirect_uri=self._redirect_uri(),
            state=state,
            scopes=scopes,
            config_id=config_id,
        )
        url = f"https://www.facebook.com/{GRAPH_VERSION}/dialog/oauth?{urlencode(params)}"
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    @api.model
    def _sdk_api(self, access_token=""):
        if not sdk_available():
            raise UserError(
                _(
                    "The Meta Facebook Business SDK (facebook-business) is not installed. "
                    "Install facebook-business==26.0.0 on the server."
                )
            )
        app_id, app_secret = self._app_credentials()
        return build_api(app_id, app_secret, access_token or "", api_version=GRAPH_VERSION)

    @api.model
    def _graph_get(self, path, params, access_token=""):
        """OAuth Graph helper via official Business SDK (no raw requests)."""
        api = self._sdk_api(access_token=access_token or params.get("access_token") or "")
        query = {k: v for k, v in (params or {}).items() if k != "access_token"}
        try:
            return graph_call(api, "GET", path, params=query)
        except (DeliveryTemporary, DeliveryPermanent, DeliveryUncertain) as err:
            _logger.warning("Meta OAuth Graph call failed for %s", path)
            raise UserError(_("Could not reach Meta Graph API. Try again.")) from err

    @api.model
    def exchange_code(self, code, media_type):
        app_id, app_secret = self._app_credentials()
        redirect_uri = self._redirect_uri()
        short = self._graph_get(
            "oauth/access_token",
            {
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        user_token = short.get("access_token")
        if not user_token:
            raise UserError(_("Meta did not return an access token."))
        long_lived = self._graph_get(
            "oauth/access_token",
            {
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": user_token,
            },
        )
        long_token = long_lived.get("access_token") or user_token
        api = self._sdk_api(access_token=long_token)
        try:
            pages = list_user_pages(api)
        except (DeliveryTemporary, DeliveryPermanent, DeliveryUncertain) as err:
            raise UserError(_("Could not load Facebook Pages from Meta. Try again.")) from err
        rows = []
        skipped_no_publish = 0
        for page in pages:
            page_token = page.get("access_token")
            if not page.get("id") or not page_token:
                continue
            if media_type == "facebook" and not page_can_publish(page):
                skipped_no_publish += 1
                continue
            if media_type == "facebook":
                rows.append(
                    {
                        "external_id": page["id"],
                        "name": page.get("name") or page["id"],
                        "access_token": page_token,
                        "page_id": page["id"],
                    }
                )
            else:
                ig = page.get("instagram_business_account") or {}
                if not ig.get("id"):
                    continue
                rows.append(
                    {
                        "external_id": ig["id"],
                        "name": ig.get("username") or ig.get("name") or page.get("name") or ig["id"],
                        "access_token": page_token,
                        "page_id": page["id"],
                    }
                )
        if skipped_no_publish:
            _logger.info(
                "Meta OAuth skipped %s Page(s) without CREATE_CONTENT task",
                skipped_no_publish,
            )
        if not rows:
            if media_type == "instagram":
                raise UserError(
                    _("No Instagram Business account linked to your Facebook Pages was found.")
                )
            if skipped_no_publish:
                raise UserError(
                    _(
                        "No Facebook Pages with publish permission (CREATE_CONTENT) "
                        "were returned for this user."
                    )
                )
            raise UserError(_("No Facebook Pages were returned for this user."))
        return rows

    @api.model
    def open_page_wizard(self, media_type, rows):
        wiz = self.env["social.meta.link.wizard"].create(
            {
                "media_type": media_type,
                "line_ids": [
                    fields.Command.create(
                        {
                            "name": row["name"],
                            "external_id": row["external_id"],
                            "page_id": row.get("page_id"),
                            "access_token": row["access_token"],
                        }
                    )
                    for row in rows
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Choose a Facebook Page") if media_type == "facebook" else _("Choose an Instagram account"),
            "res_model": "social.meta.link.wizard",
            "res_id": wiz.id,
            "view_mode": "form",
            "target": "new",
        }


class SocialMetaLinkWizard(models.TransientModel):
    _name = "social.meta.link.wizard"
    _description = "Link Meta Social Account"

    media_type = fields.Selection(
        [("facebook", "Facebook"), ("instagram", "Instagram")],
        required=True,
    )
    line_ids = fields.One2many("social.meta.link.wizard.line", "wizard_id", string="Accounts")
    hint = fields.Char(compute="_compute_hint")

    @api.depends("media_type")
    def _compute_hint(self):
        for wiz in self:
            if wiz.media_type == "instagram":
                wiz.hint = _("Pick the Instagram Business account to connect. Name and token are filled automatically.")
            else:
                wiz.hint = _("Pick the Facebook Page to connect. Name and token are filled automatically.")

    def _link_line(self, line):
        """Create/update social.account from a chosen Page / IG row (Zoho-style)."""
        self.ensure_one()
        if not self.env.user.has_group("social.group_social_admin"):
            raise AccessError(_("Only Social Connection Administrators can link Meta accounts."))
        if not line or line.wizard_id != self:
            raise UserError(_("Select a Page or Instagram account."))
        Account = self.env["social.account"]
        existing = Account.search(
            [
                ("company_id", "=", self.env.company.id),
                ("platform", "=", self.media_type),
                ("external_account_id", "=", line.external_id),
            ],
            limit=1,
        )
        scopes = INSTAGRAM_SCOPES if self.media_type == "instagram" else FACEBOOK_SCOPES
        values = {
            "name": line.name,
            "platform": self.media_type,
            "external_account_id": line.external_id,
            "meta_page_id": line.page_id or (line.external_id if self.media_type == "facebook" else False),
            "access_token": line.access_token,
            "credential_env": False,
            "token_expiry": False,
            "granted_scopes": scopes,
            "connection_status": "connected",
            "last_sync_at": fields.Datetime.now(),
            "publishing_enabled": True,
            "messaging_enabled": True,
            "active": True,
            "user_ids": [fields.Command.link(self.env.uid)],
        }
        import os

        if os.environ.get("SOCIAL_META_APP_SECRET"):
            values["meta_app_secret_env"] = "SOCIAL_META_APP_SECRET"
        if existing:
            existing.write(values)
            account = existing
        else:
            values["webhook_key"] = secrets.token_urlsafe(24)[:64]
            account = Account.create(values)
        try:
            account._meta_subscribe_webhooks()
        except Exception:
            _logger.warning(
                "Meta subscribed_apps failed for account %s; configure webhooks in Meta App Dashboard.",
                account.id,
                exc_info=True,
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Connected"),
            "res_model": "social.account",
            "res_id": account.id,
            "view_mode": "form",
            "target": "current",
        }


class SocialMetaLinkWizardLine(models.TransientModel):
    _name = "social.meta.link.wizard.line"
    _description = "Meta account choice"

    wizard_id = fields.Many2one("social.meta.link.wizard", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    external_id = fields.Char(required=True)
    page_id = fields.Char()
    access_token = fields.Char(required=True)

    def action_select(self):
        """One click — like Zoho “Add” on a Page row."""
        self.ensure_one()
        return self.wizard_id._link_line(self)

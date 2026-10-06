# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later.
import hashlib
import hmac
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .connectors import (
    FACEBOOK_WEBHOOK_FIELDS,
    INSTAGRAM_WEBHOOK_FIELDS,
    build_send_payload,
)
from .sdk import (
    GRAPH_BASE,
    GRAPH_VERSION,
    build_api,
    comment_create,
    debug_token,
    graph_call,
    page_create_feed,
    page_create_photo,
    page_create_video,
    sdk_available,
    subscribe_apps,
)

_logger = logging.getLogger(__name__)

# Re-export for oauth / connectors that import from this module.
__all__ = ["GRAPH_BASE", "GRAPH_VERSION", "SocialAccount"]


class SocialAccount(models.Model):
    _inherit = "social.account"

    meta_app_secret_env = fields.Char(
        string="Meta app secret environment variable",
        groups="social.group_social_admin",
        copy=False,
        help="SOCIAL_… env var holding the Meta App Secret for X-Hub-Signature-256 verification.",
    )
    meta_page_id = fields.Char(
        string="Meta Page ID",
        groups="social.group_social_admin",
        copy=False,
        index=True,
        help="Facebook Page ID. For Instagram Business this is the linked Page "
        "(external_account_id remains the IG user id).",
    )

    @api.constrains("meta_app_secret_env")
    def _check_meta_app_secret_ref(self):
        for rec in self:
            if rec.meta_app_secret_env and not re.fullmatch(r"SOCIAL_[A-Z0-9_]+", rec.meta_app_secret_env):
                raise ValidationError(_("Use a SOCIAL_ prefixed environment variable name, not a secret."))

    def _verify_meta_signature(self, raw_body, header_value):
        self.ensure_one()
        if not self.meta_app_secret_env:
            raise UserError(_("Meta app secret environment variable is not set on the account."))
        secret = self._secret("meta_app_secret_env")
        if not header_value or not header_value.startswith("sha256="):
            return False
        expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        supplied = header_value.split("=", 1)[1]
        return hmac.compare_digest(expected, supplied)

    def _meta_app_credentials(self):
        """App ID / Secret from server env first (operators never enter these)."""
        import os

        ICP = self.env["ir.config_parameter"].sudo()
        app_id = (os.environ.get("SOCIAL_META_APP_ID") or "").strip() or (
            ICP.get_param("social.meta_app_id") or ""
        ).strip()
        app_secret = (os.environ.get("SOCIAL_META_APP_SECRET") or "").strip() or (
            ICP.get_param("social.meta_app_secret") or ""
        ).strip()
        return app_id, app_secret

    def _meta_facebook_api(self, access_token=None):
        """Official Facebook Business SDK client for this Page / token."""
        if not sdk_available():
            raise UserError(
                _(
                    "The Meta Facebook Business SDK (facebook-business) is not installed on the server. "
                    "Install package facebook-business==26.0.0 and restart Odoo."
                )
            )
        self.ensure_one()
        app_id, app_secret = self._meta_app_credentials()
        token = access_token if access_token is not None else self._secret()
        return build_api(app_id, app_secret, token, api_version=GRAPH_VERSION)

    def _meta_graph_request(self, method, path, data=None, files=None, params=None, timeout=(10, 45)):
        """Shared Graph call via Meta Business SDK. Token never appears in raised text.

        ``timeout`` is accepted for API compatibility with callers; the SDK session
        uses its own HTTP defaults.
        """
        del timeout  # SDK session timeout is configured at FacebookSession level.
        api = self._meta_facebook_api()
        query = dict(params or {})
        if data:
            query.update(data)
        return graph_call(api, method, path, params=query, files=files)

    def _meta_page_publish_text(self, message):
        self.ensure_one()
        page_id = self.meta_page_id or self.external_account_id
        return page_create_feed(self._meta_facebook_api(), page_id, message)

    def _meta_page_publish_photo(self, caption, raw_bytes, filename, mimetype):
        self.ensure_one()
        page_id = self.meta_page_id or self.external_account_id
        return page_create_photo(
            self._meta_facebook_api(),
            page_id,
            caption,
            raw_bytes,
            filename=filename,
            mimetype=mimetype,
        )

    def _meta_page_publish_video(self, description, raw_bytes, filename, mimetype):
        self.ensure_one()
        page_id = self.meta_page_id or self.external_account_id
        return page_create_video(
            self._meta_facebook_api(),
            page_id,
            description,
            raw_bytes,
            filename=filename,
            mimetype=mimetype,
        )

    def _meta_page_comment(self, object_id, message):
        self.ensure_one()
        return comment_create(self._meta_facebook_api(), object_id, message)

    def _meta_subscribe_webhooks(self):
        """POST subscribed_apps after OAuth link (BrightBean facebook/instagram pattern)."""
        self.ensure_one()
        if self.platform == "facebook":
            object_id = self.meta_page_id or self.external_account_id
            fields = FACEBOOK_WEBHOOK_FIELDS
        elif self.platform == "instagram":
            # IG webhooks attach to the IG user id, not the Page.
            object_id = self.external_account_id
            fields = INSTAGRAM_WEBHOOK_FIELDS
        else:
            return False
        if not object_id:
            return False
        result = subscribe_apps(self._meta_facebook_api(), object_id, fields)
        ok = bool(result.get("success")) if isinstance(result, dict) else bool(result)
        if ok:
            _logger.info(
                "Meta subscribed_apps ok for %s account %s fields=%s",
                self.platform,
                self.id,
                ",".join(fields),
            )
        return ok

    def _meta_send_message(self, recipient_id, text, *, human_agent=False):
        """Messenger Send API via Page (BrightBean meta_messaging payload)."""
        self.ensure_one()
        page_id = self.meta_page_id or self.external_account_id
        if not recipient_id or not text:
            raise UserError(_("Missing recipient or message text."))
        payload = build_send_payload(recipient_id, text, human_agent=human_agent)
        return self._meta_graph_request("POST", f"{page_id}/messages", data=payload)

    @api.model
    def _cron_meta_check_tokens(self):
        """Scheduled re-validation of linked Meta tokens.

        Long-lived Page tokens can still be revoked (admin removed, app moved to
        dev mode, password reset). This proactively flags dead/expiring tokens so
        an admin re-links, instead of discovering it only on a failed publish.
        Each account is isolated: one failure never aborts the batch.
        """
        app_id, app_secret = self._meta_app_credentials()
        if not app_id or not app_secret:
            return
        accounts = self.sudo().search(
            [
                ("platform", "in", ("facebook", "instagram")),
                ("connection_status", "=", "connected"),
                ("active", "=", True),
            ]
        )
        for account in accounts:
            try:
                token = account._secret()
            except UserError:
                continue
            try:
                data = debug_token(account._meta_facebook_api(), token, app_id, app_secret)
            except Exception:
                # Transient Graph/SDK error — leave status unchanged, try next run.
                _logger.info("Meta token re-check skipped for account %s (transient).", account.id)
                continue
            info = (data or {}).get("data") or {}
            vals = {"last_sync_at": fields.Datetime.now()}
            if info.get("is_valid") is False:
                vals["connection_status"] = "error"
                account.message_post(
                    body=_(
                        "Meta access token is no longer valid. Re-link this account "
                        "(Reconnect) to restore publishing and messaging."
                    ),
                    subtype_xmlid="mail.mt_note",
                )
            account.sudo().write(vals)

    def action_meta_check_token(self):
        """Admin action: inspect Page token via /debug_token."""
        self.ensure_one()
        if not self.env.user.has_group("social.group_social_admin"):
            raise UserError(_("Only Social Connection Administrators can check Meta tokens."))
        app_id, app_secret = self._meta_app_credentials()
        if not app_id or not app_secret:
            raise UserError(_("Meta App ID/Secret are not configured on the server."))
        data = debug_token(self._meta_facebook_api(), self._secret(), app_id, app_secret)
        info = (data or {}).get("data") or {}
        scopes = info.get("scopes") or info.get("granular_scopes") or []
        if isinstance(scopes, list) and scopes and isinstance(scopes[0], dict):
            scopes = [s.get("permission") or s.get("scope") for s in scopes if s]
        scope_str = ",".join(str(s) for s in scopes if s)
        vals = {"last_sync_at": fields.Datetime.now()}
        if scope_str:
            vals["granted_scopes"] = scope_str
        if info.get("is_valid") is False:
            vals["connection_status"] = "error"
        elif info.get("is_valid") is True:
            vals["connection_status"] = "connected"
        self.sudo().write(vals)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Meta token"),
                "message": _(
                    "Valid: %(valid)s — type: %(ttype)s — scopes: %(scopes)s",
                    valid=info.get("is_valid"),
                    ttype=info.get("type") or info.get("application") or "?",
                    scopes=scope_str or _("(none returned)"),
                ),
                "sticky": False,
                "type": "success" if info.get("is_valid") else "warning",
            },
        }

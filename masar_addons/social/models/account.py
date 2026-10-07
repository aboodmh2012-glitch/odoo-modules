import os
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class SocialAccount(models.Model):
    _name = "social.account"
    _description = "Social Account"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.company, index=True)
    platform = fields.Selection([("unconfigured", "Not configured")], required=True, default="unconfigured")
    external_account_id = fields.Char(required=True, index=True)
    user_ids = fields.Many2many("res.users", string="Account members", domain=[("share", "=", False)])
    active = fields.Boolean(default=True)
    publishing_enabled = fields.Boolean(default=False, tracking=True)
    messaging_enabled = fields.Boolean(default=False, tracking=True)
    credential_env = fields.Char(string="Token environment variable", groups="social.group_social_admin", copy=False)
    access_token = fields.Char(
        string="Access token",
        groups="social.group_social_admin",
        copy=False,
        help="Page access token from OAuth. Never shown to operators; used only by connectors.",
    )
    token_expiry = fields.Datetime(
        string="Token expiry",
        groups="social.group_social_admin",
        copy=False,
        help="Empty means a long-lived Page token (no fixed Meta expiry).",
    )
    granted_scopes = fields.Char(
        string="Granted permissions",
        groups="social.group_social_admin",
        copy=False,
        readonly=True,
    )
    connection_status = fields.Selection(
        [
            ("not_connected", "Not connected"),
            ("connected", "Connected"),
            ("error", "Error"),
        ],
        default="not_connected",
        required=True,
        tracking=True,
        index=True,
    )
    last_sync_at = fields.Datetime(string="Last sync", readonly=True, copy=False)
    webhook_secret_env = fields.Char(string="Webhook secret environment variable", groups="social.group_social_admin", copy=False)
    webhook_key = fields.Char(groups="social.group_social_admin", copy=False)
    webhook_user_id = fields.Many2one(
        "res.users",
        string="Webhook operator",
        groups="social.group_social_admin",
        domain=[("share", "=", False)],
        help="Internal user used to process verified inbound webhook jobs.",
    )
    _external_unique = models.Constraint("UNIQUE(company_id, platform, external_account_id)", "This account already exists in the company.")
    _webhook_unique = models.Constraint("UNIQUE(webhook_key)", "Webhook route key must be unique.")

    @api.constrains("user_ids", "company_id")
    def _check_members(self):
        for account in self:
            if any(account.company_id not in user.company_ids for user in account.user_ids):
                raise ValidationError(_("Account members must have access to its company."))

    @api.constrains("credential_env", "webhook_secret_env", "webhook_key")
    def _check_secret_refs(self):
        for rec in self:
            for value in (rec.credential_env, rec.webhook_secret_env):
                if value and not re.fullmatch(r"SOCIAL_[A-Z0-9_]+", value):
                    raise ValidationError(_("Use a SOCIAL_ prefixed environment variable name, not a token."))
            if rec.webhook_key and not re.fullmatch(r"[a-zA-Z0-9_-]{24,100}", rec.webhook_key):
                raise ValidationError(_("Use a random webhook route key of 24–100 letters, digits, underscores or hyphens."))

    def _assert_operate(self, capability=None):
        self.ensure_one()
        self.check_access("read")
        if not self.env.user.has_group("social.group_social_user"):
            raise AccessError(_("Social operator access is required."))
        if self.company_id not in self.env.companies or not self.active:
            raise AccessError(_("Account is inactive or outside the current companies."))
        if not self.env.user.has_group("social.group_social_manager") and self.env.user not in self.user_ids:
            raise AccessError(_("You are not a member of this account."))
        if capability and not self[capability + "_enabled"]:
            raise UserError(_("This account does not enable the requested operation."))

    def _secret(self, field="credential_env"):
        # Narrow technical sudo: return only a referenced environment secret to
        # a private provider method, never to RPC, views or job arguments.
        # Linked Meta accounts may store a page token from OAuth instead of an env ref.
        self.ensure_one()
        sudo_rec = self.sudo()
        if field == "credential_env" and sudo_rec.access_token:
            return sudo_rec.access_token
        ref = sudo_rec[field]
        value = os.environ.get(ref or "")
        if not value:
            raise UserError(_("The account credential is not configured on the server."))
        return value

    def _validate_target(self, target):
        raise UserError(_("Install and configure a publishing connector first."))

    def _publish_target(self, target):
        raise UserError(_("This platform does not support publishing."))

    def _send_reply(self, conversation, text):
        raise UserError(_("This platform does not support replies."))

    def action_connect_provider(self, *args, **kwargs):
        """Reconnect this account through its provider OAuth flow."""
        del args, kwargs
        self.ensure_one()
        if self.platform in ("facebook", "instagram") and "social.meta.oauth" in self.env:
            return self.env["social.meta.oauth"].action_start(self.platform)
        raise UserError(_("Install and configure the connector for platform “%s” first.") % self.platform)

    def action_connect_facebook(self, *args, **kwargs):
        """Start Facebook OAuth directly."""
        del args, kwargs
        self.env["social.account"].check_access("create")
        if "social.meta.oauth" not in self.env:
            raise UserError(_("Install Social · Meta first."))
        return self.env["social.meta.oauth"].action_start("facebook")

    def action_connect_instagram(self, *args, **kwargs):
        """Start Instagram OAuth directly."""
        del args, kwargs
        self.env["social.account"].check_access("create")
        if "social.meta.oauth" not in self.env:
            raise UserError(_("Install Social · Meta first."))
        return self.env["social.meta.oauth"].action_start("instagram")



class SocialProfile(models.Model):
    _name = "social.profile"
    _description = "Social Connection"
    _rec_name = "name"
    _check_company_auto = True

    account_id = fields.Many2one("social.account", required=True, ondelete="restrict", check_company=True, index=True)
    company_id = fields.Many2one(related="account_id.company_id", store=True, index=True)
    platform = fields.Selection(related="account_id.platform", store=True)
    external_profile_id = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    username = fields.Char()
    partner_id = fields.Many2one("res.partner", check_company=True)
    last_seen_at = fields.Datetime()
    active = fields.Boolean(default=True)
    _identity_unique = models.Constraint("UNIQUE(account_id, external_profile_id)", "This identity already exists for this account.")

    def write(self, vals):
        if {"account_id", "external_profile_id", "company_id", "platform"}.intersection(vals):
            raise AccessError(_("Social identity identifiers cannot be changed."))
        return super().write(vals)

    def action_create_contact(self):
        self.ensure_one()
        self.check_access("write")
        self.account_id._assert_operate()
        self.env.cr.execute("SELECT id FROM social_profile WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset()
        if not self.partner_id:
            self.partner_id = self.env["res.partner"].create({"name": self.name, "company_id": self.company_id.id})
        return {"type": "ir.actions.act_window", "res_model": "res.partner", "res_id": self.partner_id.id, "view_mode": "form"}

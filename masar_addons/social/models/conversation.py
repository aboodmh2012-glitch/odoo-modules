import hashlib

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.queue_job.exception import RetryableJobError

from .attempt import deliver
from .errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain


class SocialConversation(models.Model):
    _name = "social.conversation"
    _description = "Social Inbox"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _order = "last_message_at desc, id desc"

    name = fields.Char(required=True)
    account_id = fields.Many2one("social.account", required=True, ondelete="restrict", check_company=True, index=True)
    company_id = fields.Many2one(related="account_id.company_id", store=True, index=True)
    platform = fields.Selection(related="account_id.platform", store=True, index=True)
    profile_id = fields.Many2one("social.profile", check_company=True, ondelete="restrict")
    partner_id = fields.Many2one(related="profile_id.partner_id", readonly=True)
    external_conversation_id = fields.Char(required=True, index=True)
    kind = fields.Selection([("private", "Private message"), ("comment", "Public comment"), ("mention", "Mention"), ("review", "Review")], required=True, default="private")
    state = fields.Selection([("open", "Open"), ("waiting", "Waiting for customer"), ("done", "Done")], default="open", required=True, tracking=True, index=True)
    priority = fields.Selection(
        [("0", "Low"), ("1", "Medium"), ("2", "High")],
        default="0",
        required=True,
        tracking=True,
        index=True,
    )
    assigned_user_id = fields.Many2one("res.users", tracking=True)
    important = fields.Boolean()
    spam = fields.Boolean()
    needs_reply = fields.Boolean(default=False, readonly=True)
    last_message_at = fields.Datetime(readonly=True, index=True)
    preview = fields.Char(readonly=True)
    external_url = fields.Char()
    delivery_ids = fields.One2many("social.delivery", "conversation_id", readonly=True)
    reply_text = fields.Text(string="External reply draft", copy=False)
    _conversation_unique = models.Constraint("UNIQUE(account_id, external_conversation_id, kind)", "Conversation already exists.")

    KIND_LABELS = {
        "private": "MESSAGE",
        "comment": "COMMENT",
        "mention": "MENTION",
        "review": "REVIEW",
    }

    def _kind_label(self):
        self.ensure_one()
        return self.KIND_LABELS.get(self.kind, (self.kind or "").upper())

    @api.constrains("account_id", "profile_id", "assigned_user_id")
    def _check_links(self):
        for rec in self:
            if rec.profile_id and rec.profile_id.account_id != rec.account_id:
                raise ValidationError(_("Profile must belong to the conversation account."))
            if rec.assigned_user_id:
                if rec.company_id not in rec.assigned_user_id.company_ids:
                    raise ValidationError(_("Assignee must have company access."))
                if rec.assigned_user_id not in rec.account_id.user_ids:
                    raise ValidationError(_("Add the assignee to the account members first."))

    @api.model_create_multi
    def create(self, vals_list):
        raise AccessError(_("Conversations are created by inbound connectors."))

    def write(self, vals):
        if {
            "account_id",
            "external_conversation_id",
            "company_id",
            "kind",
            "profile_id",
            "needs_reply",
            "last_message_at",
            "preview",
            "platform",
            "delivery_ids",
        }.intersection(vals):
            raise AccessError(_("Transport identifiers and delivery state are system managed."))
        for rec in self:
            rec.account_id._assert_operate()
            if rec.assigned_user_id and rec.assigned_user_id != self.env.user and not self.env.user.has_group("social.group_social_manager"):
                raise AccessError(_("Only the assignee or a Social manager may change this conversation."))
        return super().write(vals)

    @api.model
    def _inbox_platforms(self):
        """Platform chips derived from real linked accounts only."""
        accounts = self.env["social.account"].sudo().search([
            ("active", "=", True),
            ("connection_status", "=", "connected"),
            ("platform", "!=", "unconfigured"),
        ])
        platforms = sorted(set(accounts.mapped("platform")))
        return [
            {
                "name": platform.replace("_", " ").title(),
                "media_type": platform,
                "image_url": f"/social/static/src/img/{platform}.svg",
                "sequence": index,
            }
            for index, platform in enumerate(platforms)
        ]

    def action_assign_me(self):
        self.write({"assigned_user_id": self.env.uid})

    def action_done(self):
        self.write({"state": "done"})

    def action_send_reply(self):
        self.ensure_one()
        self.check_access("write")
        self.account_id._assert_operate("messaging")
        self.env.cr.execute("SELECT id FROM social_conversation WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset()
        if self.spam:
            raise UserError(_("Remove the spam flag before replying."))
        if self.assigned_user_id != self.env.user and not self.env.user.has_group("social.group_social_manager"):
            raise AccessError(_("Assign the conversation before replying."))
        if not (self.reply_text or "").strip():
            raise UserError(_("Write a reply first."))
        # Outgoing body is stored exactly once in mail.message; delivery only
        # records provider transport metadata. Internal notes do not send.
        message = self.message_post(body=self.reply_text, subtype_xmlid="mail.mt_note")
        delivery = self.env["social.delivery"]._create_transport({"conversation_id": self.id, "mail_message_id": message.id, "direction": "outgoing", "state": "queued", "sender_id": self.env.uid, "body_digest": hashlib.sha256(str(message.body).encode()).hexdigest()})
        self.write({"reply_text": False})
        delivery.with_delay(identity_key=f"social-reply-{delivery.id}", max_retries=5, description=f"Social reply {delivery.id}")._job_send()

    @api.model
    def _receive(self, account, external_id, thread_id, profile_id, name, text, occurred_at=None, kind="private"):
        """Private, called only by a verified connector as a limited operator.

        Lock account to serialize duplicate events and profile/conversation
        creation. External IDs are scoped by account, never globally.
        ``kind`` selects private inbox vs public monitor threads (comment/mention).
        """
        if kind not in dict(self._fields["kind"].selection):
            kind = "private"
        account._assert_operate("messaging")
        self.env.cr.execute("SELECT id FROM social_account WHERE id = %s FOR UPDATE", [account.id])
        existing = self.env["social.delivery"].search([("account_id", "=", account.id), ("external_id", "=", str(external_id)), ("direction", "=", "incoming")], limit=1)
        if existing:
            return existing.conversation_id
        profile = self.env["social.profile"].search([("account_id", "=", account.id), ("external_profile_id", "=", str(profile_id))], limit=1)
        if not profile:
            profile = self.env["social.profile"].create({"account_id": account.id, "external_profile_id": str(profile_id), "name": name})
        profile.last_seen_at = occurred_at or fields.Datetime.now()
        conversation = self.search([("account_id", "=", account.id), ("external_conversation_id", "=", str(thread_id)), ("kind", "=", kind)], limit=1)
        if not conversation:
            conversation = super(SocialConversation, self).create({"name": name, "account_id": account.id, "profile_id": profile.id, "external_conversation_id": str(thread_id), "kind": kind})
        message = conversation.message_post(body=text, subtype_xmlid="mail.mt_note")
        self.env["social.delivery"]._create_transport({"conversation_id": conversation.id, "mail_message_id": message.id, "direction": "incoming", "external_id": str(external_id), "state": "received"})
        snippet = (text or "").strip().replace("\n", " ")
        if len(snippet) > 240:
            snippet = snippet[:237] + "..."
        super(SocialConversation, conversation).write({
            "last_message_at": occurred_at or fields.Datetime.now(),
            "needs_reply": True,
            "state": "open",
            "preview": snippet,
        })
        return conversation


class SocialDelivery(models.Model):
    _name = "social.delivery"
    _description = "Social Message Transport"
    _check_company_auto = True
    _order = "id desc"

    conversation_id = fields.Many2one("social.conversation", required=True, ondelete="cascade", check_company=True)
    company_id = fields.Many2one(related="conversation_id.company_id", store=True, index=True)
    account_id = fields.Many2one(related="conversation_id.account_id", store=True, index=True)
    mail_message_id = fields.Many2one("mail.message", required=True, ondelete="restrict")
    direction = fields.Selection([("incoming", "Incoming"), ("outgoing", "Outgoing")], required=True)
    external_id = fields.Char(index=True)
    sender_id = fields.Many2one("res.users")
    state = fields.Selection([(s, s.title()) for s in ["received", "queued", "sending", "sent", "failed", "uncertain"]], required=True)
    error_message = fields.Char()
    sent_at = fields.Datetime()
    body_digest = fields.Char()
    _external_unique = models.Constraint("UNIQUE(account_id, direction, external_id)", "Message already processed.")

    @api.model_create_multi
    def create(self, vals_list):
        raise AccessError(_("Messages must be received or sent through the connector."))

    @api.model
    def _create_transport(self, vals):
        return super().create(vals)

    def write(self, vals):
        raise AccessError(_("Delivery records are read-only."))

    def unlink(self):
        raise AccessError(_("Delivery records are retained for audit."))

    def _set_transport(self, vals):
        return super().write(vals)

    def _job_send(self):
        self.ensure_one()
        conversation = self.conversation_id
        conversation.check_access("write")
        self.env.cr.execute("SELECT id FROM social_account WHERE id = %s FOR UPDATE", [conversation.account_id.id])
        self.env.cr.execute("SELECT id FROM social_delivery WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset()
        if self.state != "queued":
            return
        try:
            conversation.account_id._assert_operate("messaging")
            if self.body_digest != hashlib.sha256(str(self.mail_message_id.body).encode()).hexdigest():
                raise UserError(_("Queued message content was modified."))
            if not self.env.user.active or (conversation.assigned_user_id != self.env.user and not self.env.user.has_group("social.group_social_manager")):
                raise AccessError(_("Reply assignment changed."))
        except (AccessError, UserError):
            self._set_transport({"state": "failed", "error_message": _("Access or assignment changed.")})
            return
        from odoo.tools import html2plaintext
        body = html2plaintext(self.mail_message_id.body)
        self._set_transport({"state": "sending"})
        try:
            result = deliver(self, lambda: conversation.account_id._send_reply(conversation, body))
        except DeliveryTemporary as error:
            self._set_transport({"state": "queued"})
            raise RetryableJobError("Social provider temporarily unavailable", seconds=error.args[0] if error.args else 60)
        except DeliveryPermanent:
            self._set_transport({"state": "failed", "error_message": _("Provider rejected the reply.")})
            return
        except DeliveryUncertain:
            self._set_transport({"state": "uncertain", "error_message": _("Unknown outcome; inspect the platform before resending.")})
            return
        self._set_transport({"state": "sent", "external_id": str(result["id"]), "sent_at": fields.Datetime.now()})
        # Preserve needs_reply if a newer incoming message arrived meanwhile.
        newest = self.search([("conversation_id", "=", conversation.id)], order="id desc", limit=1)
        if newest == self:
            super(SocialConversation, conversation).write({"needs_reply": False, "state": "waiting"})

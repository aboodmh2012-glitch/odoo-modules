import hashlib
import json
from uuid import uuid4

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.queue_job.exception import RetryableJobError

from .attempt import deliver, assert_unpublished, reset_rejected_checkpoint
from .errors import DeliveryPermanent, DeliveryTemporary, DeliveryUncertain


class SocialPost(models.Model):
    _name = "social.post"
    _description = "Social Post"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _check_company_auto = True
    _tier_validation_manual_config = False
    _state_from = ["draft", "review"]
    _state_to = ["approved"]
    _cancel_state = "cancelled"

    name = fields.Char(required=True, tracking=True)
    content = fields.Text(required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda s: s.env.company, index=True)
    author_id = fields.Many2one("res.users", required=True, default=lambda s: s.env.user, readonly=True)
    campaign_id = fields.Many2one("utm.campaign")
    state = fields.Selection([("draft", "Draft"), ("review", "In review"), ("approved", "Approved"), ("cancelled", "Cancelled")], default="draft", required=True, readonly=True, tracking=True, copy=False)
    scheduled_at = fields.Datetime()
    attachment_ids = fields.Many2many("ir.attachment", string="Media")
    target_ids = fields.One2many("social.post.target", "post_id", copy=True)
    allowed_user_ids = fields.Many2many("res.users", compute="_compute_allowed_users", store=True)
    approved_digest = fields.Char(readonly=True, copy=False)
    published_count = fields.Integer(compute="_compute_counts")
    failed_count = fields.Integer(compute="_compute_counts")

    @api.depends("target_ids.account_id.user_ids", "author_id")
    def _compute_allowed_users(self):
        for post in self:
            accounts = post.target_ids.account_id
            allowed = accounts[0].user_ids if accounts else post.author_id
            for account in accounts[1:]:
                allowed &= account.user_ids
            post.allowed_user_ids = allowed

    @api.depends("target_ids.state")
    def _compute_counts(self):
        for rec in self:
            rec.published_count = len(rec.target_ids.filtered(lambda t: t.state == "published"))
            rec.failed_count = len(rec.target_ids.filtered(lambda t: t.state in ("failed", "uncertain")))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("state", "draft") != "draft" or vals.get("approved_digest") or vals.get("review_ids"):
                raise AccessError(_("Create a draft before requesting approval."))
            vals["author_id"] = self.env.uid
            vals.pop("allowed_user_ids", None)
        return super().create(vals_list)

    def _lock(self):
        self.check_access("write")
        if self.ids:
            self.env.cr.execute("SELECT id FROM social_post WHERE id IN %s ORDER BY id FOR UPDATE", [tuple(self.ids)])
            self.invalidate_recordset()

    def _assert_operator(self):
        self.check_access("write")
        if not self.env.user.has_group("social.group_social_user"):
            raise AccessError(_("Social operator access is required."))
        for post in self:
            if post.company_id not in self.env.companies:
                raise AccessError(_("Select the post company first."))
            for account in post.target_ids.account_id:
                account._assert_operate()

    def write(self, vals):
        protected = {"state", "approved_digest", "allowed_user_ids", "author_id", "review_ids"}
        if protected.intersection(vals):
            raise AccessError(_("Use the post workflow actions."))
        if {"company_id", "content", "attachment_ids", "target_ids", "scheduled_at", "name", "campaign_id"}.intersection(vals):
            self._lock()
            if any(post.state != "draft" for post in self):
                raise UserError(_("Reset to draft before editing reviewed content."))
        return super().write(vals)

    def unlink(self):
        self._lock()
        if any(post.state != "draft" or post.target_ids.filtered(lambda t: t.state == "published") for post in self):
            raise UserError(_("Only unpublished drafts can be deleted."))
        return super().unlink()

    def _digest(self):
        self.ensure_one()
        self.attachment_ids.check_access("read")
        data = {
            "content": self.content, "company": self.company_id.id,
            "media": [(a.id, a.checksum) for a in self.attachment_ids.sorted("id")],
            "targets": [(t.account_id.id, t.account_id.external_account_id, t.account_id.platform, t.platform_content or "", str(t.scheduled_at or "")) for t in self.target_ids.sorted("id")],
            "schedule": str(self.scheduled_at or ""),
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def request_validation(self):
        self._assert_operator()
        self._lock()
        if any(p.state not in self._state_from for p in self):
            raise UserError(_("Only drafts or review documents can request validation."))
        return super().request_validation()

    def action_request_review(self):
        self._assert_operator()
        self._lock()
        for post in self:
            if post.state != "draft" or not post.target_ids:
                raise UserError(_("Add at least one target to a draft first."))
            # Change state before requesting tiers, so OCA can lock the content.
            super(SocialPost, post).write({"state": "review"})
            post.request_validation()

    def action_approve(self):
        self._assert_operator()
        self._lock()
        if not self.env.user.has_group("social.group_social_publisher"):
            raise AccessError(_("Publisher access is required."))
        for post in self:
            if post.state not in self._state_from or not post.target_ids:
                raise UserError(_("Only a draft or reviewed post with targets can be approved."))
            if post.need_validation or (post.review_ids and post.validation_status != "validated"):
                raise UserError(_("Complete all required tier reviews before approving."))
            for target in post.target_ids:
                target.account_id._assert_operate("publishing")
                target.account_id._validate_target(target)
            super(SocialPost, post).write({"state": "approved", "approved_digest": post._digest()})

    def action_reset_draft(self):
        self._assert_operator()
        self._lock()
        for post in self:
            if post.target_ids.filtered(lambda t: t.state in ("publishing", "published", "uncertain")):
                raise UserError(_("Duplicate the post to revise published or uncertain deliveries."))
            assert_unpublished(post.target_ids)
            post.target_ids._set_delivery({"state": "cancelled"})
            post.restart_validation()
            super(SocialPost, post).write({"state": "draft", "approved_digest": False})
            post.restart_validation()
            post.target_ids._set_delivery({"state": "draft", "error_message": False})

    def action_cancel(self):
        self._assert_operator()
        self._lock()
        for post in self:
            if post.target_ids.filtered(lambda t: t.state in ("publishing", "uncertain")):
                raise UserError(_("Resolve in-flight or uncertain deliveries first."))
            pending = post.target_ids.filtered(lambda t: t.state != "published")
            assert_unpublished(pending)
            pending._set_delivery({"state": "cancelled"})
            super(SocialPost, post).write({"state": "cancelled"})

    def action_publish(self):
        self._assert_operator()
        self._lock()
        if not self.env.user.has_group("social.group_social_publisher"):
            raise AccessError(_("Publisher access is required."))
        for post in self:
            post._assert_approved()
            for target in post.target_ids.filtered(lambda t: t.state == "draft"):
                target._enqueue()

    def _assert_approved(self):
        self.ensure_one()
        if self.state != "approved" or self.approved_digest != self._digest():
            raise UserError(_("Approved content changed or the post is not approved."))
        # Re-evaluate current tier definitions, including newly-added rules.
        definitions = self.env["tier.definition"].search([("model", "=", self._name), ("company_id", "in", [False, self.company_id.id])])
        required = definitions.filtered(lambda d: self.evaluate_tier(d))
        approved = self.review_ids.filtered(lambda r: r.status == "approved").definition_id
        if required - approved or (self.review_ids and self.validation_status != "validated"):
            raise UserError(_("Required tier approval is missing or no longer valid."))


class SocialPostTarget(models.Model):
    _name = "social.post.target"
    _description = "Social Publication"
    _rec_name = "account_id"
    _check_company_auto = True

    post_id = fields.Many2one("social.post", required=True, ondelete="cascade", index=True, check_company=True)
    company_id = fields.Many2one(related="post_id.company_id", store=True, index=True)
    account_id = fields.Many2one("social.account", required=True, ondelete="restrict", check_company=True, index=True)
    platform = fields.Selection(related="account_id.platform", store=True)
    platform_content = fields.Text()
    scheduled_at = fields.Datetime()
    state = fields.Selection([(x, label) for x, label in [("draft", "Draft"), ("queued", "Queued / scheduled"), ("publishing", "Publishing"), ("published", "Published"), ("failed", "Failed"), ("uncertain", "Check platform"), ("cancelled", "Cancelled")]], default="draft", required=True, readonly=True, index=True, copy=False)
    external_post_id = fields.Char(readonly=True, copy=False)
    external_url = fields.Char(readonly=True, copy=False)
    published_at = fields.Datetime(readonly=True, copy=False)
    last_attempt_at = fields.Datetime(readonly=True, copy=False)
    error_message = fields.Char(readonly=True, copy=False)
    attempt_count = fields.Integer(readonly=True, copy=False)
    queue_generation = fields.Char(readonly=True, copy=False)
    scheduled_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    _target_unique = models.Constraint("UNIQUE(post_id, account_id)", "Use one target per account in a post.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if set(vals) - {"post_id", "account_id", "platform_content", "scheduled_at", "state"} or vals.get("state", "draft") != "draft":
                raise AccessError(_("Delivery fields are system managed."))
            post = self.env["social.post"].browse(vals["post_id"])
            post._lock()
            if post.state != "draft":
                raise UserError(_("Targets can only be added to drafts."))
            self.env["social.account"].browse(vals["account_id"])._assert_operate()
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) - {"platform_content", "scheduled_at", "account_id"}:
            raise AccessError(_("Delivery fields are system managed."))
        self.post_id._lock()
        if any(t.post_id.state != "draft" for t in self):
            raise UserError(_("Reset the post before changing targets."))
        if vals.get("account_id"):
            self.env["social.account"].browse(vals["account_id"])._assert_operate()
        return super().write(vals)

    def unlink(self):
        self.post_id._lock()
        if any(t.post_id.state != "draft" for t in self):
            raise UserError(_("Targets can only be removed from drafts."))
        return super().unlink()

    def _set_delivery(self, vals):
        return super().write(vals)

    def _enqueue(self):
        self.ensure_one()
        self.account_id._assert_operate("publishing")
        self.account_id._validate_target(self)
        reset_rejected_checkpoint(self)
        generation = str(uuid4())
        self._set_delivery({"queue_generation": generation, "state": "queued", "scheduled_by_id": self.env.uid, "error_message": False})
        self.with_delay(eta=self.scheduled_at or self.post_id.scheduled_at, identity_key=f"social-publish-{self.id}-{generation}", max_retries=5, description=f"Social publication {self.id}")._job_publish(generation)

    def action_retry(self):
        self.post_id._assert_operator()
        self.post_id._lock()
        if not self.env.user.has_group("social.group_social_publisher"):
            raise AccessError(_("Publisher access is required."))
        for target in self:
            if target.state != "failed":
                raise UserError(_("Only known failed deliveries may be retried. Check uncertain results on the platform."))
            target.post_id._assert_approved()
            target._enqueue()

    def _job_publish(self, generation=None):
        self.ensure_one()
        self.post_id._lock()
        self.invalidate_recordset()
        if self.state != "queued" or (generation and generation != self.queue_generation):
            return
        try:
            if not self.env.user.active or not self.env.user.has_group("social.group_social_publisher"):
                raise AccessError(_("The scheduling user no longer has publishing access."))
            self.account_id._assert_operate("publishing")
            self.post_id._assert_approved()
            self.account_id._validate_target(self)
        except (AccessError, UserError, ValidationError):
            self._set_delivery({"state": "failed", "error_message": _("Access, approval or configuration changed. Review before retrying.")})
            return
        self._set_delivery({"state": "publishing", "last_attempt_at": fields.Datetime.now(), "attempt_count": self.attempt_count + 1})
        try:
            result = deliver(self, lambda: self.account_id._publish_target(self))
        except DeliveryTemporary as error:
            self._set_delivery({"state": "queued"})
            raise RetryableJobError("Social provider temporarily unavailable", seconds=error.args[0] if error.args else 60)
        except DeliveryPermanent:
            self._set_delivery({"state": "failed", "error_message": _("Provider rejected the publication. Check account permissions and content.")})
            return
        except DeliveryUncertain:
            self._set_delivery({"state": "uncertain", "error_message": _("Delivery outcome is unknown. Inspect the platform before taking further action.")})
            return
        self._set_delivery({"state": "published", "external_post_id": str(result["id"]), "external_url": result.get("url", False), "published_at": fields.Datetime.now(), "error_message": False})
        self.post_id.message_post(body=_("Publication completed for account %s.", self.account_id.name), subtype_xmlid="mail.mt_note")

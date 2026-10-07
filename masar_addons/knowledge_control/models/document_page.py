# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Controlled document lifecycle on ``document.page``.

ADR-1: versions are frozen ``document.page.history`` rows (no second content store).
ADR-2 Option A: Tier Validation gates controlled publish; ``document_page_approval``
remains for ordinary change requests. On publish we mark the history row approved
so HEAD stays coherent.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


KC_STATES = [
    ("draft", "Draft"),
    ("review", "Review"),
    ("approval", "Approval"),
    ("published", "Published"),
    ("review_due", "Review Due"),
    ("superseded", "Superseded"),
    ("archived", "Archived"),
]

KC_DOC_TYPES = [
    ("article", "Knowledge Article"),
    ("policy", "Policy"),
    ("procedure", "Procedure"),
    ("manual", "Manual"),
    ("guideline", "Guideline"),
    ("work_instruction", "Work Instruction"),
    ("form", "Form"),
    ("template", "Template"),
    ("controlled", "Controlled Document"),
]

_FROZEN_STATES = frozenset({"published", "superseded", "archived"})
_ACK_CONFIRMATION_TEXT = (
    "I confirm that I have read and understood this controlled document version "
    "and agree to comply with its requirements."
)


class DocumentPage(models.Model):
    _name = "document.page"
    _inherit = ["document.page", "tier.validation"]

    _state_field = "kc_state"
    _state_from = ["draft", "review", "approval"]
    _state_to = ["published"]
    _cancel_state = "archived"
    _tier_validation_manual_config = False

    kc_controlled = fields.Boolean(
        string="Controlled document",
        default=False,
        tracking=True,
        help="Enable formal lifecycle, versioning and distribution. "
        "Ordinary Knowledge pages must leave this disabled.",
    )
    kc_document_type = fields.Selection(
        KC_DOC_TYPES,
        string="Document type",
        default="article",
        tracking=True,
        index=True,
    )
    kc_state = fields.Selection(
        KC_STATES,
        string="Control status",
        default="draft",
        tracking=True,
        copy=False,
        index=True,
    )
    kc_version_type = fields.Selection(
        [
            ("major", "Major"),
            ("minor", "Minor"),
            ("editorial", "Editorial"),
        ],
        string="Next version type",
        default="minor",
        help="Applied when publishing the next controlled revision on this page.",
    )
    kc_published_history_id = fields.Many2one(
        "document.page.history",
        string="Published version",
        readonly=True,
        copy=False,
        help="Exact frozen history snapshot currently in force.",
    )
    kc_published_version = fields.Char(
        related="kc_published_history_id.kc_version_label",
        string="Published version label",
        readonly=True,
    )
    kc_published_date = fields.Datetime(readonly=True, copy=False)
    kc_published_uid = fields.Many2one("res.users", readonly=True, copy=False)
    kc_baseline_kind = fields.Selection(
        [
            ("native", "Native historical version"),
            ("baseline_at_control", "Baseline at control activation"),
        ],
        string="Baseline provenance",
        copy=False,
        help="Set when control is first activated; never invents older versions.",
    )
    kc_previous_page_id = fields.Many2one(
        "document.page",
        string="Forked from page",
        copy=False,
        help="Only when deliberately forking to a new page (rare).",
    )
    kc_superseded_by_id = fields.Many2one(
        "document.page",
        string="Superseded by page",
        readonly=True,
        copy=False,
        help="Set only for page-level forks, not in-place history revisions.",
    )
    kc_policy_ids = fields.Many2many(
        "document.page",
        "document_page_kc_policy_rel",
        "procedure_id",
        "policy_id",
        string="Related policies",
        domain="[('kc_document_type', '=', 'policy'), ('id', '!=', id)]",
    )
    kc_procedure_ids = fields.Many2many(
        "document.page",
        "document_page_kc_policy_rel",
        "policy_id",
        "procedure_id",
        string="Related procedures",
        domain="[('kc_document_type', 'in', ('procedure', 'work_instruction', 'form', 'template')), "
        "('id', '!=', id)]",
    )
    kc_distribution_ids = fields.One2many(
        "document.page.distribution",
        "page_id",
        string="Distributions",
    )
    kc_distribution_count = fields.Integer(compute="_compute_kc_distribution_stats")
    kc_ack_count = fields.Integer(compute="_compute_kc_distribution_stats")
    kc_ack_pending_count = fields.Integer(compute="_compute_kc_distribution_stats")
    kc_ack_rate = fields.Float(
        string="Acknowledgment %",
        compute="_compute_kc_distribution_stats",
        digits=(16, 1),
    )
    kc_ack_confirmation_text = fields.Text(
        string="Acknowledgment wording",
        default=_ACK_CONFIRMATION_TEXT,
        help="Frozen onto each distribution line at assignment time.",
    )

    def init(self):
        # Unique document code among controlled pages (company scope).
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS document_page_kc_doc_code_uniq
            ON document_page (COALESCE(company_id, 0), masar_doc_code)
            WHERE kc_controlled IS TRUE
              AND masar_doc_code IS NOT NULL
              AND masar_doc_code != ''
            """
        )

    @api.depends(
        "kc_distribution_ids",
        "kc_distribution_ids.state",
        "kc_distribution_ids.history_id",
        "kc_published_history_id",
    )
    def _compute_kc_distribution_stats(self):
        for page in self:
            lines = page.kc_distribution_ids.filtered(
                lambda d: d.history_id == page.kc_published_history_id
                and d.state != "cancelled"
            )
            page.kc_distribution_count = len(lines)
            ack = lines.filtered(lambda d: d.state == "acknowledged")
            pending = lines.filtered(lambda d: d.state in ("pending", "viewed", "overdue"))
            page.kc_ack_count = len(ack)
            page.kc_ack_pending_count = len(pending)
            page.kc_ack_rate = (100.0 * len(ack) / len(lines)) if lines else 0.0

    def write(self, vals):
        content_keys = {"content", "name", "draft_name", "draft_summary", "template"}
        if content_keys & set(vals) and not self.env.context.get("kc_allow_frozen_write"):
            frozen = self.filtered(
                lambda p: p.kc_controlled and p.kc_state in _FROZEN_STATES
            )
            if frozen:
                frozen._kc_assert_editable()
        # Activating control: baseline provenance, never invent versions.
        if vals.get("kc_controlled") is True:
            for page in self:
                if not page.kc_controlled and not page.kc_baseline_kind:
                    vals.setdefault("kc_baseline_kind", "baseline_at_control")
        return super().write(vals)

    def _inverse_content(self):
        if not self.env.context.get("kc_allow_frozen_write"):
            self.filtered(
                lambda p: p.kc_controlled and p.kc_state in _FROZEN_STATES
            )._kc_assert_editable()
        return super()._inverse_content()

    def unlink(self):
        protected = self.filtered(
            lambda p: p.kc_controlled
            and (
                p.kc_state in ("published", "superseded", "archived", "review_due")
                or p.kc_published_history_id
                or p.kc_distribution_ids
            )
        )
        if protected and not self.env.context.get("kc_force_unlink"):
            raise UserError(
                _(
                    "Cannot permanently delete controlled document(s) «%s». "
                    "Archive or supersede instead.",
                    ", ".join(protected.mapped("display_name")),
                )
            )
        return super().unlink()

    def _kc_assert_editable(self):
        for page in self:
            if page.kc_controlled and page.kc_state in _FROZEN_STATES:
                raise UserError(
                    _(
                        "Controlled document «%(name)s» is %(state)s and cannot be "
                        "edited in place. Use «Start revision» first.",
                        name=page.name,
                        state=dict(KC_STATES).get(page.kc_state),
                    )
                )

    def _kc_require_controlled(self):
        for page in self:
            if not page.kc_controlled:
                raise UserError(
                    _("Enable «Controlled document» before using this action.")
                )

    def _kc_lock_page_row(self):
        """Serialize version assignment for this page (concurrency-safe)."""
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM document_page WHERE id = %s FOR UPDATE",
            [self.id],
        )

    def _kc_get_publish_candidate_history(self):
        """Latest unfrozen history row (draft/to approve/approved), else HEAD."""
        self.ensure_one()
        History = self.env["document.page.history"].sudo()
        domain = [
            ("page_id", "=", self.id),
            ("kc_frozen", "=", False),
        ]
        if "state" in History._fields:
            domain.append(("state", "in", ("draft", "to approve", "approved")))
        candidate = History.search(domain, order="id desc", limit=1)
        return candidate or self.history_head

    def _kc_mark_history_approved(self, history):
        """Option A bridge: keep document_page_approval HEAD coherent after Tier publish."""
        if "state" not in history._fields:
            return
        if history.state != "approved":
            history.sudo().write(
                {
                    "state": "approved",
                    "approved_date": fields.Datetime.now(),
                    "approved_uid": self.env.uid,
                }
            )
            # Refresh filtered history_ids / HEAD
            history.page_id._compute_history_head()

    def action_kc_submit_review(self):
        self._kc_require_controlled()
        for page in self:
            if page.kc_state not in ("draft", "review_due"):
                raise UserError(_("Only Draft / Review Due documents can enter Review."))
            page.kc_state = "review"
            page.masar_status = "under_review"
        return True

    def action_kc_request_approval(self):
        """Move to Approval and request Tier Validation (controlled publish gate)."""
        self._kc_require_controlled()
        for page in self:
            if page.kc_state not in ("review", "draft"):
                raise UserError(_("Submit for approval from Review or Draft."))
            page.kc_state = "approval"
            page.masar_status = "under_review"
            if page.need_validation:
                page.request_validation()
        return True

    def action_kc_start_revision(self):
        """Open an in-place revision on the same page (ADR-1 / ADR-3).

        Keeps ``kc_published_history_id`` pointing at the still-current frozen
        version until the next publish. Does not invent a new page record.
        """
        self._kc_require_controlled()
        for page in self:
            if page.kc_state not in ("published", "review_due"):
                raise UserError(_("Start revision from Published or Review Due."))
            page.with_context(kc_allow_frozen_write=True).write(
                {
                    "kc_state": "draft",
                    "masar_status": "draft",
                }
            )
            page.message_post(
                body=_(
                    "Revision started. Current published version remains %(ver)s "
                    "until the next publish.",
                    ver=page.kc_published_version or "—",
                )
            )
        return True

    def action_kc_publish(self):
        self._kc_require_controlled()
        for page in self:
            if page.kc_state not in ("approval", "draft", "review"):
                raise UserError(
                    _("Publish is only allowed from Approval (or Review for simple flows).")
                )
            # Hard gate: if this controlled page needs Tier Validation, it may
            # only publish once validation_status is "validated". The previous
            # form only blocked the waiting/pending/rejected sub-states, so a
            # page that needed validation but had no tier review yet (status
            # "no") slipped through and published unvalidated.
            if page.need_validation and page.validation_status != "validated":
                raise UserError(
                    _("Complete Tier Validation before publishing «%s».", page.name)
                )
            page._kc_lock_page_row()
            history = page._kc_get_publish_candidate_history()
            if not history:
                raise UserError(_("Save content before publishing."))
            if history.kc_frozen:
                raise UserError(
                    _("This history snapshot is already a published controlled version.")
                )
            previous = page.kc_published_history_id
            if not previous and page.kc_previous_page_id:
                previous = page.kc_previous_page_id.kc_published_history_id
            history._kc_assign_version(
                version_type=page.kc_version_type or "minor",
                previous=previous,
            )
            history.write({"kc_frozen": True})
            page._kc_mark_history_approved(history)
            page.with_context(kc_allow_frozen_write=True).write(
                {
                    "kc_state": "published",
                    "kc_published_history_id": history.id,
                    "kc_published_date": fields.Datetime.now(),
                    "kc_published_uid": self.env.uid,
                    "masar_status": "active",
                    "masar_effective_date": page.masar_effective_date
                    or fields.Date.context_today(page),
                }
            )
            page.message_post(
                body=_(
                    "Published controlled version %(ver)s "
                    "(history #%(hid)s).",
                    ver=history.kc_version_label,
                    hid=history.id,
                )
            )
        return True

    def action_kc_mark_review_due(self):
        for page in self.filtered(
            lambda p: p.kc_controlled and p.kc_state == "published"
        ):
            # Idempotent: skip if already review_due
            page.kc_state = "review_due"
            page.masar_status = "under_review"
            existing = page.activity_ids.filtered(
                lambda a: a.activity_type_id
                == self.env.ref("knowledge_control.mail_activity_kc_review")
                and a.state != "done"
            )
            if not existing:
                page.activity_schedule(
                    "knowledge_control.mail_activity_kc_review",
                    user_id=(page.masar_owner_uid or page.content_uid or self.env.user).id,
                    summary=_("Document review due: %s", page.display_name),
                )
        return True

    def action_kc_archive_controlled(self):
        self._kc_require_controlled()
        for page in self:
            if page.kc_state not in ("published", "review_due", "superseded"):
                raise UserError(_("Archive from Published / Review Due / Superseded."))
            page.kc_state = "archived"
            page.masar_status = "retired"
            page.active = False
        return True

    def action_kc_fork_page(self):
        """Rare: fork to a new page record. Prefer «Start revision» on same page."""
        self.ensure_one()
        self._kc_require_controlled()
        if self.kc_state not in ("published", "review_due"):
            raise UserError(_("Only a published document can be forked."))
        new_page = self.copy(
            {
                "name": self.name,
                "kc_state": "draft",
                "kc_controlled": True,
                "kc_published_history_id": False,
                "kc_published_date": False,
                "kc_published_uid": False,
                "kc_previous_page_id": self.id,
                "kc_superseded_by_id": False,
                "kc_baseline_kind": "baseline_at_control",
                "masar_status": "draft",
                "masar_doc_code": False,
            }
        )
        self.with_context(kc_allow_frozen_write=True).write(
            {
                "kc_state": "superseded",
                "kc_superseded_by_id": new_page.id,
                "masar_status": "retired",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "document.page",
            "res_id": new_page.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_kc_open_distributions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Acknowledgments"),
            "res_model": "document.page.distribution",
            "view_mode": "list,form",
            "domain": [("page_id", "=", self.id)],
            "context": {
                "default_page_id": self.id,
                "default_history_id": self.kc_published_history_id.id,
            },
        }

    def action_kc_distribute_wizard(self):
        self.ensure_one()
        if not self.kc_published_history_id:
            raise UserError(_("Publish a version before distributing."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Distribute document"),
            "res_model": "document.page.distribute.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_page_id": self.id,
                "default_history_id": self.kc_published_history_id.id,
            },
        }

    @api.model
    def _cron_kc_review_due(self):
        today = fields.Date.context_today(self)
        due = self.search(
            [
                ("kc_controlled", "=", True),
                ("kc_state", "=", "published"),
                ("masar_review_date", "!=", False),
                ("masar_review_date", "<=", today),
            ]
        )
        due.action_kc_mark_review_due()

    @api.model
    def _cron_kc_ack_overdue(self):
        self.env["document.page.distribution"]._cron_mark_overdue()

    @api.model
    def _get_under_validation_exceptions(self):
        exceptions = super()._get_under_validation_exceptions()
        exceptions += [
            "kc_state",
            "kc_published_history_id",
            "kc_published_date",
            "kc_published_uid",
            "kc_baseline_kind",
            "masar_status",
            "masar_effective_date",
            "masar_review_date",
        ]
        return exceptions

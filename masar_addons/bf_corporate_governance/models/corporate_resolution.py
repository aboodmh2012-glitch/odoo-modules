# -*- coding: utf-8 -*-
# Copyright (c) 2026 Les services de consultation Blue Fox, Inc.
# Copyright 2026 MASAR (Odoo 19 port; AGPL-3 — see ADR-8 / THIRD_PARTY_NOTICES)
# SPDX-License-Identifier: AGPL-3.0-or-later
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CorporateResolution(models.Model):
    _name = "corporate.resolution"
    _description = "Corporate Resolution"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "meeting_date desc, sequence desc"

    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
    )
    sequence = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        default="New",
    )
    resolution_type = fields.Selection(
        selection=[
            ("board", "Board resolution"),
            ("shareholder", "Shareholder resolution"),
            ("written_board", "Written board resolution"),
            ("written_shareholder", "Written shareholder resolution"),
        ],
        string="Resolution type",
        required=True,
        default="board",
        tracking=True,
    )
    meeting_type = fields.Selection(
        selection=[
            ("regular", "Regular"),
            ("special", "Special"),
            ("agm", "Annual general meeting"),
            ("written", "Written consent"),
        ],
        string="Meeting type",
        default="regular",
        tracking=True,
    )
    subject_category = fields.Selection(
        selection=[
            ("officer_appointment", "Officer appointment"),
            ("director_election", "Director election"),
            ("dividend_declaration", "Dividend declaration"),
            ("share_issuance", "Share issuance"),
            ("bylaw_amendment", "Bylaw amendment"),
            ("contract_approval", "Contract approval"),
            ("bank_authorization", "Bank authorization"),
            ("auditor_appointment", "Auditor appointment"),
            ("fiscal_year", "Fiscal year"),
            ("financial_approval", "Financial approval"),
            ("dissolution", "Dissolution"),
            ("other", "Other"),
        ],
        string="Subject category",
        tracking=True,
    )
    status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("proposed", "Proposed"),
            ("adopted", "Adopted"),
            ("rejected", "Rejected"),
            ("superseded", "Superseded"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    meeting_date = fields.Date(
        string="Meeting date",
        required=True,
        tracking=True,
    )
    meeting_id = fields.Many2one(
        "corporate.meeting",
        string="Meeting",
        tracking=True,
        index=True,
        help="Optional meeting at which this resolution was adopted. Written "
        "board/shareholder resolutions may have no meeting; leave empty.",
    )
    whereas_text = fields.Html(
        string="Whereas…",
        help="Preamble / whereas clauses (jurisdiction-neutral wording).",
    )
    resolved_text = fields.Html(
        string="Resolved…",
        help="Operative / resolved clauses.",
    )
    mover_id = fields.Many2one(
        "res.partner",
        string="Moved by",
        tracking=True,
    )
    seconder_id = fields.Many2one(
        "res.partner",
        string="Seconded by",
        tracking=True,
    )
    vote_for = fields.Integer(string="Votes for")
    vote_against = fields.Integer(string="Votes against")
    vote_abstain = fields.Integer(string="Abstentions")
    unanimously_adopted = fields.Boolean(
        string="Unanimously adopted",
        tracking=True,
    )
    effective_date = fields.Date(
        string="Effective date",
        tracking=True,
    )
    superseded_by_id = fields.Many2one(
        "corporate.resolution",
        string="Superseded by",
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "corporate_resolution_attachment_rel",
        "resolution_id",
        "attachment_id",
        string="Attachments",
    )
    # Navigation only — mutable Knowledge pages. Evidence = approved_history_ids.
    document_ids = fields.Many2many(
        "document.page",
        "corporate_resolution_document_rel",
        "resolution_id",
        "document_id",
        string="Minute Book pages (navigation)",
        help="Convenience links to Knowledge pages. Not legal evidence. "
             "Pin exact frozen controlled versions in Approved controlled versions.",
    )
    # Exact controlled Knowledge versions adopted by this resolution (evidence).
    approved_history_ids = fields.Many2many(
        "document.page.history",
        "corporate_resolution_history_rel",
        "resolution_id",
        "history_id",
        string="Approved controlled versions (evidence)",
        domain="[('kc_frozen', '=', True)]",
        help="Pin exact frozen document.page.history rows that the board/shareholders "
             "adopted. Only kc_frozen published controlled snapshots are allowed. "
             "Never rely on mutable page HEAD alone.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    signatory_ids = fields.One2many(
        "corporate.resolution.signatory",
        "resolution_id",
        string="Signatories",
        copy=True,
        help="People who sign this resolution and the capacity in which they sign. "
             "If empty, board resolutions fall back to directors in office on the "
             "meeting date; shareholder resolutions leave a blank signature line.",
    )
    notes = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("sequence", "New") == "New":
                vals["sequence"] = self.env["ir.sequence"].next_by_code(
                    "corporate.resolution"
                ) or "New"
        return super().create(vals_list)

    def action_propose(self):
        self.write({"status": "proposed"})

    @api.onchange("meeting_id")
    def _onchange_meeting_id(self):
        """Reuse the meeting's date rather than re-entering it (kept for the
        legacy ``meeting_date`` field used by existing reports)."""
        if self.meeting_id and self.meeting_id.date:
            self.meeting_date = fields.Date.to_date(self.meeting_id.date)

    def action_adopt(self):
        # Adoption is a board act; a Board Secretary may prepare drafts but may
        # not adopt on the board's behalf (needs Governance Manager).
        if not self.env.user.has_group(
            "bf_corporate_governance.group_corporate_manager"
        ):
            raise ValidationError(_(
                "Only a Governance Manager can adopt a resolution. A Board "
                "Secretary may prepare and propose drafts, but adoption is a "
                "board act."
            ))
        self._check_approved_histories()
        vals = {"status": "adopted"}
        for rec in self:
            write_vals = dict(vals)
            if not rec.effective_date:
                write_vals["effective_date"] = rec.meeting_date
            rec.write(write_vals)

    def action_reject(self):
        self.write({"status": "rejected"})

    def action_reset_draft(self):
        self.write({"status": "draft"})

    @api.constrains("approved_history_ids")
    def _check_approved_histories(self):
        """Evidence rows must be frozen numbered controlled publish snapshots.

        Ordinary ``document.page.history`` approval states (change requests) are
        not enough — the board must pin an exact ``kc_frozen`` version.
        """
        for rec in self:
            for hist in rec.approved_history_ids:
                if not hist.kc_frozen:
                    raise ValidationError(_(
                        "Approved controlled version “%(label)s” is not frozen. "
                        "Only published controlled snapshots (kc_frozen) may be "
                        "pinned as resolution evidence."
                    ) % {"label": hist.display_name})
                if not hist.kc_version_major and not hist.kc_version_minor:
                    raise ValidationError(_(
                        "History “%(label)s” has no controlled version number. "
                        "Pin a published Major.Minor snapshot, not a draft "
                        "history row."
                    ) % {"label": hist.display_name})

    @api.constrains("document_ids", "approved_history_ids", "status")
    def _check_evidence_vs_navigation(self):
        """Adopted resolutions that cite controlled pages need frozen evidence."""
        for rec in self:
            if rec.status != "adopted":
                continue
            controlled_pages = rec.document_ids.filtered("kc_controlled")
            if not controlled_pages:
                continue
            pinned_pages = rec.approved_history_ids.mapped("page_id")
            missing = controlled_pages - pinned_pages
            if missing:
                raise ValidationError(_(
                    "Resolution %(ref)s links controlled Knowledge page(s) "
                    "%(pages)s but does not pin frozen approved versions. "
                    "Pages are navigation only; add Approved controlled versions "
                    "before adopting."
                ) % {
                    "ref": rec.sequence or rec.display_name,
                    "pages": ", ".join(missing.mapped("name")),
                })

    def _get_active_directors(self):
        return self.env["corporate.director"].search([
            ("company_id", "=", self.company_id.id),
            ("is_active", "=", True),
        ])

    def _get_directors_at_date(self, date=None):
        """Directors in office on a given date (meeting date by default).

        ``is_active`` answers “today”. A resolution may be printed months later;
        without a date bound the PDF would name directors not yet elected.
        A term ending on day D is no longer in office on day D.
        """
        self.ensure_one()
        date = date or self.meeting_date or fields.Date.today()
        return self.env["corporate.director"].search([
            ("company_id", "=", self.company_id.id),
            ("appointment_date", "<=", date),
            "|", ("end_date", "=", False), ("end_date", ">", date),
        ])

    def _get_signatories(self):
        """Signature block: who signs, in which capacity, for what purpose.

        1. Explicit signatories win.
        2. Else board resolution → directors in office on meeting date.
        3. Else shareholder resolution → mover/seconder named without capacity
           (module has no shareholder register).
        """
        self.ensure_one()
        if self.signatory_ids:
            return [{
                "name": line.partner_id.name,
                "capacity": line.capacity_label,
                "purpose": line.purpose,
            } for line in self.signatory_ids]
        if self.resolution_type in ("board", "written_board"):
            return [{
                "name": director.partner_id.name,
                "capacity": _("Director"),
                "purpose": False,
            } for director in self._get_directors_at_date()]
        return [{
            "name": partner.name,
            "capacity": False,
            "purpose": False,
        } for partner in (self.mover_id | self.seconder_id)]

    def _get_resolution_type_label(self):
        if self.resolution_type in ("board", "written_board"):
            return _("Written resolution of the directors")
        return _("Written resolution of the shareholders")

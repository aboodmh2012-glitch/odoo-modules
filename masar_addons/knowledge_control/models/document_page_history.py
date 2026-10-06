# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError


class DocumentPageHistory(models.Model):
    _inherit = "document.page.history"

    kc_version_major = fields.Integer(string="Major", copy=False)
    kc_version_minor = fields.Integer(string="Minor", copy=False)
    kc_version_type = fields.Selection(
        [
            ("major", "Major"),
            ("minor", "Minor"),
            ("editorial", "Editorial"),
        ],
        string="Version type",
        copy=False,
    )
    kc_version_label = fields.Char(
        string="Version",
        compute="_compute_kc_version_label",
        store=True,
        index=True,
    )
    kc_frozen = fields.Boolean(
        string="Frozen controlled version",
        default=False,
        copy=False,
        index=True,
        help="True when this history row is a published controlled version snapshot.",
    )
    kc_previous_history_id = fields.Many2one(
        "document.page.history",
        string="Previous controlled version",
        copy=False,
        ondelete="restrict",
    )
    kc_content_sha256 = fields.Char(
        string="Content SHA-256",
        copy=False,
        help="Hash of HTML content at freeze time (integrity evidence).",
    )

    def init(self):
        # Partial unique: only frozen controlled versions (maj,min) per page.
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS document_page_history_kc_frozen_version_uniq
            ON document_page_history (page_id, kc_version_major, kc_version_minor)
            WHERE kc_frozen IS TRUE
              AND kc_version_major IS NOT NULL
              AND kc_version_minor IS NOT NULL
            """
        )

    @api.depends("kc_version_major", "kc_version_minor", "name", "kc_frozen")
    def _compute_kc_version_label(self):
        for rec in self:
            if rec.kc_version_major is not None and rec.kc_version_minor is not None and (
                rec.kc_frozen or rec.kc_version_major or rec.kc_version_minor
            ):
                rec.kc_version_label = f"{rec.kc_version_major or 0}.{rec.kc_version_minor or 0}"
            else:
                rec.kc_version_label = rec.name or ""

    def write(self, vals):
        if self.filtered("kc_frozen") and not self.env.context.get("kc_allow_frozen_history"):
            forbidden = {"content", "name", "summary", "kc_version_major", "kc_version_minor"}
            if forbidden & set(vals):
                raise UserError(
                    self.env._(
                        "Frozen controlled history snapshots cannot be rewritten."
                    )
                )
        return super().write(vals)

    def unlink(self):
        if self.filtered("kc_frozen") and not self.env.context.get("kc_force_unlink"):
            raise UserError(
                self.env._(
                    "Cannot delete frozen controlled version snapshots. "
                    "Supersede via a new publish instead."
                )
            )
        return super().unlink()

    def _kc_assign_version(self, *, version_type="minor", previous=False):
        """Stamp structured version numbers — caller must hold page row lock."""
        self.ensure_one()
        if self.kc_frozen:
            raise UserError(self.env._("History row is already a frozen controlled version."))
        prev = previous or self.env["document.page.history"]
        major = prev.kc_version_major if prev else 0
        minor = prev.kc_version_minor if prev else 0
        if version_type == "major":
            major = (major or 0) + 1
            minor = 0
        else:  # minor or editorial — both advance the minor number
            # "editorial" is recorded in kc_version_type (below) for provenance,
            # but must still take a DISTINCT number: keeping the previous
            # major.minor collided with the frozen predecessor and made every
            # editorial publish raise "version already exists".
            if not prev or (not major and not minor):
                major, minor = 1, 0
            else:
                minor = (minor or 0) + 1
        # Collision check under page lock
        clash = self.search(
            [
                ("page_id", "=", self.page_id.id),
                ("kc_frozen", "=", True),
                ("kc_version_major", "=", major),
                ("kc_version_minor", "=", minor),
            ],
            limit=1,
        )
        if clash:
            raise UserError(
                self.env._(
                    "Controlled version %(ver)s already exists for this document.",
                    ver=f"{major}.{minor}",
                )
            )
        import hashlib

        raw = (self.content or "").encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        label = f"{major}.{minor}"
        self.with_context(kc_allow_frozen_history=True).write(
            {
                "kc_version_major": major,
                "kc_version_minor": minor,
                "kc_version_type": version_type,
                "kc_previous_history_id": prev.id if prev else False,
                "kc_content_sha256": digest,
                "name": label,
            }
        )
        return label

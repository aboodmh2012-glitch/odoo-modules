# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrDisciplinaryCase(models.Model):
    _inherit = "hr.disciplinary.case"

    discovery_date = fields.Date(
        default=fields.Date.context_today,
        tracking=True,
        help="Date the company discovered the violation (Art. 94/97 clock).",
    )
    investigation_started_on = fields.Date(copy=False)
    suspension_notice_kind = fields.Selection(
        [
            ("oral", "Oral (verbal)"),
            ("written", "Written"),
        ],
        string="Suspension notice form",
        copy=False,
        help="Art. 98: oral ≤5 days; written ≤30 days. Precautionary, not a sanction.",
    )
    suspension_start = fields.Date(
        string="Precautionary suspension start",
        copy=False,
        help="Art. 98: precautionary measure — not a disciplinary sanction.",
    )
    suspension_end = fields.Date(string="Precautionary suspension end", copy=False)
    suspension_reason = fields.Text(copy=False)
    suspension_authority_id = fields.Many2one(
        "res.users",
        string="Suspension authorized by",
        copy=False,
    )
    sanction_aged = fields.Boolean(
        string="Notice/warning aged out",
        copy=False,
        help="Art. 95: set by cron after company warning age-out days.",
    )

    @api.constrains("suspension_start", "suspension_end")
    def _check_suspension_dates(self):
        for rec in self:
            if (
                rec.suspension_start
                and rec.suspension_end
                and rec.suspension_end < rec.suspension_start
            ):
                raise ValidationError(
                    _("Suspension end must be on or after suspension start.")
                )

    def _yemen_company(self):
        self.ensure_one()
        return self.company_id

    def _basic_wage(self):
        """Best-effort basic wage from current employee version (Odoo 19)."""
        self.ensure_one()
        emp = self.employee_id
        wage = 0.0
        version = getattr(emp, "version_id", False) or getattr(
            emp, "current_version_id", False
        )
        if version and version.wage:
            wage = version.wage
        return wage

    def _assert_discover_window(self):
        """Art. 94/97(1)(a): do not start/punish after discover_days from discovery."""
        for rec in self:
            company = rec._yemen_company()
            days = company.masar_hr_discover_days or 15
            discovered = rec.discovery_date or rec.incident_date
            if not discovered:
                continue
            limit = discovered + timedelta(days=days)
            if fields.Date.context_today(rec) > limit:
                raise UserError(
                    _(
                        "Cannot proceed: more than %(days)s days since discovery "
                        "(%(discovered)s) — Labor Law Art. 94/97. Adjust dates only "
                        "if discovery was recorded incorrectly.",
                        days=days,
                        discovered=discovered,
                    )
                )

    def _assert_completion_window(self):
        """Art. 97(1)(b): finish investigation and apply sanction within one month."""
        for rec in self:
            company = rec._yemen_company()
            days = company.masar_hr_investigate_days or 30
            # Prefer investigation start; fall back to discovery for the clock.
            started = rec.investigation_started_on or rec.discovery_date
            if not started:
                continue
            limit = started + timedelta(days=days)
            if fields.Date.context_today(rec) > limit:
                raise UserError(
                    _(
                        "Cannot apply sanction: more than %(days)s days since "
                        "investigation start/discovery (%(started)s) — "
                        "Labor Law Art. 97(1)(b).",
                        days=days,
                        started=started,
                    )
                )

    def _sanction_needs_investigation(self, sanction):
        """Art. 96: investigation required for deduction/dismissal (Art. 93(3)(4))."""
        self.ensure_one()
        if not sanction:
            return False
        return bool(
            sanction.requires_investigation
            or sanction.sanction_kind in ("deduction", "dismissal")
        )

    def _assert_investigation_required(self, sanction):
        for rec in self:
            if not rec._sanction_needs_investigation(sanction):
                continue
            if not rec.investigation_notes and not rec.employee_statement:
                raise UserError(
                    _(
                        "Sanction %(sanction)s requires a written investigation "
                        "and/or employee statement (Art. 94/96/97).",
                        sanction=sanction.display_name,
                    )
                )
            if not rec.investigation_started_on:
                raise UserError(
                    _(
                        "Start the investigation workflow before applying "
                        "deduction or dismissal (Art. 96)."
                    )
                )

    def _assert_deduction_cap(self, amount):
        for rec in self:
            if amount <= 0:
                continue
            company = rec._yemen_company()
            pct = company.masar_hr_max_deduction_pct or 20.0
            wage = rec._basic_wage()
            if wage <= 0:
                raise UserError(
                    _(
                        "Employee %(emp)s has no basic wage on the current contract "
                        "version; cannot validate the Art. 93 deduction cap "
                        "(%(pct)s%%). Set wage on hr.version first.",
                        emp=rec.employee_id.display_name,
                        pct=pct,
                    )
                )
            max_amt = wage * (pct / 100.0)
            if amount > max_amt + 0.0001:
                raise UserError(
                    _(
                        "Deduction %(amount)s exceeds %(pct)s%% of basic wage "
                        "%(wage)s (max %(max_amt)s) — Art. 93(3).",
                        amount=amount,
                        pct=pct,
                        wage=wage,
                        max_amt=max_amt,
                    )
                )

    def action_start_investigation(self):
        self._assert_discover_window()
        res = super().action_start_investigation()
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.investigation_started_on:
                # Not workflow-protected; plain write is fine.
                super(HrDisciplinaryCase, rec).write(
                    {"investigation_started_on": today}
                )
        return res

    def action_submit_recommendation(self):
        for rec in self:
            if rec.recommended_sanction_id:
                rec._assert_investigation_required(rec.recommended_sanction_id)
        return super().action_submit_recommendation()

    def action_approve_decision(self):
        for rec in self:
            sanction = rec.recommended_sanction_id
            if not sanction:
                raise UserError(_("A recommended sanction is required before approval."))
            if not rec.offense_type_id:
                raise UserError(
                    _("Cannot punish an undefined offense (Art. 94 — schedule).")
                )
            rec._assert_discover_window()
            if rec._sanction_needs_investigation(sanction) or rec.investigation_started_on:
                rec._assert_completion_window()
            rec._assert_investigation_required(sanction)
            if sanction.sanction_kind == "deduction" or sanction.has_financial_impact:
                rec._assert_deduction_cap(rec.financial_amount)
            # One sanction only — model already has a single decided_sanction_id
        res = super().action_approve_decision()
        # Prefer company default when offense still has base-module legacy 7 days
        for rec in self.filtered(lambda r: r.state == "awaiting_appeal"):
            company_days = rec.company_id.masar_hr_appeal_days_default or 30
            offense_days = rec.offense_type_id.appeal_deadline_days
            days = company_days if (not offense_days or offense_days == 7) else offense_days
            deadline = fields.Date.context_today(rec) + timedelta(days=days)
            if rec.appeal_deadline != deadline:
                rec._workflow_write({"appeal_deadline": deadline})
        return res

    def action_set_precautionary_suspension(self):
        """Record precautionary suspension (Art. 98) — not a sanction."""
        self._require_group("masar_hr_disciplinary.group_disciplinary_hr_manager")
        for rec in self:
            if not rec.suspension_start or not rec.suspension_reason:
                raise UserError(
                    _("Suspension start date and reason are required (Art. 98).")
                )
            kind = rec.suspension_notice_kind or "written"
            company = rec._yemen_company()
            if kind == "oral":
                max_days = company.masar_hr_suspension_oral_days or 5
            else:
                max_days = company.masar_hr_suspension_written_days or 30
            if not rec.suspension_end:
                raise UserError(
                    _("Suspension end date is required to validate the Art. 98 limit.")
                )
            span = (rec.suspension_end - rec.suspension_start).days + 1
            if span > max_days:
                raise UserError(
                    _(
                        "%(kind)s precautionary suspension may not exceed %(days)s "
                        "days (Art. 98).",
                        kind=_("Oral") if kind == "oral" else _("Written"),
                        days=max_days,
                    )
                )
            rec.write(
                {
                    "suspension_notice_kind": kind,
                    "suspension_authority_id": self.env.user.id,
                }
            )
            rec.message_post(
                body=_(
                    "Precautionary suspension (%(kind)s) %(start)s → %(end)s. "
                    "Reason: %(reason)s",
                    kind=kind,
                    start=rec.suspension_start,
                    end=rec.suspension_end or "-",
                    reason=rec.suspension_reason,
                )
            )
        return True

    @api.model
    def _cron_age_out_warnings(self):
        companies = self.env["res.company"].search([])
        for company in companies:
            days = company.masar_hr_warning_age_days or 365
            limit = fields.Date.context_today(self) - timedelta(days=days)
            # Include decided / awaiting_appeal — cases may sit there without close
            cases = self.search(
                [
                    ("company_id", "=", company.id),
                    ("state", "in", ("closed", "decided", "awaiting_appeal")),
                    ("sanction_aged", "=", False),
                    ("decision_date", "!=", False),
                    ("decision_date", "<=", fields.Datetime.to_datetime(limit)),
                    ("decided_sanction_id.sanction_kind", "in", ("notice", "warning")),
                ]
            )
            if cases:
                cases.write({"sanction_aged": True})
                for case in cases:
                    case.message_post(
                        body=_(
                            "Written notice/warning aged out after %(days)s days "
                            "(Art. 95).",
                            days=days,
                        )
                    )
        return True

# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrResignation(models.Model):
    _inherit = "hr.resignation"

    # Readable on certificate PDF even for hr.group_hr_user (wage is manager-gated).
    certificate_basic_wage = fields.Float(
        string="Certificate basic wage",
        compute="_compute_certificate_wage_info",
    )
    certificate_currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_certificate_wage_info",
    )

    @api.depends("employee_id", "company_id")
    def _compute_certificate_wage_info(self):
        for rec in self:
            emp = rec.employee_id.sudo()
            rec.certificate_basic_wage = emp.wage or 0.0
            rec.certificate_currency_id = (
                rec.company_id.currency_id or self.env.company.currency_id
            )

    def _masar_exit_checklist(self):
        """Soft exit reminders — no hard workflow. Returns list of note strings."""
        self.ensure_one()
        notes = []
        emp = self.employee_id
        last_day = self.approved_last_day or self.expected_last_day

        # Art. 37 — open leave overlapping last day (warning only by default)
        if "hr.leave" in self.env and last_day:
            Leave = self.env["hr.leave"]
            leave_domain = [
                ("employee_id", "=", emp.id),
                ("state", "=", "validate"),
                ("request_date_from", "<=", last_day),
                ("request_date_to", ">=", last_day),
            ]
            if Leave.search_count(leave_domain):
                notes.append(
                    _("Employee has validated leave overlapping the last day (Art. 37).")
                )

        # Open disciplinary case
        if "hr.disciplinary.case" in self.env:
            Case = self.env["hr.disciplinary.case"]
            open_states = [
                "submitted",
                "investigation",
                "awaiting_statement",
                "recommendation",
                "hr_review",
                "pending_approval",
                "awaiting_appeal",
                "appeal_review",
            ]
            if Case.search_count(
                [("employee_id", "=", emp.id), ("state", "in", open_states)]
            ):
                notes.append(_("Open disciplinary case — review before exit (Art. 37)."))

        # Open PPE allocations (optional module)
        if "hr.personal.equipment" in self.env:
            PPE = self.env["hr.personal.equipment"]
            open_ppe = PPE.search_count(
                [
                    ("employee_id", "=", emp.id),
                    ("state", "in", ("accepted", "valid")),
                ]
            )
            if open_ppe:
                notes.append(
                    _(
                        "%(count)s personal equipment item(s) still accepted/valid — "
                        "return or expire before archive.",
                        count=open_ppe,
                    )
                )

        # Exit document stubs (types seeded by this module)
        if "hr.employee.document" in self.env and "hr.employee.document.type" in self.env:
            Doc = self.env["hr.employee.document"]
            Type = self.env["hr.employee.document.type"]
            for code, label in (
                ("YE_CLEARANCE", _("Clearance (إخلاء الطرف)")),
                ("YE_SERVICE_CERT", _("Service certificate (م.41)")),
            ):
                dtype = Type.search([("code", "=", code)], limit=1)
                if not dtype:
                    continue
                if not Doc.search_count(
                    [
                        ("employee_id", "=", emp.id),
                        ("document_type_id", "=", dtype.id),
                    ]
                ):
                    notes.append(_("Missing exit document: %s") % label)

        if not emp.contract_date_start and not self.joining_date:
            notes.append(_("Joining / contract start date is empty."))

        return notes

    def _masar_ensure_exit_document_stubs(self):
        """Create empty clearance/certificate document rows if types exist — no force."""
        if "hr.employee.document" not in self.env:
            return
        Doc = self.env["hr.employee.document"]
        Type = self.env["hr.employee.document.type"]
        for rec in self:
            for code in ("YE_CLEARANCE", "YE_SERVICE_CERT"):
                dtype = Type.search([("code", "=", code)], limit=1)
                if not dtype:
                    continue
                exists = Doc.search_count(
                    [
                        ("employee_id", "=", rec.employee_id.id),
                        ("document_type_id", "=", dtype.id),
                    ]
                )
                if exists:
                    continue
                Doc.create(
                    {
                        "name": "%s / %s" % (code, rec.employee_id.name),
                        "employee_id": rec.employee_id.id,
                        "document_type_id": dtype.id,
                        "description": _(
                            "Stub created from resignation %s — attach signed file."
                        )
                        % rec.name,
                        "notification_type": "none",
                    }
                )

    def action_masar_exit_checklist(self):
        """Show soft checklist in chatter; never blocks."""
        for rec in self:
            notes = rec._masar_exit_checklist()
            if not notes:
                body = _("Exit checklist: nothing pending.")
            else:
                items = "".join("<li>%s</li>" % n for n in notes)
                body = _("Exit checklist (advisory):<ul>%s</ul>") % items
            rec.message_post(body=body)
        return True

    def action_confirm(self):
        res = super().action_confirm()
        self._masar_ensure_exit_document_stubs()
        for rec in self:
            notes = rec._masar_exit_checklist()
            if notes:
                items = "".join("<li>%s</li>" % n for n in notes)
                rec.message_post(
                    body=_("Exit reminders after confirm:<ul>%s</ul>") % items
                )
        return res

    def action_approve(self):
        for rec in self:
            notes = rec._masar_exit_checklist()
            strict = bool(rec.company_id.masar_hr_exit_strict)
            if notes and strict:
                raise UserError(
                    _(
                        "Exit checklist incomplete (strict mode is on):\n- %s\n"
                        "Turn off «Strict exit checklist» in Settings, or resolve items."
                    )
                    % "\n- ".join(notes)
                )
            if notes:
                items = "".join("<li>%s</li>" % n for n in notes)
                rec.message_post(
                    body=_("Approved with open exit items:<ul>%s</ul>") % items
                )
        return super().action_approve()

    def action_print_service_certificate(self):
        """Art. 41 — free service / end-of-relationship certificate."""
        self.ensure_one()
        return self.env.ref(
            "masar_hr_yemen.action_report_service_certificate"
        ).report_action(self)

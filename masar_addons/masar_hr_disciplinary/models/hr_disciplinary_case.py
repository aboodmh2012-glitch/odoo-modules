# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


LOCKED_STATES = frozenset(
    {"decided", "awaiting_appeal", "appeal_review", "closed"}
)

# Fields that may only change via _workflow_write (action methods).
WORKFLOW_PROTECTED = frozenset(
    {
        "state",
        "payroll_ready",
        "decided_sanction_id",
        "decision_notes",
        "decision_date",
        "decided_by_id",
        "appeal_deadline",
    }
)

CHATTER_FIELDS = frozenset(
    {
        "message_main_attachment_id",
        "message_follower_ids",
        "activity_ids",
    }
)


class HrDisciplinaryCase(models.Model):
    """Full disciplinary case lifecycle with server-side immutability."""

    _name = "hr.disciplinary.case"
    _description = "Disciplinary Case"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        tracking=True,
        index=True,
        check_company=True,
    )
    department_id = fields.Many2one(
        "hr.department",
        compute="_compute_department_id",
        store=True,
        readonly=False,
    )
    manager_id = fields.Many2one(
        "hr.employee",
        string="Line Manager",
        compute="_compute_manager_id",
        store=True,
        readonly=False,
    )
    incident_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    incident_summary = fields.Text(required=True)
    evidence_attachment_ids = fields.Many2many(
        "ir.attachment",
        "hr_disciplinary_case_evidence_rel",
        "case_id",
        "attachment_id",
        string="Evidence",
    )
    offense_type_id = fields.Many2one(
        "hr.discipline.offense.type",
        required=True,
        tracking=True,
        check_company=True,
    )
    policy_page_id = fields.Many2one(
        "document.page",
        string="Policy Article",
        related="offense_type_id.policy_page_id",
        store=True,
    )
    severity = fields.Selection(
        related="offense_type_id.severity",
        store=True,
    )
    prior_offense_count = fields.Integer(
        compute="_compute_prior_offense_count",
        store=True,
    )
    investigator_id = fields.Many2one(
        "res.users",
        tracking=True,
        domain="[('share', '=', False)]",
    )
    investigation_notes = fields.Html()
    employee_statement = fields.Text(
        string="Employee Statement",
        tracking=True,
    )
    statement_attachment_ids = fields.Many2many(
        "ir.attachment",
        "hr_disciplinary_case_statement_rel",
        "case_id",
        "attachment_id",
        string="Statement Attachments",
    )
    recommendation = fields.Text(tracking=True)
    recommended_sanction_id = fields.Many2one(
        "hr.discipline.sanction.type",
        tracking=True,
        check_company=True,
    )
    hr_review_notes = fields.Text()
    decided_sanction_id = fields.Many2one(
        "hr.discipline.sanction.type",
        tracking=True,
        check_company=True,
        copy=False,
    )
    decision_notes = fields.Text(copy=False)
    decision_date = fields.Datetime(copy=False)
    decided_by_id = fields.Many2one("res.users", copy=False)
    financial_amount = fields.Monetary(
        currency_field="currency_id",
        tracking=True,
        help="Approved financial penalty. Payroll may consume this only when "
        "payroll_ready is set (Phase 3 integration).",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        store=True,
    )
    payroll_ready = fields.Boolean(
        string="Ready for Payroll Deduction",
        copy=False,
        help="Set only after appeal window closes (or if appeals are disabled). "
        "Does not modify payslips by itself.",
    )
    appeal_allowed = fields.Boolean(
        related="offense_type_id.allows_appeal",
        store=True,
    )
    appeal_deadline = fields.Date(copy=False)
    appeal_text = fields.Text(copy=False)
    appeal_decision_notes = fields.Text(copy=False)
    appeal_outcome = fields.Selection(
        [
            ("rejected", "Appeal Rejected"),
            ("upheld", "Appeal Upheld / Overturned"),
        ],
        copy=False,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("investigation", "Investigation"),
            ("awaiting_statement", "Awaiting Employee Statement"),
            ("recommendation", "Recommendation"),
            ("hr_review", "HR Review"),
            ("pending_approval", "Pending Approval"),
            ("decided", "Decision Approved"),
            ("awaiting_appeal", "Awaiting Appeal"),
            ("appeal_review", "Appeal Review"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
    )
    amendment_reason = fields.Text(
        copy=False,
        help="Required reason when formally amending or cancelling a decided case.",
    )

    @api.depends("employee_id")
    def _compute_department_id(self):
        for rec in self:
            rec.department_id = rec.employee_id.department_id

    @api.depends("employee_id")
    def _compute_manager_id(self):
        for rec in self:
            rec.manager_id = rec.employee_id.parent_id

    @api.depends(
        "employee_id",
        "offense_type_id",
        "offense_type_id.escalation_enabled",
        "offense_type_id.recurrence_period_days",
        "incident_date",
    )
    def _compute_prior_offense_count(self):
        Case = self.env["hr.disciplinary.case"]
        for rec in self:
            if (
                not rec.employee_id
                or not rec.offense_type_id
                or not rec.offense_type_id.escalation_enabled
            ):
                rec.prior_offense_count = 0
                continue
            days = rec.offense_type_id.recurrence_period_days or 365
            start = (rec.incident_date or fields.Date.context_today(rec)) - timedelta(
                days=days
            )
            domain = [
                ("employee_id", "=", rec.employee_id.id),
                ("offense_type_id", "=", rec.offense_type_id.id),
                ("state", "in", list(LOCKED_STATES)),
                ("incident_date", ">=", start),
            ]
            if isinstance(rec.id, int):
                domain.append(("id", "!=", rec.id))
            rec.prior_offense_count = Case.search_count(domain)

    def _is_hr_officer(self):
        return self.env.user.has_group(
            "masar_hr_disciplinary.group_disciplinary_hr_officer"
        )

    def _is_investigator(self):
        return self.env.user.has_group(
            "masar_hr_disciplinary.group_disciplinary_investigator"
        )

    def _is_approver(self):
        return self.env.user.has_group(
            "masar_hr_disciplinary.group_disciplinary_approver"
        )

    def _employee_allowed_fields(self, state):
        if state == "awaiting_statement":
            return {"employee_statement", "statement_attachment_ids"}
        if state in ("awaiting_appeal", "decided"):
            return {"appeal_text"}
        return set()

    @api.model_create_multi
    def create(self, vals_list):
        if not self._is_hr_officer() and not self._is_investigator():
            # Line managers may create via their ACL; officers/investigators/managers
            if not self.env.user.has_group(
                "masar_hr_disciplinary.group_disciplinary_line_manager"
            ):
                raise AccessError(_("You are not allowed to create disciplinary cases."))
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = seq.next_by_code("hr.disciplinary.case") or _("New")
            bad = set(vals) & (WORKFLOW_PROTECTED - {"state"})
            if bad:
                raise UserError(
                    _("Cannot set protected fields on create: %s")
                    % ", ".join(sorted(bad))
                )
            if vals.get("state") and vals["state"] != "draft":
                raise UserError(_("New cases must start in draft."))
        return super().create(vals_list)

    def write(self, vals):
        """Public write: never accepts workflow-protected fields (use _workflow_write)."""
        protected = set(vals) & WORKFLOW_PROTECTED
        if protected:
            raise UserError(
                _(
                    "Field(s) %(fields)s can only be changed through workflow actions.",
                    fields=", ".join(sorted(protected)),
                )
            )

        is_officer = self._is_hr_officer()
        is_approver = self._is_approver()
        is_investigator = self._is_investigator()

        for rec in self:
            if rec.state in LOCKED_STATES:
                allowed = set(CHATTER_FIELDS) | {"amendment_reason"}
                if rec.state == "awaiting_appeal":
                    allowed |= {"appeal_text"}
                if rec.state == "appeal_review" and is_approver:
                    allowed |= {"appeal_decision_notes", "appeal_outcome"}
                forbidden = set(vals) - allowed
                if forbidden:
                    raise UserError(
                        _(
                            "Case %(name)s is %(state)s and cannot be edited directly. "
                            "Use a formal workflow action.",
                            name=rec.name,
                            state=rec.state,
                        )
                    )
                continue

            if not (is_officer or is_investigator or is_approver):
                allowed = self._employee_allowed_fields(rec.state) | CHATTER_FIELDS
                forbidden = set(vals) - allowed
                if forbidden:
                    raise AccessError(
                        _(
                            "You may only update: %(fields)s in state %(state)s.",
                            fields=", ".join(sorted(allowed - CHATTER_FIELDS)) or "-",
                            state=rec.state,
                        )
                    )
            elif rec.state not in ("draft", "submitted", "investigation", "recommendation", "hr_review", "pending_approval", "awaiting_statement"):
                # cancelled etc.
                if set(vals) - CHATTER_FIELDS - {"amendment_reason"}:
                    raise UserError(
                        _("Case %(name)s cannot be edited in state %(state)s.")
                        % {"name": rec.name, "state": rec.state}
                    )
        return super().write(vals)

    def _workflow_write(self, vals):
        """Trusted write used only by action methods (bypasses this model's write)."""
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state not in ("draft", "cancelled"):
                raise UserError(
                    _("Only draft or cancelled disciplinary cases can be deleted.")
                )
        return super().unlink()

    def _assert_state(self, allowed):
        for rec in self:
            if rec.state not in allowed:
                raise UserError(
                    _(
                        "Invalid transition for case %(name)s from state %(state)s.",
                        name=rec.name,
                        state=rec.state,
                    )
                )

    def _require_group(self, xmlid):
        if not self.env.user.has_group(xmlid):
            raise AccessError(_("You are not allowed to perform this action."))

    def _needs_finance(self):
        self.ensure_one()
        sanction = self.recommended_sanction_id or self.decided_sanction_id
        return bool(
            (sanction and sanction.has_financial_impact)
            or self.offense_type_id.has_financial_impact
        )

    def action_submit(self):
        self._require_group("masar_hr_disciplinary.group_disciplinary_hr_officer")
        self._assert_state({"draft"})
        for rec in self:
            if not rec.incident_summary:
                raise ValidationError(_("Provide an incident summary before submitting."))
        self._workflow_write({"state": "submitted"})
        return True

    def action_start_investigation(self):
        self._require_group("masar_hr_disciplinary.group_disciplinary_investigator")
        self._assert_state({"submitted", "investigation"})
        for rec in self:
            vals = {"state": "investigation"}
            if not rec.investigator_id:
                vals["investigator_id"] = self.env.user.id
            rec._workflow_write(vals)
        return True

    def action_request_statement(self):
        self._require_group("masar_hr_disciplinary.group_disciplinary_investigator")
        self._assert_state({"investigation", "submitted"})
        self._workflow_write({"state": "awaiting_statement"})
        for rec in self:
            if rec.employee_id.user_id:
                rec.activity_schedule(
                    "masar_hr_disciplinary.mail_act_disciplinary_statement",
                    user_id=rec.employee_id.user_id.id,
                    summary=_("Provide your statement for case %s") % rec.name,
                )
        return True

    def action_submit_statement(self):
        self._assert_state({"awaiting_statement"})
        for rec in self:
            is_employee = rec.employee_id.user_id == self.env.user
            is_officer = self._is_hr_officer()
            if not (is_employee or is_officer):
                raise AccessError(_("Only the employee (or HR) can submit the statement."))
            if not rec.employee_statement:
                raise UserError(_("Please enter your statement before submitting."))
            act_type = self.env.ref(
                "masar_hr_disciplinary.mail_act_disciplinary_statement",
                raise_if_not_found=False,
            )
            if act_type:
                rec.activity_ids.filtered(
                    lambda a, t=act_type: a.activity_type_id == t
                ).action_feedback(feedback=_("Statement submitted"))
        self._workflow_write({"state": "recommendation"})
        return True

    def action_submit_recommendation(self):
        self._require_group("masar_hr_disciplinary.group_disciplinary_investigator")
        self._assert_state({"recommendation", "investigation", "awaiting_statement"})
        for rec in self:
            if not rec.recommendation or not rec.recommended_sanction_id:
                raise UserError(
                    _("Recommendation text and recommended sanction are required.")
                )
            if (
                rec.recommended_sanction_id
                and rec.offense_type_id.sanction_type_ids
                and rec.recommended_sanction_id
                not in rec.offense_type_id.sanction_type_ids
            ):
                raise UserError(
                    _("Recommended sanction is not allowed for this offense type.")
                )
        self._workflow_write({"state": "hr_review"})
        return True

    def action_hr_review_done(self):
        self._require_group("masar_hr_disciplinary.group_disciplinary_hr_officer")
        self._assert_state({"hr_review"})
        self._workflow_write({"state": "pending_approval"})
        return True

    def _user_meets_approval_level(self, level):
        user = self.env.user
        if level == "officer":
            return user.has_group("masar_hr_disciplinary.group_disciplinary_hr_officer")
        if level == "manager":
            return user.has_group("masar_hr_disciplinary.group_disciplinary_hr_manager")
        return user.has_group("masar_hr_disciplinary.group_disciplinary_approver")

    def action_approve_decision(self):
        self._assert_state({"pending_approval"})
        for rec in self:
            level = rec.offense_type_id.approval_level
            sanction = rec.recommended_sanction_id
            if sanction and sanction.requires_approval_level:
                order = {"officer": 1, "manager": 2, "approver": 3}
                if order.get(sanction.requires_approval_level, 2) > order.get(level, 2):
                    level = sanction.requires_approval_level
            if not rec._user_meets_approval_level(level):
                raise AccessError(
                    _(
                        "Your role is not sufficient to approve this case "
                        "(required: %s)."
                    )
                    % level
                )
            if not sanction:
                raise UserError(_("A recommended sanction is required before approval."))
            amount = rec.financial_amount
            if rec._needs_finance() and amount <= 0:
                raise UserError(
                    _("This sanction requires a positive financial penalty amount.")
                )
            vals = {
                "decided_sanction_id": sanction.id,
                "decision_notes": rec.hr_review_notes or rec.recommendation,
                "decision_date": fields.Datetime.now(),
                "decided_by_id": self.env.user.id,
                "payroll_ready": False,
            }
            if rec.appeal_allowed:
                days = rec.offense_type_id.appeal_deadline_days or 7
                vals["appeal_deadline"] = fields.Date.context_today(rec) + timedelta(
                    days=days
                )
                vals["state"] = "awaiting_appeal"
            else:
                vals["state"] = "decided"
                if rec._needs_finance() and amount > 0:
                    vals["payroll_ready"] = True
            rec._workflow_write(vals)
            rec.message_post(
                body=_(
                    "Decision approved: %(sanction)s. Financial amount: %(amount)s",
                    sanction=sanction.display_name,
                    amount=amount or 0.0,
                )
            )
        return True

    def action_submit_appeal(self):
        self._assert_state({"awaiting_appeal", "decided"})
        for rec in self:
            is_employee = rec.employee_id.user_id == self.env.user
            if not is_employee and not self._is_hr_officer():
                raise AccessError(_("Only the employee can submit an appeal."))
            if not rec.appeal_allowed:
                raise UserError(_("Appeals are not allowed for this offense type."))
            if rec.appeal_deadline and fields.Date.context_today(rec) > rec.appeal_deadline:
                raise UserError(_("The appeal deadline has passed."))
            if not rec.appeal_text:
                raise UserError(_("Please enter the appeal text."))
        self._workflow_write({"state": "appeal_review"})
        return True

    def action_resolve_appeal(self):
        self._require_group("masar_hr_disciplinary.group_disciplinary_approver")
        self._assert_state({"appeal_review"})
        for rec in self:
            if not rec.appeal_decision_notes:
                raise UserError(_("Record the appeal decision notes before closing."))
            if not rec.appeal_outcome:
                raise UserError(_("Select the appeal outcome (rejected or upheld)."))
            if rec.appeal_outcome == "upheld":
                rec._workflow_write(
                    {
                        "state": "pending_approval",
                        "payroll_ready": False,
                        "decided_sanction_id": False,
                        "decision_date": False,
                        "decided_by_id": False,
                        "decision_notes": False,
                    }
                )
                rec.message_post(body=_("Appeal upheld — decision overturned for re-approval."))
            else:
                vals = {"state": "closed"}
                if rec._needs_finance() and rec.financial_amount > 0:
                    vals["payroll_ready"] = True
                rec._workflow_write(vals)
                rec.message_post(body=_("Appeal rejected — case closed."))
        return True

    def action_close(self):
        self._require_group("masar_hr_disciplinary.group_disciplinary_hr_officer")
        self._assert_state({"decided", "awaiting_appeal"})
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state == "awaiting_appeal":
                if rec.appeal_text:
                    raise UserError(_("An appeal was filed; resolve it instead."))
                if rec.appeal_deadline and today <= rec.appeal_deadline:
                    raise UserError(
                        _(
                            "Cannot close before the appeal deadline (%(deadline)s). "
                            "Wait for the employee to appeal or for the deadline to pass.",
                            deadline=rec.appeal_deadline,
                        )
                    )
            vals = {"state": "closed"}
            if rec._needs_finance() and rec.financial_amount > 0:
                vals["payroll_ready"] = True
            rec._workflow_write(vals)
        return True

    def action_cancel(self):
        self._require_group("masar_hr_disciplinary.group_disciplinary_hr_manager")
        for rec in self:
            if rec.state in LOCKED_STATES:
                if not rec.amendment_reason:
                    raise UserError(
                        _(
                            "Provide an amendment_reason before cancelling "
                            "a decided case."
                        )
                    )
            if rec.state == "cancelled":
                continue
            rec._workflow_write({"state": "cancelled", "payroll_ready": False})
        return True

    def action_formal_amend_open(self):
        """Re-open a decided case for formal amendment (auditable)."""
        self._require_group("masar_hr_disciplinary.group_disciplinary_approver")
        self._assert_state({"decided", "closed", "awaiting_appeal"})
        for rec in self:
            if not rec.amendment_reason:
                raise UserError(_("Amendment reason is required to re-open a case."))
            rec.message_post(body=_("Formal amendment: %s") % rec.amendment_reason)
            rec._workflow_write(
                {
                    "state": "pending_approval",
                    "payroll_ready": False,
                    "decided_sanction_id": False,
                    "decision_date": False,
                    "decided_by_id": False,
                    "decision_notes": False,
                    "appeal_text": False,
                    "appeal_decision_notes": False,
                    "appeal_outcome": False,
                    "appeal_deadline": False,
                }
            )
        return True

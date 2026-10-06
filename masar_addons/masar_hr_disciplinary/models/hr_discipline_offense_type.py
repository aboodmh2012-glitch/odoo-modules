# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrDisciplineOffenseType(models.Model):
    """Central regulation catalog for disciplinary offenses."""

    _name = "hr.discipline.offense.type"
    _description = "Disciplinary Offense Type"
    _order = "severity, name"
    _check_company_auto = True

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        index=True,
    )
    classification = fields.Selection(
        [
            ("attendance", "Attendance"),
            ("conduct", "Conduct"),
            ("performance", "Performance"),
            ("safety", "Safety"),
            ("policy", "Policy Violation"),
            ("other", "Other"),
        ],
        default="conduct",
        required=True,
    )
    severity = fields.Selection(
        [
            ("1", "Minor"),
            ("2", "Moderate"),
            ("3", "Major"),
            ("4", "Critical"),
        ],
        default="2",
        required=True,
        index=True,
    )
    policy_page_id = fields.Many2one(
        "document.page",
        string="Policy / Regulation Article",
        help="Link to the controlled policy article in Knowledge.",
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    description = fields.Html(translate=True)
    sanction_type_ids = fields.Many2many(
        "hr.discipline.sanction.type",
        "hr_discipline_offense_sanction_rel",
        "offense_id",
        "sanction_id",
        string="Possible Sanctions",
    )
    escalation_enabled = fields.Boolean(
        string="Track Recurrence",
        default=True,
        help="Count prior cases of this offense when recommending sanctions.",
    )
    recurrence_period_days = fields.Integer(
        default=365,
        help="Look-back window (days) when counting prior offenses.",
    )
    approval_level = fields.Selection(
        [
            ("officer", "HR Officer"),
            ("manager", "HR Manager"),
            ("approver", "Disciplinary Approver"),
        ],
        default="manager",
        required=True,
        help="Minimum role required to approve the final decision.",
    )
    requires_investigation = fields.Boolean(default=True)
    allows_appeal = fields.Boolean(default=True)
    appeal_deadline_days = fields.Integer(default=7)
    has_financial_impact = fields.Boolean(
        help="If set, a financial penalty amount can be recorded after decision.",
    )
    _code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "Offense code must be unique per company.",
    )

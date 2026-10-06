# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Yemen Labor Law–oriented defaults (Art. 93–98, 38, 28) — all configurable.
    masar_hr_discover_days = fields.Integer(
        string="Discipline: days to start after discovery",
        default=15,
        help="Art. 94/97: do not punish / start investigation after this many days "
        "from discovery_date.",
    )
    masar_hr_investigate_days = fields.Integer(
        string="Discipline: max investigation window (days)",
        default=30,
        help="Art. 97: finish investigation and apply sanction within this window.",
    )
    masar_hr_appeal_days_default = fields.Integer(
        string="Discipline: default appeal days",
        default=30,
        help="Art. 97(2): employee may appeal within this many days (default for "
        "new offense types).",
    )
    masar_hr_max_deduction_pct = fields.Float(
        string="Discipline: max deduction %% of basic wage",
        default=20.0,
        help="Art. 93(3): salary deduction cap as %% of basic wage.",
    )
    masar_hr_warning_age_days = fields.Integer(
        string="Discipline: written notice/warning age-out (days)",
        default=365,
        help="Art. 95: notice/warning considered spent after this many days.",
    )
    masar_hr_suspension_oral_days = fields.Integer(
        string="Discipline: oral precautionary suspension max (days)",
        default=5,
        help="Art. 98: verbal suspension for investigation — max 5 days.",
    )
    masar_hr_suspension_written_days = fields.Integer(
        string="Discipline: written precautionary suspension max (days)",
        default=30,
        help="Art. 98: written suspension — max 30 days.",
    )
    masar_hr_probation_max_days = fields.Integer(
        string="Probation maximum (days)",
        default=180,
        help="Art. 28: trial period must not exceed six months.",
    )
    masar_hr_probation_warn_days = fields.Integer(
        string="Probation reminder (days before end)",
        default=14,
    )
    masar_hr_annual_leave_days = fields.Float(
        string="Annual leave days per year",
        default=30.0,
        help="Art. 79: at least 30 days paid annual leave per year of service.",
    )
    masar_hr_annual_leave_per_month = fields.Float(
        string="Annual leave accrual per month",
        default=2.5,
        help="Art. 79: at least 2.5 days per month of actual service.",
    )
    masar_hr_casual_leave_days = fields.Float(
        string="Casual leave days per year",
        default=10.0,
        help="Art. 85: up to 10 days paid casual leave per year (employer grant).",
    )
    masar_hr_hajj_leave_days = fields.Float(
        string="Hajj leave days",
        default=20.0,
        help="Art. 84: 20 days once after four years of actual service.",
    )
    masar_hr_hajj_min_service_years = fields.Float(
        string="Hajj minimum service (years)",
        default=4.0,
    )
    masar_hr_maternity_days = fields.Integer(
        string="Maternity leave days",
        default=70,
        help="Art. 45 as amended by Law 15/2008: 70 days paid maternity leave "
        "(+20 for difficult birth or twins). NIC consolidated text may still "
        "show the pre-amendment 60 — company policy uses the amended figure.",
    )
    masar_hr_iddah_days = fields.Integer(
        string="Iddah leave days (paid)",
        default=40,
        help="Art. 87: 40 days paid on husband's death (+ up to 90 unpaid).",
    )
    masar_hr_exit_strict = fields.Boolean(
        string="Strict exit checklist",
        default=False,
        help="If enabled, resignation approval is blocked when the soft exit "
        "checklist still has open items (leave, discipline, PPE, exit docs). "
        "Default off — reminders only.",
    )
    masar_hr_auto_onboarding = fields.Boolean(
        string="Auto-launch onboarding on hire",
        default=True,
        help="When a recruitment applicant is turned into an employee, "
        "automatically launch the MASAR onboarding plan (documents, access, "
        "PPE, contract dates). Best-effort — never blocks hiring.",
    )

# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    masar_hr_discover_days = fields.Integer(
        related="company_id.masar_hr_discover_days", readonly=False
    )
    masar_hr_investigate_days = fields.Integer(
        related="company_id.masar_hr_investigate_days", readonly=False
    )
    masar_hr_appeal_days_default = fields.Integer(
        related="company_id.masar_hr_appeal_days_default", readonly=False
    )
    masar_hr_max_deduction_pct = fields.Float(
        related="company_id.masar_hr_max_deduction_pct", readonly=False
    )
    masar_hr_warning_age_days = fields.Integer(
        related="company_id.masar_hr_warning_age_days", readonly=False
    )
    masar_hr_suspension_oral_days = fields.Integer(
        related="company_id.masar_hr_suspension_oral_days", readonly=False
    )
    masar_hr_suspension_written_days = fields.Integer(
        related="company_id.masar_hr_suspension_written_days", readonly=False
    )
    masar_hr_probation_max_days = fields.Integer(
        related="company_id.masar_hr_probation_max_days", readonly=False
    )
    masar_hr_probation_warn_days = fields.Integer(
        related="company_id.masar_hr_probation_warn_days", readonly=False
    )
    masar_hr_annual_leave_days = fields.Float(
        related="company_id.masar_hr_annual_leave_days", readonly=False
    )
    masar_hr_annual_leave_per_month = fields.Float(
        related="company_id.masar_hr_annual_leave_per_month", readonly=False
    )
    masar_hr_casual_leave_days = fields.Float(
        related="company_id.masar_hr_casual_leave_days", readonly=False
    )
    masar_hr_hajj_leave_days = fields.Float(
        related="company_id.masar_hr_hajj_leave_days", readonly=False
    )
    masar_hr_hajj_min_service_years = fields.Float(
        related="company_id.masar_hr_hajj_min_service_years", readonly=False
    )
    masar_hr_maternity_days = fields.Integer(
        related="company_id.masar_hr_maternity_days", readonly=False
    )
    masar_hr_iddah_days = fields.Integer(
        related="company_id.masar_hr_iddah_days", readonly=False
    )
    masar_hr_exit_strict = fields.Boolean(
        related="company_id.masar_hr_exit_strict", readonly=False
    )
    masar_hr_auto_onboarding = fields.Boolean(
        related="company_id.masar_hr_auto_onboarding", readonly=False
    )

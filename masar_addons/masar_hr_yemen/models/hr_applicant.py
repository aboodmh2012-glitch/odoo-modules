# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    def create_employee_from_applicant(self):
        """Standard recruitment hire, then launch the MASAR onboarding plan.

        Best-effort: any failure to launch the plan is logged and swallowed so
        it can never block turning an applicant into an employee.
        """
        res = super().create_employee_from_applicant()
        for applicant in self:
            company = applicant.company_id or self.env.company
            if not company.masar_hr_auto_onboarding:
                continue
            employee = applicant.emp_id if "emp_id" in applicant._fields else False
            if not employee:
                continue
            try:
                applicant._masar_launch_onboarding(employee)
            except Exception:  # pragma: no cover - never block hiring
                _logger.warning(
                    "MASAR: onboarding launch failed for applicant %s",
                    applicant.display_name,
                    exc_info=True,
                )
        return res

    def _masar_plan_user(self, template, employee):
        """Resolve the responsible user for a plan template, HR-friendly."""
        self.ensure_one()
        rtype = template.responsible_type or "on_demand"
        if rtype == "employee":
            return employee.user_id
        if rtype == "coach":
            return employee.coach_id.user_id if employee.coach_id else self.env.user
        if rtype == "manager":
            return employee.parent_id.user_id if employee.parent_id else self.env.user
        if rtype == "other":
            responsible = getattr(template, "responsible_id", False)
            return responsible or self.env.user
        # on_demand / anything else: default to the HR user doing the hire.
        return self.env.user

    def _masar_launch_onboarding(self, employee):
        """Schedule the onboarding plan's templates as activities on the employee.

        Uses the stable activity_schedule API (not the plan wizard, whose fields
        vary across versions) so the link is robust.
        """
        self.ensure_one()
        plan = self.env.ref(
            "masar_hr_yemen.plan_masar_onboarding", raise_if_not_found=False
        )
        if not plan or not employee:
            return
        templates = plan.template_ids if "template_ids" in plan._fields else []
        today = fields.Date.context_today(self)
        for template in templates:
            try:
                user = self._masar_plan_user(template, employee)
                if not user:
                    continue
                deadline = today
                delay = template.delay_count or 0
                if delay and (template.delay_unit or "days") == "days":
                    deadline = today + timedelta(days=delay)
                act_values = {
                    "summary": template.summary or _("Onboarding step"),
                    "note": template.note or False,
                    "user_id": user.id,
                    "date_deadline": deadline,
                }
                if template.activity_type_id:
                    act_values["activity_type_id"] = template.activity_type_id.id
                employee.activity_schedule(
                    "mail.mail_activity_data_todo", **act_values
                )
            except Exception:  # pragma: no cover - one bad template must not stop the rest
                _logger.warning(
                    "MASAR: onboarding template %s failed for %s",
                    template.id,
                    employee.display_name,
                    exc_info=True,
                )

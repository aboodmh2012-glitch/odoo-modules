# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import fields, models, _
from odoo.exceptions import UserError


class DocumentPageDistributeWizard(models.TransientModel):
    _name = "document.page.distribute.wizard"
    _description = "Distribute Controlled Document"

    page_id = fields.Many2one("document.page", required=True)
    history_id = fields.Many2one("document.page.history", required=True)
    department_ids = fields.Many2many("hr.department", string="Departments")
    user_ids = fields.Many2many("res.users", string="Users")
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    partner_ids = fields.Many2many("res.partner", string="Partners")
    due_date = fields.Date(
        default=lambda self: fields.Date.context_today(self) + timedelta(days=14)
    )
    create_activity = fields.Boolean(default=True)

    def action_distribute(self):
        self.ensure_one()
        if not self.history_id:
            raise UserError(_("Select a published version."))
        partners = self.partner_ids
        for user in self.user_ids:
            partners |= user.partner_id
        for emp in self.employee_ids:
            if emp.work_contact_id:
                partners |= emp.work_contact_id
            elif emp.user_id:
                partners |= emp.user_id.partner_id
        if self.department_ids:
            emps = self.env["hr.employee"].search(
                [("department_id", "child_of", self.department_ids.ids)]
            )
            for emp in emps:
                if emp.work_contact_id:
                    partners |= emp.work_contact_id
                elif emp.user_id:
                    partners |= emp.user_id.partner_id
        partners = partners.filtered(lambda p: p)
        if not partners:
            raise UserError(_("Select at least one recipient."))

        Distribution = self.env["document.page.distribution"]
        created = Distribution
        for partner in partners:
            existing = Distribution.search(
                [
                    ("history_id", "=", self.history_id.id),
                    ("partner_id", "=", partner.id),
                ],
                limit=1,
            )
            if existing:
                continue
            user = partner.user_ids[:1]
            employee = self.env["hr.employee"].search(
                [("work_contact_id", "=", partner.id)], limit=1
            ) or self.env["hr.employee"].search(
                [("user_id", "in", partner.user_ids.ids)], limit=1
            )
            line = Distribution.create(
                {
                    "page_id": self.page_id.id,
                    "history_id": self.history_id.id,
                    "partner_id": partner.id,
                    "user_id": user.id if user else False,
                    "employee_id": employee.id if employee else False,
                    "department_id": employee.department_id.id if employee else False,
                    "due_date": self.due_date,
                    "state": "pending",
                    "acknowledgment_text": self.page_id.kc_ack_confirmation_text,
                }
            )
            created |= line
        if self.create_activity and created:
            created.action_send_reminder()
        return {
            "type": "ir.actions.act_window",
            "name": _("Distributions"),
            "res_model": "document.page.distribution",
            "view_mode": "list,form",
            "domain": [("id", "in", created.ids)],
        }

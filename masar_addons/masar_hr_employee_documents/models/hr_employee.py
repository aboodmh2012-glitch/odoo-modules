# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    document_ids = fields.One2many("hr.employee.document", "employee_id")
    document_count = fields.Integer(compute="_compute_document_stats")
    entry_checklist_progress = fields.Float(
        string="Entry Checklist %", compute="_compute_document_stats"
    )
    exit_checklist_progress = fields.Float(
        string="Exit Checklist %", compute="_compute_document_stats"
    )

    def _compute_document_stats(self):
        Doc = self.env["hr.employee.document"]
        Type = self.env["hr.employee.document.type"]
        for emp in self:
            docs = Doc.search([("employee_id", "=", emp.id)])
            emp.document_count = len(docs)
            for kind, field in (
                ("entry", "entry_checklist_progress"),
                ("exit", "exit_checklist_progress"),
            ):
                types = Type.search([("checklist_kind", "=", kind), ("active", "=", True)])
                if not types:
                    setattr(emp, field, 0.0)
                    continue
                covered = types.filtered(
                    lambda t, d=docs: d.filtered(lambda x: x.document_type_id == t)
                )
                setattr(emp, field, 100.0 * len(covered) / len(types))

    def action_view_employee_documents(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Documents",
            "res_model": "hr.employee.document",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }

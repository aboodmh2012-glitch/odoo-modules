# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Per-version distribution and acknowledgment (auditable)."""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DocumentPageDistribution(models.Model):
    _name = "document.page.distribution"
    _description = "Controlled Document Distribution"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _check_company_auto = True

    page_id = fields.Many2one(
        "document.page",
        required=True,
        ondelete="cascade",
        index=True,
    )
    history_id = fields.Many2one(
        "document.page.history",
        string="Document version",
        required=True,
        ondelete="restrict",
        index=True,
        help="Acknowledgment applies only to this exact version snapshot.",
    )
    company_id = fields.Many2one(
        related="page_id.company_id",
        store=True,
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Recipient",
        required=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        index=True,
        help="Optional portal/internal user linked to the recipient.",
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", index=True)
    department_id = fields.Many2one("hr.department", string="Department")
    state = fields.Selection(
        [
            ("pending", "Assigned / Pending"),
            ("viewed", "Opened in Odoo"),
            ("acknowledged", "Acknowledged"),
            ("overdue", "Overdue"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
        required=True,
        tracking=True,
        index=True,
        help="Honest evidence states: Assigned does not mean email Delivered; "
        "Opened does not mean Acknowledged.",
    )
    assigned_date = fields.Datetime(default=fields.Datetime.now, required=True)
    due_date = fields.Date()
    viewed_date = fields.Datetime(readonly=True, copy=False)
    acknowledged_date = fields.Datetime(readonly=True, copy=False)
    reminder_count = fields.Integer(default=0, copy=False)
    version_label = fields.Char(related="history_id.kc_version_label", store=True)
    page_name = fields.Char(related="page_id.name", store=True)
    acknowledgment_text = fields.Text(
        string="Confirmation text (snapshot)",
        readonly=True,
        copy=False,
        help="Exact wording shown/agreed at acknowledgment time.",
    )
    acknowledgment_method = fields.Selection(
        [
            ("ui_button", "UI acknowledge button"),
            ("portal", "Portal"),
            ("import", "Import / migration"),
        ],
        default="ui_button",
        copy=False,
    )

    _partner_version_uniq = models.Constraint(
        "UNIQUE(history_id, partner_id)",
        "This recipient already has a distribution line for this version.",
    )

    def action_mark_viewed(self):
        for rec in self.filtered(lambda r: r.state in ("pending", "overdue")):
            rec.write({"state": "viewed", "viewed_date": fields.Datetime.now()})
        return True

    def action_acknowledge(self):
        for rec in self:
            if rec.state == "cancelled":
                raise UserError(_("Cancelled distributions cannot be acknowledged."))
            text = rec.acknowledgment_text or rec.page_id.kc_ack_confirmation_text
            rec.write(
                {
                    "state": "acknowledged",
                    "acknowledged_date": fields.Datetime.now(),
                    "viewed_date": rec.viewed_date or fields.Datetime.now(),
                    "acknowledgment_text": text,
                    "acknowledgment_method": "ui_button",
                }
            )
            rec.message_post(
                body=_(
                    "Acknowledged version %(ver)s of «%(doc)s».",
                    ver=rec.version_label or rec.history_id.display_name,
                    doc=rec.page_id.name,
                )
            )
        return True

    def action_send_reminder(self):
        ack_type = self.env.ref(
            "knowledge_control.mail_activity_kc_acknowledge", raise_if_not_found=False
        )
        for rec in self.filtered(lambda r: r.state in ("pending", "viewed", "overdue")):
            user = rec.user_id
            if not user and rec.partner_id.user_ids:
                user = rec.partner_id.user_ids[:1]
            if not user:
                continue
            # Idempotent: never stack a second open acknowledgment activity for
            # the same recipient. _cron_mark_overdue calls this daily, so without
            # this guard every overdue distribution would grow a new to-do each
            # run. Odoo removes an activity once it is marked done, so a genuinely
            # outstanding acknowledgment is reminded exactly once at a time.
            already = rec.activity_ids.filtered(
                lambda a: a.user_id.id == user.id
                and (not ack_type or a.activity_type_id.id == ack_type.id)
            )
            if already:
                continue
            rec.activity_schedule(
                "knowledge_control.mail_activity_kc_acknowledge",
                user_id=user.id,
                summary=_("Acknowledge: %s (%s)", rec.page_id.name, rec.version_label),
            )
            rec.reminder_count += 1
        return True

    @api.model
    def _cron_mark_overdue(self):
        today = fields.Date.context_today(self)
        overdue = self.search(
            [
                ("state", "in", ("pending", "viewed")),
                ("due_date", "!=", False),
                ("due_date", "<", today),
            ]
        )
        overdue.write({"state": "overdue"})
        overdue.action_send_reminder()

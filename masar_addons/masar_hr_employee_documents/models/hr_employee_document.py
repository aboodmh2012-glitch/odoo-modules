# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployeeDocument(models.Model):
    _name = "hr.employee.document"
    _description = "Employee Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "expiry_date, id desc"
    _check_company_auto = True

    name = fields.Char(string="Document Number", required=True, tracking=True)
    employee_id = fields.Many2one(
        "hr.employee", required=True, index=True, tracking=True, check_company=True
    )
    company_id = fields.Many2one(
        "res.company",
        related="employee_id.company_id",
        store=True,
        index=True,
    )
    document_type_id = fields.Many2one(
        "hr.employee.document.type", required=True, tracking=True, check_company=True
    )
    issue_date = fields.Date(default=fields.Date.context_today)
    expiry_date = fields.Date(tracking=True)
    description = fields.Text()
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "hr_employee_document_attachment_rel",
        "document_id",
        "attachment_id",
        string="Attachments",
    )
    notification_type = fields.Selection(
        [
            ("none", "No Notification"),
            ("on_expiry", "On Expiry Date"),
            ("before_days", "On Expiry and Before Days"),
            ("daily_until", "Daily Until Expiry"),
            ("daily_after", "Daily On and After Expiry"),
        ],
        default="before_days",
        required=True,
    )
    before_days = fields.Integer(default=30)
    state = fields.Selection(
        [
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
            ("no_expiry", "No Expiry"),
        ],
        compute="_compute_state",
        store=True,
    )
    last_reminder_date = fields.Date(copy=False)
    is_confidential = fields.Boolean(
        string="Confidential (HR only)",
        default=False,
        tracking=True,
        help="When set, this document is hidden from the employee's own portal "
        "and is visible only to HR. Use for disciplinary, medical or "
        "investigation files.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "is_confidential" not in vals and vals.get("document_type_id"):
                dtype = self.env["hr.employee.document.type"].browse(
                    vals["document_type_id"]
                )
                if dtype.confidential_default:
                    vals["is_confidential"] = True
        return super().create(vals_list)

    @api.depends("expiry_date", "before_days")
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.expiry_date:
                rec.state = "no_expiry"
            elif rec.expiry_date < today:
                rec.state = "expired"
            elif rec.expiry_date <= today + timedelta(days=rec.before_days or 0):
                rec.state = "expiring_soon"
            else:
                rec.state = "valid"

    @api.constrains("expiry_date", "document_type_id")
    def _check_requires_expiry(self):
        for rec in self:
            if rec.document_type_id.requires_expiry and not rec.expiry_date:
                raise ValidationError(
                    _("Document type %s requires an expiry date.")
                    % rec.document_type_id.display_name
                )

    def _should_notify_today(self):
        self.ensure_one()
        if not self.expiry_date or self.notification_type == "none":
            return False
        today = fields.Date.context_today(self)
        if self.last_reminder_date == today:
            return False
        days = self.before_days or 0
        expiry = self.expiry_date
        if self.notification_type == "on_expiry":
            return today == expiry
        if self.notification_type == "before_days":
            return today in {expiry, expiry - timedelta(days=days)}
        if self.notification_type == "daily_until":
            return expiry - timedelta(days=days) <= today <= expiry
        if self.notification_type == "daily_after":
            return expiry <= today <= expiry + timedelta(days=days)
        return False

    @api.model
    def _cron_document_expiry_reminders(self):
        docs = self.search(
            [("expiry_date", "!=", False), ("notification_type", "!=", "none")]
        )
        today = fields.Date.context_today(self)
        hr_group = self.env.ref("hr.group_hr_user")
        # Prefetch once; filter per document company below
        hr_users_all = hr_group.user_ids.filtered(lambda u: u.active and not u.share)
        for doc in docs:
            if not doc._should_notify_today():
                continue
            body = _(
                "Document %(doc)s for %(employee)s expires on %(date)s.",
                doc=doc.name,
                employee=doc.employee_id.name,
                date=doc.expiry_date,
            )
            company = doc.company_id
            hr_users = hr_users_all.filtered(
                lambda u, c=company: not c or c in u.company_ids
            )[:3]
            # One activity per document to the first matching HR user
            if hr_users:
                existing = doc.activity_ids.filtered(
                    lambda a: a.summary and a.summary.startswith("Document expiry:")
                )
                if not existing:
                    doc.activity_schedule(
                        "mail.mail_activity_data_todo",
                        user_id=hr_users[0].id,
                        summary=_("Document expiry: %s") % doc.name,
                        note=body,
                    )
            if doc.employee_id.work_email:
                self.env["mail.mail"].sudo().create(
                    {
                        "subject": _("Document expiry reminder: %s") % doc.name,
                        "body_html": f"<p>{body}</p>",
                        "email_to": doc.employee_id.work_email,
                        "auto_delete": True,
                    }
                ).send()
            doc.last_reminder_date = today
        return True

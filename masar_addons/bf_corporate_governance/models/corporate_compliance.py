# -*- coding: utf-8 -*-
# Copyright (c) 2026 Les services de consultation Blue Fox, Inc.
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later
from datetime import timedelta

from odoo import api, fields, models


class CorporateComplianceEvent(models.Model):
    _name = "corporate.compliance.event"
    _description = "Corporate Compliance Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "due_date asc"

    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
    )
    event_type = fields.Selection(
        selection=[
            ("annual_declaration", "Annual declaration / filing"),
            ("agm", "Annual general meeting"),
            ("director_election", "Director election"),
            ("auditor_appointment", "Auditor appointment"),
            ("financial_approval", "Financial approval"),
            ("bylaw_review", "Bylaw / articles review"),
            ("other", "Other"),
        ],
        string="Event type",
        required=True,
        tracking=True,
    )
    fiscal_year = fields.Char(
        string="Fiscal year",
        tracking=True,
    )
    due_date = fields.Date(
        string="Due date",
        required=True,
        tracking=True,
    )
    completed_date = fields.Date(
        string="Completed on",
        tracking=True,
    )
    status = fields.Selection(
        selection=[
            ("upcoming", "Upcoming"),
            ("due_soon", "Due soon"),
            ("overdue", "Overdue"),
            ("completed", "Completed"),
        ],
        string="Status",
        compute="_compute_status",
        store=True,
        index=True,
    )
    resolution_id = fields.Many2one(
        "corporate.resolution",
        string="Related resolution",
    )
    filing_reference = fields.Char(
        string="Filing reference",
        help="Jurisdiction-agnostic filing / confirmation number "
             "(regulator receipt, registry reference, etc.).",
    )
    notes = fields.Text(string="Notes")
    reminder_sent = fields.Boolean(
        string="Reminder recorded",
        default=False,
        help="Set when a reminder activity was created for the current due_date. "
             "Cleared automatically when due_date changes so a new cycle can run.",
    )
    reminder_due_date = fields.Date(
        string="Reminded for due date",
        help="Due date value for which reminder_sent applies. Used for "
             "idempotent cron retries without duplicate activities.",
        copy=False,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    @api.depends("due_date", "completed_date")
    def _compute_status(self):
        today = fields.Date.today()
        for rec in self:
            if rec.completed_date:
                rec.status = "completed"
            elif not rec.due_date:
                rec.status = "upcoming"
            elif rec.due_date < today:
                rec.status = "overdue"
            elif rec.due_date <= today + timedelta(days=30):
                rec.status = "due_soon"
            else:
                rec.status = "upcoming"

    def write(self, vals):
        if "due_date" in vals:
            # New schedule → allow a fresh reminder cycle.
            vals = dict(vals)
            vals.setdefault("reminder_sent", False)
            vals.setdefault("reminder_due_date", False)
        return super().write(vals)

    def action_complete(self):
        self.write({"completed_date": fields.Date.today()})

    def action_reset(self):
        self.write({
            "completed_date": False,
            "reminder_sent": False,
            "reminder_due_date": False,
        })

    def _has_open_compliance_activity(self, user):
        """True if an open todo activity already exists for this event+user."""
        self.ensure_one()
        Activity = self.env["mail.activity"]
        return bool(Activity.search_count([
            ("res_model", "=", self._name),
            ("res_id", "=", self.id),
            ("user_id", "=", user.id),
            ("activity_type_id", "=", self.env.ref("mail.mail_activity_data_todo").id),
        ]))

    @api.model
    def _cron_check_compliance_deadlines(self):
        """Daily reminder cron — idempotent across retries and due_date resets."""
        today = fields.Date.today()
        events = self.search([
            ("completed_date", "=", False),
            ("due_date", "<=", today + timedelta(days=30)),
        ])
        manager_group = self.env.ref(
            "bf_corporate_governance.group_corporate_manager",
            raise_if_not_found=False,
        )
        if not manager_group:
            return

        for event in events:
            # Skip if we already reminded for this exact due_date.
            if (
                event.reminder_sent
                and event.reminder_due_date
                and event.reminder_due_date == event.due_date
            ):
                continue

            days_until = (event.due_date - today).days
            if days_until <= 0:
                priority = "3"
                label = "OVERDUE"
            elif days_until <= 7:
                priority = "2"
                label = f"{days_until} days"
            elif days_until <= 14:
                priority = "1"
                label = f"{days_until} days"
            else:
                priority = "0"
                label = f"{days_until} days"

            for user in manager_group.all_user_ids:
                if event._has_open_compliance_activity(user):
                    continue
                event.activity_schedule(
                    "mail.mail_activity_data_todo",
                    date_deadline=event.due_date,
                    user_id=user.id,
                    note=(
                        f"<p><strong>Corporate compliance ({label})</strong></p>"
                        f"<p>{event.name} — due {event.due_date}</p>"
                    ),
                )
            event.write({
                "reminder_sent": True,
                "reminder_due_date": event.due_date,
            })

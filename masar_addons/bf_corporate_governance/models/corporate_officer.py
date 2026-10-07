# -*- coding: utf-8 -*-
# Copyright (c) 2026 Les services de consultation Blue Fox, Inc.
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later
from odoo import api, fields, models


class CorporateOfficer(models.Model):
    _name = "corporate.officer"
    _description = "Corporate Officer"
    _inherit = ["mail.thread"]
    _order = "is_active desc, appointment_date desc"

    partner_id = fields.Many2one(
        "res.partner",
        string="Officer",
        required=True,
        tracking=True,
    )
    # Optional bridge to the operational HR record (Governance = appointment SSOT).
    employee_id = fields.Many2one(
        "hr.employee",
        string="Linked Employee",
        tracking=True,
        help="Optional link to the HR employee record for this officer "
        "(e.g. CEO). Does not duplicate name or job title.",
    )
    title = fields.Selection(
        selection=[
            ("president", "President"),
            ("vice_president", "Vice President"),
            ("secretary", "Secretary"),
            ("treasurer", "Treasurer"),
            ("director_general", "Managing Director / CEO"),
            ("other", "Other"),
        ],
        string="Title",
        required=True,
        tracking=True,
    )
    title_custom = fields.Char(
        string="Custom title",
    )
    appointment_date = fields.Date(
        string="Appointment date",
        required=True,
        tracking=True,
    )
    end_date = fields.Date(
        string="End date",
        tracking=True,
    )
    appointment_resolution_id = fields.Many2one(
        "corporate.resolution",
        string="Appointment resolution",
    )
    is_active = fields.Boolean(
        string="Active",
        compute="_compute_is_active",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    @api.depends("end_date")
    def _compute_is_active(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_active = not rec.end_date or rec.end_date > today

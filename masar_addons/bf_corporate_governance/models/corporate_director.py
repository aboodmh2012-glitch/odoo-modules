# -*- coding: utf-8 -*-
# Copyright (c) 2026 Les services de consultation Blue Fox, Inc.
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later
from odoo import api, fields, models


class CorporateDirector(models.Model):
    _name = "corporate.director"
    _description = "Corporate Director"
    _inherit = ["mail.thread"]
    _order = "is_active desc, appointment_date desc"

    partner_id = fields.Many2one(
        "res.partner",
        string="Director",
        required=True,
        tracking=True,
    )
    board_role = fields.Selection(
        selection=[
            ("chair", "Chair"),
            ("vice_chair", "Vice Chair"),
            ("member", "Member"),
        ],
        string="Board role",
        default="member",
        required=True,
        tracking=True,
        help="Role on the board of directors. Secretary is NOT a board role — "
        "it is an operational/security responsibility (Governance / Board "
        "Secretary group).",
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
    end_reason = fields.Selection(
        selection=[
            ("resignation", "Resignation"),
            ("removal", "Removal"),
            ("term_expired", "Term expired"),
            ("other", "Other"),
        ],
        string="End reason",
    )
    appointment_resolution_id = fields.Many2one(
        "corporate.resolution",
        string="Appointment resolution",
    )
    end_resolution_id = fields.Many2one(
        "corporate.resolution",
        string="End resolution",
    )
    domicile = fields.Char(
        string="Address / domicile",
        help="Optional registered address for the director "
             "(jurisdiction-configurable; not hard-coded to a statute).",
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

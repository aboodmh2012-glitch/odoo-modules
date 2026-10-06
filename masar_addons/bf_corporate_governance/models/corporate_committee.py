# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import api, fields, models


class CorporateCommittee(models.Model):
    _name = "corporate.committee"
    _description = "Board Committee"
    _inherit = ["mail.thread"]
    _order = "is_active desc, name"

    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    committee_type = fields.Selection(
        selection=[
            ("audit", "Audit"),
            ("risk", "Risk"),
            ("compliance", "Compliance"),
            ("risk_compliance", "Risk & Compliance"),
            ("nomination", "Nomination & Remuneration"),
            ("other", "Other"),
        ],
        required=True,
        tracking=True,
    )
    effective_date = fields.Date(tracking=True)
    end_date = fields.Date(tracking=True)
    is_active = fields.Boolean(
        compute="_compute_is_active",
        store=True,
        index=True,
    )
    charter = fields.Html(string="Charter / Terms of Reference")
    resolution_id = fields.Many2one(
        "corporate.resolution",
        string="Related Board Resolution",
    )
    member_ids = fields.One2many(
        "corporate.committee.member",
        "committee_id",
        string="Members",
    )
    chairperson_id = fields.Many2one(
        "res.partner",
        string="Chairperson",
        compute="_compute_officers",
        store=True,
    )
    secretary_id = fields.Many2one(
        "res.partner",
        string="Secretary",
        compute="_compute_officers",
        store=True,
    )

    @api.depends("end_date")
    def _compute_is_active(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_active = not rec.end_date or rec.end_date > today

    @api.depends(
        "member_ids.role",
        "member_ids.partner_id",
        "member_ids.is_active",
    )
    def _compute_officers(self):
        for rec in self:
            active = rec.member_ids.filtered("is_active")
            chair = active.filtered(lambda m: m.role == "chair")[:1]
            secretary = active.filtered(lambda m: m.role == "secretary")[:1]
            rec.chairperson_id = chair.partner_id if chair else False
            rec.secretary_id = secretary.partner_id if secretary else False


class CorporateCommitteeMember(models.Model):
    _name = "corporate.committee.member"
    _description = "Board Committee Member"
    _inherit = ["mail.thread"]
    _order = "is_active desc, appointment_date desc"

    committee_id = fields.Many2one(
        "corporate.committee",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Member",
        required=True,
        tracking=True,
    )
    role = fields.Selection(
        selection=[
            ("chair", "Chair"),
            ("member", "Member"),
            ("secretary", "Secretary"),
            ("observer", "Observer"),
        ],
        required=True,
        default="member",
        tracking=True,
    )
    appointment_date = fields.Date(required=True, tracking=True)
    end_date = fields.Date(tracking=True)
    appointment_resolution_id = fields.Many2one(
        "corporate.resolution",
        string="Appointment Resolution",
    )
    is_active = fields.Boolean(
        compute="_compute_is_active",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="committee_id.company_id",
        store=True,
        index=True,
    )

    @api.depends("end_date", "committee_id.is_active")
    def _compute_is_active(self):
        today = fields.Date.today()
        for rec in self:
            committee_ok = bool(rec.committee_id and rec.committee_id.is_active)
            member_ok = not rec.end_date or rec.end_date > today
            rec.is_active = committee_ok and member_ok

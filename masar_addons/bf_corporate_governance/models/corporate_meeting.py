# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CorporateMeeting(models.Model):
    _name = "corporate.meeting"
    _description = "Board / Committee Meeting"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(string="Subject", required=True, tracking=True)
    reference = fields.Char(
        string="Reference", readonly=True, copy=False, default="New", index=True
    )
    meeting_type = fields.Selection(
        selection=[("board", "Board"), ("committee", "Committee")],
        required=True,
        default="board",
        tracking=True,
    )
    committee_id = fields.Many2one(
        "corporate.committee",
        string="Committee",
        tracking=True,
        help="Required for committee meetings.",
    )
    date = fields.Datetime(string="Date / Time", required=True, tracking=True)
    meeting_mode = fields.Selection(
        selection=[
            ("in_person", "In person"),
            ("remote", "Remote"),
            ("hybrid", "Hybrid"),
        ],
        default="in_person",
        required=True,
        tracking=True,
    )
    location = fields.Char(string="Location")
    agenda = fields.Html(string="Agenda")
    chairperson_id = fields.Many2one("res.partner", string="Chairperson", tracking=True)
    attendance_ids = fields.One2many(
        "corporate.meeting.attendance", "meeting_id", string="Attendance"
    )
    quorum_achieved = fields.Boolean(string="Quorum achieved", tracking=True)
    minutes = fields.Html(string="Minutes")
    minutes_page_id = fields.Many2one(
        "document.page",
        string="Minutes (Knowledge page)",
        help="Optional link to a Minute Book / Knowledge page. The frozen "
        "controlled version pinned on a resolution remains the legal evidence.",
    )
    resolution_ids = fields.One2many(
        "corporate.resolution", "meeting_id", string="Resolutions"
    )
    resolution_count = fields.Integer(
        compute="_compute_resolution_count", string="Resolutions"
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("held", "Held"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    @api.depends("resolution_ids")
    def _compute_resolution_count(self):
        for rec in self:
            rec.resolution_count = len(rec.resolution_ids)

    @api.constrains("meeting_type", "committee_id")
    def _check_committee(self):
        for rec in self:
            if rec.meeting_type == "committee" and not rec.committee_id:
                raise ValidationError(
                    _("A committee meeting must reference a committee.")
                )

    @api.onchange("meeting_type")
    def _onchange_meeting_type(self):
        if self.meeting_type == "board":
            self.committee_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("reference", "New") == "New":
                vals["reference"] = (
                    self.env["ir.sequence"].next_by_code("corporate.meeting")
                    or "New"
                )
        return super().create(vals_list)

    def action_schedule(self):
        self.write({"state": "scheduled"})

    def action_mark_held(self):
        self.write({"state": "held"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_draft(self):
        self.write({"state": "draft"})

    def action_open_resolutions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Resolutions"),
            "res_model": "corporate.resolution",
            "view_mode": "list,form",
            "domain": [("meeting_id", "=", self.id)],
            "context": {"default_meeting_id": self.id},
        }


class CorporateMeetingAttendance(models.Model):
    _name = "corporate.meeting.attendance"
    _description = "Meeting Attendance"
    _order = "id"

    meeting_id = fields.Many2one(
        "corporate.meeting", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one("res.partner", string="Person", required=True)
    attendance_status = fields.Selection(
        selection=[
            ("present", "Present"),
            ("absent", "Absent"),
            ("excused", "Excused"),
        ],
        default="present",
        required=True,
    )
    attendance_mode = fields.Selection(
        selection=[("in_person", "In person"), ("remote", "Remote")],
        default="in_person",
    )
    company_id = fields.Many2one(
        related="meeting_id.company_id", store=True, index=True
    )

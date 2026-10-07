# -*- coding: utf-8 -*-
# Copyright (c) 2026 Les services de consultation Blue Fox, Inc.
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CorporateResolutionSignatory(models.Model):
    """Who signs a resolution, and in which capacity.

    The directors register does not answer this. A shareholder resolution is
    signed by shareholders; a conflict disclosure may be countersigned by an
    officer who does not vote. Inferring capacity from the register would
    invent facts — hence one manual line per signatory.
    """

    _name = "corporate.resolution.signatory"
    _description = "Corporate Resolution Signatory"
    _order = "sequence, id"

    resolution_id = fields.Many2one(
        "corporate.resolution",
        string="Resolution",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Print order of signature blocks.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Signatory",
        required=True,
    )
    capacity = fields.Selection(
        selection=[
            ("sole_shareholder", "Sole shareholder"),
            ("shareholder", "Shareholder"),
            ("sole_director", "Sole director"),
            ("director", "Director"),
            ("officer", "Officer"),
            ("proxy", "Proxy / attorney"),
            ("other", "Other"),
        ],
        string="Capacity",
        required=True,
        default="shareholder",
        help="Capacity in which the person signs (printed under the name).",
    )
    capacity_custom = fields.Char(
        string="Capacity (custom)",
        help="Literal capacity when the list is insufficient — e.g. "
             "“Vice President, Secretary and Treasurer”. Required when "
             "capacity is Other.",
    )
    capacity_label = fields.Char(
        string="Printed capacity",
        compute="_compute_capacity_label",
    )
    purpose = fields.Char(
        string="Signature purpose",
        help="Printed under capacity when the signature is for a limited "
             "purpose — e.g. “for the sole purpose of acknowledging the "
             "conflict disclosure”.",
    )

    @api.depends("capacity", "capacity_custom")
    def _compute_capacity_label(self):
        labels = dict(self.fields_get(["capacity"])["capacity"]["selection"])
        for rec in self:
            if rec.capacity == "other":
                rec.capacity_label = rec.capacity_custom or False
            else:
                rec.capacity_label = labels.get(rec.capacity) or False

    @api.constrains("capacity", "capacity_custom")
    def _check_capacity_custom(self):
        for rec in self:
            if rec.capacity == "other" and not rec.capacity_custom:
                raise ValidationError(_(
                    "Specify the capacity for %s: Other without text would "
                    "print a name with no capacity."
                ) % (rec.partner_id.name or _("this signatory")))

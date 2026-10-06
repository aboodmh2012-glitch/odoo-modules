# Copyright 2026 MASAR
# License LGPL-3.0 or later.
from odoo import fields, models


class MasarKnowledgeTag(models.Model):
    _name = "masar.knowledge.tag"
    _description = "Knowledge Tag"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    color = fields.Integer()
    active = fields.Boolean(default=True)
    _name_uniq = models.Constraint("UNIQUE(name)", "This tag already exists.")

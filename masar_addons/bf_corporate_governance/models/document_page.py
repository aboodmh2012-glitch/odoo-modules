# -*- coding: utf-8 -*-
# Copyright (c) 2026 Les services de consultation Blue Fox, Inc.
# Copyright 2026 MASAR — Minute Book on document.page (was project.document)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Minute Book classification on OCA Knowledge pages.

Upstream attached ``minute_book_section`` to proprietary ``project.document``.
MASAR keeps the same field semantics on ``document.page``.
"""
from odoo import fields, models


class DocumentPage(models.Model):
    _inherit = "document.page"

    minute_book_section = fields.Selection(
        selection=[
            ("charter", "Incorporation / Charter"),
            ("bylaws", "Articles / Bylaws"),
            ("agreements", "Material Agreements"),
            ("director_minutes", "Board Minutes"),
            ("shareholder_minutes", "Shareholder Minutes"),
            ("board_resolutions", "Board Resolutions"),
            ("shareholder_resolutions", "Shareholder Resolutions"),
            ("policies", "Policies"),
            ("forms_filed", "Regulatory Filings"),
            ("financial_statements", "Financial Statements"),
            ("other", "Other"),
        ],
        string="Minute Book section",
        index=True,
        help="Classify this Knowledge page in the corporate Minute Book view.",
    )

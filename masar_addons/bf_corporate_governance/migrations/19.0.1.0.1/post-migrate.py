# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Idempotent post-migrate for bf_corporate_governance 19.0.1.0.1.

ORM adds ``reminder_due_date`` on upgrade. This script only backfills
idempotent reminder state — safe to re-run; never deletes user data.
Railway one-shot markers are deploy orchestration only and are NOT a
substitute for this module upgrade path.
"""


def migrate(cr, version):
    if not version:
        return
    # Align legacy reminder_sent rows so cron does not double-fire after upgrade.
    cr.execute(
        """
        UPDATE corporate_compliance_event
           SET reminder_due_date = due_date
         WHERE reminder_sent IS TRUE
           AND reminder_due_date IS NULL
           AND due_date IS NOT NULL
        """
    )

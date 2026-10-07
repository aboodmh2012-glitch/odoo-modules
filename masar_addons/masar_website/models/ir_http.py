"""English job slugs through Odoo's native model converter and redirects."""

from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _slug(cls, value):
        if getattr(value, "_name", None) == "hr.job":
            return value.masar_english_slug()
        return super()._slug(value)

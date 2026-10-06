from odoo import _, api, fields, models
from odoo.exceptions import UserError


class McpModelSelectionWizard(models.TransientModel):
    """Wizard for selecting multiple models to enable for MCP access at once."""

    _name = "mcp.model.selection.wizard"
    _description = "MCP Model Selection Wizard"

    # Static field domain: Odoo 20 validates Many2many links against this on
    # create/write. Keep it identical to what a saved selection is allowed to
    # contain. Already-enabled models are hidden in the picker via the computed
    # view domain, not here -- a lambda ``id not in`` domain is not sent to the
    # web client, so users could still pick those rows and Odoo 20 then raises
    # ``Cannot link inaccessible records``.
    _MODEL_DOMAIN = [
        ("transient", "=", False),
        ("model", "not like", "ir.%"),
        ("model", "not like", "base_%"),
        ("model", "not like", "mcp.%"),
    ]

    @api.model
    def _get_model_domain(self):
        domain = list(self._MODEL_DOMAIN)
        enabled_model_ids = (
            self.env["mcp.enabled.model"].search([]).mapped("model_id.id")
        )
        if enabled_model_ids:
            domain.append(("id", "not in", enabled_model_ids))
        return domain

    @api.depends()
    def _compute_model_ids_domain(self):
        domain = self._get_model_domain()
        for rec in self:
            rec.model_ids_domain = domain

    model_ids_domain = fields.Binary(
        compute="_compute_model_ids_domain",
        default=lambda self: self._get_model_domain(),
    )
    model_ids = fields.Many2many(
        "ir.model",
        string="Models",
        required=True,
        domain="[('transient', '=', False), ('model', 'not like', 'ir.%'), "
        "('model', 'not like', 'base_%'), ('model', 'not like', 'mcp.%')]",
        help="Select models to enable for MCP access",
    )
    allow_read = fields.Boolean(default=True, help="Allow read operations through MCP")
    allow_create = fields.Boolean(
        default=False, help="Allow create operations through MCP"
    )
    allow_write = fields.Boolean(
        string="Allow Update", default=False, help="Allow update operations through MCP"
    )
    allow_unlink = fields.Boolean(
        string="Allow Delete", default=False, help="Allow delete operations through MCP"
    )
    allow_method_calls = fields.Boolean(
        default=False,
        help="Admin opt-in (off by default): let MCP clients invoke this "
        "model's own public business methods through call_model_method. Private "
        "(leading-underscore) methods, the public web_* family and the generic "
        "ORM/CRUD/data-access API (create/read/write/unlink/search/...) are "
        "always blocked; use the per-operation permissions above for CRUD. "
        "Everything runs under the calling user's Odoo access rights.",
    )

    @staticmethod
    def _ids_from_m2m_commands(commands):
        ids = []
        for command in commands or []:
            if not command:
                continue
            op = command[0]
            if op == 6:
                ids = list(command[2] or [])
            elif op == 5:
                ids = []
            elif op in (4, 1) and command[1]:
                ids.append(command[1])
        return ids

    @api.model_create_multi
    def create(self, vals_list):
        IrModel = self.env["ir.model"]
        for vals in vals_list:
            raw_ids = self._ids_from_m2m_commands(vals.get("model_ids"))
            if not raw_ids:
                continue
            valid = IrModel.browse(raw_ids).filtered_domain(self._MODEL_DOMAIN)
            if not valid:
                raise UserError(
                    _(
                        "None of the selected models can be enabled for MCP. "
                        "Choose a non-transient business model (not ir.*, "
                        "base_*, or mcp.*)."
                    )
                )
            vals["model_ids"] = [(6, 0, valid.ids)]
        return super().create(vals_list)

    def action_enable_models(self):
        """Enable selected models for MCP access.

        A selected model may already have an mcp.enabled.model row that is
        ARCHIVED (still occupying its ``UNIQUE(model_id)`` slot). Such rows are
        invisible to a default search, so a plain ``create()`` would raise the
        unique constraint. Search with ``active_test=False`` and reactivate the
        archived row (refreshing its permissions) instead of creating a
        duplicate; create only genuinely new models.
        """
        self.ensure_one()
        vals = {
            "allow_read": self.allow_read,
            "allow_create": self.allow_create,
            "allow_write": self.allow_write,
            "allow_unlink": self.allow_unlink,
            "allow_method_calls": self.allow_method_calls,
        }
        existing = (
            self.env["mcp.enabled.model"]
            .with_context(active_test=False)
            .search([("model_id", "in", self.model_ids.ids)])
        )
        existing_by_model = {rec.model_id.id: rec for rec in existing}

        vals_list = []
        for model in self.model_ids:
            record = existing_by_model.get(model.id)
            if not record:
                vals_list.append({"model_id": model.id, **vals})
            elif not record.active:
                record.write({**vals, "active": True})
            # An already-active row is left untouched.
        if vals_list:
            self.env["mcp.enabled.model"].create(vals_list)
        return {"type": "ir.actions.act_window_close"}

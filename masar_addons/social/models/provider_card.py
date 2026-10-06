from odoo import api, fields, models, _

PROVIDERS = [
    ("facebook", "Facebook", "Manage your Facebook pages and schedule posts", "/social/static/src/img/facebook.svg", 10, True),
    ("instagram", "Instagram", "Manage your Instagram Business account and schedule posts", "/social/static/src/img/instagram.svg", 20, True),
    ("linkedin", "LinkedIn", "Manage your LinkedIn account and schedule posts", "/social/static/src/img/linkedin.svg", 30, False),
    ("twitter", "X", "Manage your X accounts and schedule posts", "/social/static/src/img/twitter.svg", 40, False),
    ("youtube", "YouTube", "Manage your YouTube videos and schedule video uploads", "/social/static/src/img/youtube.svg", 50, False),
    ("telegram", "Telegram", "Manage your Telegram channel and scheduled posts", "/social/static/src/img/telegram.svg", 60, False),
]


class SocialProviderCard(models.TransientModel):
    _name = "social.provider.card"
    _description = "Social Provider"
    _order = "sequence, id"

    name = fields.Char(readonly=True)
    provider = fields.Char(readonly=True)
    description = fields.Char(readonly=True)
    image_url = fields.Char(readonly=True)
    sequence = fields.Integer(readonly=True)
    can_link = fields.Boolean(readonly=True)
    account_count = fields.Integer(readonly=True)

    @api.model
    def _refresh_cards(self):
        self.search([]).unlink()
        Account = self.env["social.account"]
        for provider, name, description, image_url, sequence, can_link in PROVIDERS:
            self.create({
                "name": name,
                "provider": provider,
                "description": description,
                "image_url": image_url,
                "sequence": sequence,
                "can_link": can_link,
                "account_count": Account.search_count([
                    ("platform", "=", provider),
                    ("company_id", "in", self.env.companies.ids),
                    ("active", "=", True),
                ]),
            })

    @api.model
    def action_open_providers(self):
        self._refresh_cards()
        return self.env.ref("social.action_social_provider_cards").read()[0]

    def action_link(self):
        self.ensure_one()
        if self.provider == "facebook":
            return self.env["social.account"].action_connect_facebook()
        if self.provider == "instagram":
            return self.env["social.account"].action_connect_instagram()
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {
            "title": self.name, "message": _("Connector coming soon."), "type": "info", "sticky": False}}

    def action_accounts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "name": _("%s accounts", self.name),
            "res_model": "social.account", "view_mode": "list,form",
            "domain": [("platform", "=", self.provider)],
        }

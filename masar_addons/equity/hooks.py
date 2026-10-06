# Part of Odoo. See LICENSE file for full copyright and licensing details.


def _activate_yer_and_company_equity(env):
    """Point the main company at MASAR AoA capital (YER ordinary shares)."""
    yer = env["res.currency"].with_context(active_test=False).search([("name", "=", "YER")], limit=1)
    if yer:
        yer.active = True
    company = env.company
    partner = company.partner_id
    vals = {
        "name": "MASAR Global for Financial Systems and Solutions",
        "is_company": True,
        "equity_legal_form": "Closed Yemeni Joint Stock Company",
        "equity_formation_date": "2026-04-01",
        "city": "Aden",
    }
    yemen = env.ref("base.ye", raise_if_not_found=False)
    if yemen:
        vals["country_id"] = yemen.id
    if yer:
        vals["equity_currency_id"] = yer.id
    partner.write(vals)
    company.write({"name": vals["name"]})


def post_init_hook(env):
    _activate_yer_and_company_equity(env)

# Copyright 2026 MASAR
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

"""Brand install hooks: reinstall-safe params + Settings admin feature toggles."""

# Optional xmlids — skipped quietly if the module is not installed.
ADMIN_FEATURE_GROUPS = (
    "crm.group_use_lead",
    "crm.group_use_recurring_revenues",
    "analytic.group_analytic_accounting",
    "product.group_product_variant",
    "product.group_product_pricelist",
    "uom.group_uom",
    "project.group_project_milestone",
    "project.group_project_recurring_tasks",
    "project.group_project_task_dependencies",
    "project.group_project_stages",
    "stock.group_production_lot",
    "stock.group_stock_multi_locations",
    "stock.group_adv_location",
    "mrp.group_mrp_routings",
    "sale.group_warning_sale",
    "mass_mailing.group_mass_mailing_campaign",
    "fieldservice.group_fsm_tag",
    "fieldservice.group_fsm_team",
    "fieldservice.group_fsm_category",
    "fieldservice.group_fsm_territory",
)


def pre_init_hook(env):
    """Clear orphan ir.config_parameter rows left after a previous uninstall
    (xmlids are removed but unique keys remain and block reinstall)."""
    cr = env.cr
    cr.execute(
        """
        DELETE FROM ir_config_parameter
         WHERE key IN (
            'masar.brand',
            'masar.company_name_ar',
            'masar.company_name_en'
         )
           AND id NOT IN (
            SELECT res_id FROM ir_model_data
             WHERE module = 'masar_brand'
               AND model = 'ir.config_parameter'
               AND res_id IS NOT NULL
           )
        """
    )


def _ensure_admin_feature_groups(env):
    system = env.ref("base.group_system", raise_if_not_found=False)
    if not system:
        return
    for xmlid in ADMIN_FEATURE_GROUPS:
        group = env.ref(xmlid, raise_if_not_found=False)
        if group and group not in system.implied_ids:
            system.write({"implied_ids": [(4, group.id)]})


def _apply_display_names(env):
    """noupdate XML will not overwrite an already-named company/website."""
    company = env.ref("base.main_company", raise_if_not_found=False)
    if company:
        vals = {}
        if company.name != "MASAR Pay":
            vals["name"] = "MASAR Pay"
        if "masar_brand_name" in company._fields and company.masar_brand_name != "MASAR":
            vals["masar_brand_name"] = "MASAR"
        if vals:
            company.write(vals)
    partner = env.ref("base.main_partner", raise_if_not_found=False)
    if partner and partner.name != "MASAR Pay":
        partner.write({"name": "MASAR Pay"})
    website = env.ref("base.default_website", raise_if_not_found=False)
    if website and website.name != "MASAR Pay":
        website.write({"name": "MASAR Pay"})


def post_init_hook(env):
    _ensure_admin_feature_groups(env)
    _apply_display_names(env)

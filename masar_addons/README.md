# MASAR → SMART addons (Odoo 20)

Copied read-only from `smartexsoftorg/masar` `custom_addons/`.
MASAR Production is never modified.

Native-first decisions: [`docs/migration/NON_HR_NATIVE_MATRIX.md`](../docs/migration/NON_HR_NATIVE_MATRIX.md).
Odoo 20 compatibility audit, security fix and wave plan: [`docs/migration/ODOO20_FUNCTIONAL_AUDIT.md`](../docs/migration/ODOO20_FUNCTIONAL_AUDIT.md).

## Priority

1. Non-HR modules (accounting, helpdesk, FSM, social, brand, …)
2. **HR lifecycle (go-ahead)** — native-first; see [`docs/migration/EMPLOYEE_FEATURE_DECISIONS.md`](../docs/migration/EMPLOYEE_FEATURE_DECISIONS.md)

## HR copied now (installable)

- `masar_hr_employee_documents`
- `masar_hr_disciplinary`
- `masar_hr_employee_transfer`
- `masar_hr_resignation`
- `masar_hr_attendance_regularization`
- `masar_hr_yemen`

## HR skipped (not essential yet)

- `fieldservice_sign`, `sign_oca`, `masar_hr_contract_sign`
- `payroll`, `masar_hr_payroll_yemen`
- `hr_appraisal_oca`, `hr_personal_equipment_*`
- `masar_hr_learning`, `masar_hr_org_chart`

## Copied now (99 modules)

- `account_asset_force_account`
- `account_asset_management`
- `account_chart_update`
- `account_check_deposit`
- `account_financial_report`
- `account_fiscal_year`
- `account_journal_lock_date`
- `account_lock_date_update`
- `account_move_name_sequence`
- `account_move_template`
- `account_move_tier_validation`
- `account_netting`
- `account_tax_balance`
- `account_usability`
- `attachment_zipped_download`
- `base_territory`
- `base_tier_validation`
- `base_tier_validation_confirm_auth`
- `base_tier_validation_formula`
- `base_tier_validation_forward`
- `base_tier_validation_server_action`
- `bf_corporate_governance`
- `date_range`
- `date_range_account`
- `dms`
- `document_knowledge`
- `document_page`
- `document_page_access_group`
- `document_page_approval`
- `document_page_partner`
- `document_page_project`
- `document_url`
- `equity`
- `fieldservice`
- `fieldservice_account`
- `fieldservice_activity`
- `fieldservice_availability`
- `fieldservice_calendar`
- `fieldservice_crm`
- `fieldservice_equipment_stock`
- `fieldservice_expense`
- `fieldservice_kanban_info`
- `fieldservice_portal`
- `fieldservice_project`
- `fieldservice_purchase`
- `fieldservice_recurring`
- `fieldservice_repair`
- `fieldservice_route`
- `fieldservice_route_availability`
- `fieldservice_sale`
- `fieldservice_sale_recurring`
- `fieldservice_sale_stock`
- `fieldservice_size`
- `fieldservice_skill`
- `fieldservice_stage_server_action`
- `fieldservice_stage_validation`
- `fieldservice_stock`
- `fieldservice_timesheet`
- `fieldservice_vehicle`
- `helpdesk_mgmt`
- `helpdesk_mgmt_activity`
- `helpdesk_mgmt_crm`
- `helpdesk_mgmt_project`
- `helpdesk_mgmt_rating`
- `helpdesk_mgmt_sale`
- `helpdesk_mgmt_sla`
- `helpdesk_portal_priority`
- `helpdesk_product`
- `helpdesk_ticket_close_inactive`
- `helpdesk_ticket_partner_response`
- `helpdesk_ticket_related`
- `helpdesk_type`
- `knowledge_control`
- `masar_brand`
- `masar_crm_services`
- `masar_knowledge`
- `masar_theme`
- `masar_ui_tweaks`
- `masar_website`
- `mcp_server`
- `partner_statement`
- `purchase_tier_validation`
- `queue_job`
- `report_xlsx`
- `report_xlsx_helper`
- `sale_tier_validation`
- `social`
- `social_crm`
- `social_facebook`
- `social_helpdesk`
- `social_instagram`
- `social_linkedin`
- `social_mcp`
- `social_meta`
- `social_telegram`
- `social_tiktok`
- `social_youtube`
- `stock_picking_tier_validation`
- `web_responsive`

## Odoo 20 notes

- Security converted from `ir.rule` / `ir.model.access.csv` → `security/ir.access.csv` where present.
- Manifest versions bumped `19.0.*` → `20.0.*`.
- Prefer Odoo 20 **Community native** when it covers the need (see `docs/migration/NON_HR_NATIVE_MATRIX.md`).
- Never `-i all`. Install dependency-ordered batches via `SMART_INSTALL_MODULES`.

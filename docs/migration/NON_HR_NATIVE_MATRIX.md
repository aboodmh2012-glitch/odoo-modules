# Non-HR native-first matrix — MASAR → SMART (Odoo 20 CE)

Updated: 2026-10-06. SMART runtime is **Odoo 20 Community** (`odoo:20.0`).  
MASAR Production is read-only. HR/employee modules are **out of scope** until explicit go-ahead.

## Decision rules

| Decision | When |
|----------|------|
| **NATIVE** | Odoo 20 CE already covers the need; do not install the MASAR/OCA module |
| **NATIVE + CONFIGURE** | Use CE app; configure settings/data instead of custom code |
| **COPY & MIGRATE** | CE gap vs MASAR; keep module at `20.0.*` with `ir.access.csv` |
| **DEFER** | Install later (dependency or product priority) |
| **SKIP (EE-only)** | Feature exists only in Enterprise; CE must use OCA/MASAR copy |

Enterprise apps (`industry_fsm`, EE `helpdesk`, EE `social`, EE `knowledge`, EE `account_asset`) are **not** on SMART → never treat them as installable natives.

## Domain summary

| Domain | Verdict | Notes |
|--------|---------|-------|
| Accounting OCA (assets, fiscal year, lock, reports, netting, templates, tax balance) | **COPY & MIGRATE** | CE lacks most of these; OCA is the CE path |
| Tier validation (+ sale/purchase/stock/account bridges) | **COPY & MIGRATE** | No CE native multi-tier approval stack |
| Helpdesk (OCA `helpdesk_mgmt` + bridges) | **COPY & MIGRATE** | EE Helpdesk unavailable; OCA is CE standard |
| Field Service (OCA `fieldservice` + bridges) | **COPY & MIGRATE** | EE Industry FSM unavailable |
| Knowledge / DMS / document pages | **COPY & MIGRATE** | EE Knowledge unavailable; OCA Knowledge + DMS |
| Social + Meta/Telegram/… + MCP | **COPY & MIGRATE** | MASAR stack; EE Social unavailable |
| Branding / theme / website / UI | **COPY & MIGRATE** | MASAR identity; review theme for Odoo 20 UI |
| Corporate governance (`bf_*`) | **COPY & MIGRATE** | Custom MASAR/BF domain |
| Reporting helpers (`report_xlsx*`, `date_range*`) | **COPY & MIGRATE** | Shared deps for accounting/reports |
| `queue_job`, `web_responsive` | **COPY & MIGRATE** | Infra used by jobs / UX |
| HR / payroll / sign / appraisal / PPE | **PARTIAL** | Core lifecycle + OCA `payroll`/`payroll_account` COPY; Yemen overlay/sign/PPE/learning SKIP — see `EMPLOYEE_FEATURE_DECISIONS.md` |

## Module decisions (100 copied)

### Accounting & reporting — COPY & MIGRATE

| Module | Why not NATIVE |
|--------|----------------|
| `account_asset_management`, `account_asset_force_account` | CE has no full assets app equivalent to EE |
| `account_chart_update`, `account_check_deposit`, `account_fiscal_year` | OCA CE workflows |
| `account_financial_report`, `partner_statement`, `account_tax_balance` | OCA reporting stack |
| `account_journal_lock_date`, `account_lock_date_update` | Per-journal / adviser lock beyond stock CE |
| `account_move_name_sequence`, `account_move_template`, `account_netting`, `account_usability` | CE gaps / OCA UX |
| `account_move_tier_validation` | Needs OCA tier validation |
| `date_range`, `date_range_account`, `report_xlsx`, `report_xlsx_helper` | Shared reporting deps |
| `equity` | Cap-table / securities — not in CE |

**Deferred from accounting install (needs deeper Odoo 20 port):**
- `account_chart_update` — references removed `account.group` model
- `account_usability` — inherits removed `account.group`
- `account_financial_report` — inherits removed `account.group` (trial balance grouping)

### Tier validation — COPY & MIGRATE

`base_tier_validation`, `base_tier_validation_confirm_auth`, `base_tier_validation_formula`, `base_tier_validation_forward`, `base_tier_validation_server_action`, `purchase_tier_validation`, `sale_tier_validation`, `stock_picking_tier_validation`

### Helpdesk — COPY & MIGRATE (not EE Helpdesk)

`helpdesk_mgmt`, `helpdesk_mgmt_activity`, `helpdesk_mgmt_crm`, `helpdesk_mgmt_project`, `helpdesk_mgmt_rating`, `helpdesk_mgmt_sale`, `helpdesk_mgmt_sla`, `helpdesk_portal_priority`, `helpdesk_product`, `helpdesk_ticket_close_inactive`, `helpdesk_ticket_partner_response`, `helpdesk_ticket_related`, `helpdesk_type`

### Field Service — COPY & MIGRATE (not EE Industry FSM)

`fieldservice` + all `fieldservice_*` present in tree (except deferred `fieldservice_sign`)

### Knowledge / documents — COPY & MIGRATE

`document_knowledge`, `document_page`, `document_page_access_group`, `document_page_approval`, `document_page_partner`, `document_page_project`, `document_url`, `dms`, `knowledge_control`, `masar_knowledge`, `attachment_zipped_download`

### MCP / jobs — COPY & MIGRATE

`mcp_server`, `queue_job`

**Removed from SMART (uninstalled + deleted):** MASAR `social*` stack (`social`, `social_meta`, `social_facebook`, `social_instagram`, `social_telegram`, `social_linkedin`, `social_tiktok`, `social_youtube`, `social_crm`, `social_helpdesk`, `social_mcp`). Keep native CE `social_media` (website/email). Do not uninstall `mcp_server` / `helpdesk_mgmt` / `crm`.

### Branding / UX / CRM extras — COPY & MIGRATE

| Module | Notes |
|--------|-------|
| `masar_brand`, `masar_theme`, `masar_website`, `masar_ui_tweaks` | Keep MASAR identity; theme summary still mentions Odoo 19 — visual QA on SMART |
| `web_responsive` | Better CE backend UX than stock |
| `masar_crm_services` | MASAR service/channel tracking on CRM |
| `base_territory` | FSM territory model |

### Governance — COPY & MIGRATE

`bf_corporate_governance`

## Explicitly not “take EE instead”

Do **not** replace the above with Enterprise modules on this SMART Community image. If SMART later moves to EE, re-run this matrix before uninstalling OCA copies.


**Deferred from knowledge install (needs Odoo 20 portal view port):**
- `dms` — portal inherit `portal_common_category` missing in Odoo 20
- `document_page_project` — project kanban xpath `o_project_kanban_boxes` missing

**Helpdesk note:** team dashboard kanban (`helpdesk_dashboard_views.xml`) temporarily omitted pending Odoo 20 kanban template port.

## HR (go-ahead; native-first)

Core lifecycle modules are under `masar_addons/masar_hr_*` (documents, disciplinary, transfer, resignation, attendance regularization, yemen).  
Skipped for now: Yemen payroll overlay / sign / PPE / appraisal / learning / org_chart — see `EMPLOYEE_FEATURE_DECISIONS.md`. OCA `payroll` and `payroll_account` are copied.

## Recommended non-HR install batches

Never `-i all`. One batch at a time via `SMART_INSTALL_MODULES`, then clear the variable.

```text
# Batch A — foundations
report_xlsx,report_xlsx_helper,date_range,date_range_account,attachment_zipped_download,web_responsive,queue_job,base_territory,base_tier_validation,base_tier_validation_formula,base_tier_validation_forward,base_tier_validation_server_action,base_tier_validation_confirm_auth

# Batch B — accounting
account_usability,account_fiscal_year,account_move_name_sequence,account_chart_update,account_check_deposit,account_journal_lock_date,account_lock_date_update,account_move_template,account_netting,account_tax_balance,account_financial_report,partner_statement,account_asset_management,account_asset_force_account,account_move_tier_validation,purchase_tier_validation,sale_tier_validation,stock_picking_tier_validation,equity

# Batch C — knowledge / DMS
document_knowledge,document_page,document_page_access_group,document_page_approval,document_page_partner,document_page_project,document_url,dms,masar_knowledge,knowledge_control

# Batch D — helpdesk
helpdesk_mgmt,helpdesk_type,helpdesk_mgmt_activity,helpdesk_mgmt_crm,helpdesk_mgmt_project,helpdesk_mgmt_rating,helpdesk_mgmt_sale,helpdesk_mgmt_sla,helpdesk_portal_priority,helpdesk_product,helpdesk_ticket_close_inactive,helpdesk_ticket_partner_response,helpdesk_ticket_related

# Batch E — field service
fieldservice,fieldservice_vehicle,fieldservice_activity,fieldservice_calendar,fieldservice_crm,fieldservice_project,fieldservice_stock,fieldservice_equipment_stock,fieldservice_account,fieldservice_sale,fieldservice_sale_stock,fieldservice_purchase,fieldservice_recurring,fieldservice_sale_recurring,fieldservice_repair,fieldservice_route,fieldservice_availability,fieldservice_route_availability,fieldservice_portal,fieldservice_expense,fieldservice_kanban_info,fieldservice_size,fieldservice_skill,fieldservice_stage_server_action,fieldservice_stage_validation,fieldservice_timesheet

# Batch F — mcp
mcp_server

# Batch G — brand / website / governance
masar_brand,masar_theme,masar_ui_tweaks,masar_website,masar_crm_services,bf_corporate_governance
```

## Python extras (image)

Baked via `odoo20/requirements-extra.txt` in the SMART Dockerfile:
`openupgradelib`, `xlsxwriter`, `xlrd`, `defusedxml`, `packaging`, `authlib`.

## Safety

- MASAR: read/copy only
- SMART: edits only in `aboodmh2012-glitch/odoo-modules`
- HR install: **stop and confirm with user** before any HR batch

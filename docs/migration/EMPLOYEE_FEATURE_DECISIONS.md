# Employee feature decisions — MASAR → Odoo 20 (SMART)

Updated: 2026-10-06. User go-ahead to migrate HR after native-first review.

## Native-first (Odoo 20 CE) — prefer these, do not re-copy MASAR overlays

| Topic | Decision | Notes |
|-------|----------|-------|
| Employee form layout | **NATIVE** | Keep Odoo 20 `hr` form; MASAR heavy overlays stay `active=False` |
| Remote work / homeworking | **NATIVE** | Built into Odoo 20 `hr` |
| Onboarding / offboarding plans | **NATIVE + CONFIGURE** | `mail.activity.plan` seeds from `masar_hr_yemen` (light data only) |
| Time off / attendance apps | **NATIVE** | CE `hr_holidays`, `hr_attendance`, `hr_recruitment` |
| Recruitment board | **NATIVE** | CE `hr_recruitment` (+ website jobs if needed later) |

## COPY & MIGRATE now (CE gap vs MASAR — needed for SMART)

| Module | Why not native | Odoo 20 fixes |
|--------|----------------|---------------|
| `masar_hr_employee_documents` | Doc types, expiry cron, entry/exit checklist | `ir.access.csv`; form overlay inactive |
| `masar_hr_disciplinary` | Cases / sanctions / investigation | Groups XML kept; rules → `ir.access` domains |
| `masar_hr_employee_transfer` | Transfer without cloning employee | `ir.access.csv` |
| `masar_hr_resignation` | Resignation + deferred archive | `ir.access.csv` |
| `masar_hr_attendance_regularization` | Attendance correction requests | `ir.access.csv` |
| `masar_hr_yemen` | Yemen labor seeds + light extensions | `ir.access.csv`; drop `report_file`; **omit** `hr.leave.type` seeds (Odoo 20 → `hr.time.rule`, use native Time Off) |
| `payroll` | OCA payslips; MASAR formula on structure (not `masar_hr_payroll_yemen`) | `20.0.1.1.0`; APPEARANCE 25% + TRANSPORT 20%; TAX `(BASIC-10000)×15%`; EINS 6%; CINS 9% |
| `payroll_account` | Post payslips to `account.move` | `20.0.1.0.0`; `primary_bank_account_id`; no Yemen CoA mapping |

Deps already on SMART: `document_page`, `helpdesk_mgmt`, `helpdesk_type`.

## SKIP for now (not essential / heavy / weak CE fit)

| Module | Decision | Reason |
|--------|----------|--------|
| `masar_hr_learning` | **SKIP** | Needs `hr_skills_slides/survey/event` — not a clean CE 20 path |
| `masar_hr_org_chart` | **SKIP** | Visual polish; depends on `masar_theme` |
| `masar_hr_contract_sign` + `sign_oca` | **SKIP** | Heavy CE sign stack — later if needed |
| `masar_hr_payroll_yemen` | **SKIP** | Yemen overlay; depends on sign stack — not copied |
| `hr_appraisal_oca` | **SKIP** | Not critical; revisit if CE appraisal gaps appear |
| `hr_personal_equipment_*` | **SKIP** | PPE after core HR stable |
| `fieldservice_sign` | **SKIP** | Needs `sign_oca` |

## Install batch (after non-HR health is green)

```text
SMART_INSTALL_MODULES=payroll,payroll_account
```

Never `-i all`. Install once, then clear the variable.

## Safety

- MASAR Production: **READ/COPY only**
- All edits in `aboodmh2012-glitch/odoo-modules`
- Prefer native Odoo 20 CE whenever it already covers the need

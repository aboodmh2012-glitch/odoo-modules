# MASAR → SMART addons (Odoo 20)

Copied **read-only** from `smartexsoftorg/masar` (`custom_addons/`) for SMART lab.
MASAR Production is never modified here.

## Phase 1 (employee lifecycle) — present

| Module | Action | Notes |
|--------|--------|-------|
| `masar_hr_employee_documents` | COPY & MIGRATE | Not in Odoo 20 CE native |
| `masar_hr_disciplinary` | COPY & MIGRATE | Not native |
| `masar_hr_employee_transfer` | COPY & MIGRATE | Not native |
| `masar_hr_resignation` | COPY & MIGRATE | Not native |
| `masar_hr_attendance_regularization` | COPY & MIGRATE | Not native |
| `masar_hr_yemen` | COPY & MIGRATE | Yemen seeds/policy on top of above |
| `document_knowledge` / `document_page` | COPY (deps) | Used by disciplinary / yemen |
| `helpdesk_mgmt` / `helpdesk_type` | COPY (deps) | Used by yemen grievance ticket type |

## Deferred (native-first or later phase)

| Module | Why deferred |
|--------|----------------|
| Heavy employee-form XML overlays | MASAR PRs #167–#170 already restore native form |
| `hr_homeworking` | Merged into Odoo 20 `hr` |
| `masar_hr_org_chart` + `masar_theme` | Needs theme/web stack — later |
| `masar_hr_contract_sign` + `sign_oca` | Later |
| `masar_hr_payroll_yemen` + `payroll` | Later |
| `masar_hr_learning` | Needs `hr_skills_*` stack — investigate CE availability |

Install on SMART only via `SMART_INSTALL_MODULES=...` (never `-i all`).

## Odoo 20 security note

Odoo 20 removed `ir.rule` / classic `ir.model.access.csv`. Phase-1a HR modules
were converted to `security/ir.access.csv`. Remaining deps (`document_*`,
`helpdesk_*`, `masar_hr_disciplinary`, `masar_hr_yemen`) still need the same
conversion before install.

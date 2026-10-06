# Employee feature decisions — MASAR → Odoo 20 (SMART)

Updated: 2026-10-06 after read access to `smartexsoftorg/masar`.

## Native-first rules (from MASAR itself)

MASAR Odoo 19 already restored **native employee form** (PRs #167–#170).  
Do **not** reintroduce heavy form overlays on Odoo 20.

| Topic | Decision |
|-------|----------|
| Employee form layout | **NATIVE** (Odoo 20 `hr`) |
| Remote work / `hr_homeworking` | **NATIVE** (merged into Odoo 20 `hr`) |
| Onboarding/Offboarding plans | **NATIVE** `mail.activity.plan` + CONFIGURE (per MASAR HR review) |
| Recruitment board | Prefer CE `hr_recruitment` / website jobs before custom |

## Phase 1 copied into `masar_addons/` (this SMART branch)

| Module | Source | Why not native | Action |
|--------|--------|----------------|--------|
| `masar_hr_employee_documents` | MASAR | Document types, expiry cron, entry/exit checklist | COPY & MIGRATE → version `20.0.*` |
| `masar_hr_disciplinary` | MASAR | Cases / sanctions / investigation | COPY & MIGRATE |
| `masar_hr_employee_transfer` | MASAR | Transfer without cloning | COPY & MIGRATE |
| `masar_hr_resignation` | MASAR | Resignation + deferred archive | COPY & MIGRATE |
| `masar_hr_attendance_regularization` | MASAR | Attendance correction requests | COPY & MIGRATE |
| `masar_hr_yemen` | MASAR | Yemen labor seeds/policy extensions | COPY & MIGRATE |
| `document_knowledge` / `document_page` | OCA (vendored) | Dep of disciplinary/yemen | COPY (deps) |
| `helpdesk_mgmt` / `helpdesk_type` | OCA (vendored) | Dep of yemen grievance type | COPY (deps) |

## Deferred

| Module | Decision | Reason |
|--------|----------|--------|
| `masar_hr_org_chart` + `masar_theme` | LATER | Theme/web stack |
| `masar_hr_contract_sign` + `sign_oca` | LATER | Sign CE stack |
| `masar_hr_payroll_yemen` + `payroll` | LATER | Payroll CE — separate phase |
| `masar_hr_learning` | INVESTIGATE | Needs `hr_skills_*` availability on CE 20 |
| `hr_appraisal_oca` | LATER | Appraisal CE alternative |
| `hr_personal_equipment_*` | LATER | PPE — link after resignation gates |

## Recommended SMART install order

```text
SMART_INSTALL_MODULES=document_knowledge,document_page,helpdesk_mgmt,helpdesk_type,masar_hr_employee_documents,masar_hr_disciplinary,masar_hr_employee_transfer,masar_hr_resignation,masar_hr_attendance_regularization,masar_hr_yemen
```

Never `-i all`. Install once, then clear the variable.

## Safety

- MASAR Production: **READ/COPY only** — no commits/pushes to `smartexsoftorg/masar`
- All edits live in `aboodmh2012-glitch/odoo-modules`

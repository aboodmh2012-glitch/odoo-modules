# Employee feature decisions — MASAR → Odoo 20 (SMART)

Goal: **do not blind-copy** MASAR employee customizations. Prefer Odoo 20 Community native.

Updated: 2026-10-06 via Railway read of MASAR production logs/commits (**no MASAR writes**).

## Decision legend

| Decision | Meaning |
|----------|---------|
| NATIVE | Use Odoo 20 core; do not copy custom code |
| ADAPT | Thin SMART module wrapping native |
| COPY & MIGRATE | MASAR-specific; copy into `masar_addons/` and port to 20.0 |
| DROP | No longer needed |
| INVESTIGATE | Need source files (GitHub read) |

## Critical finding from MASAR recent history

MASAR already moved **toward native employee form** on Odoo 19:

| PR | Message | Implication |
|----|---------|-------------|
| #167 | Restore native Odoo 19 employee form | Prefer NATIVE for form layout |
| #169 | force employee form reset | Strip custom form chrome |
| #170 | show remaining employee-form inherits + reset v3 | Keep only leftover inherits worth keeping |

**Do not re-copy old heavy employee-form overlays.** Re-evaluate only what #170 still inherits.

## MASAR custom modules seen in production logs

### Brand / website
| Module | Likely role | Provisional action |
|--------|-------------|--------------------|
| `masar_website` | Website pack / content | COPY & MIGRATE (theme/content) |
| `masar_theme` | Theme | COPY & MIGRATE |
| `masar_brand` / `masar_brand_fix` | Branding | COPY & MIGRATE |
| `masar_ux` | UX tweaks | INVESTIGATE — drop if superseded by native |
| `masar_homepage_polish` | Homepage | COPY & MIGRATE or fold into theme |
| `masar_footer_polish` | Footer | COPY & MIGRATE or fold into theme |

### HR / employees (priority)
| Module | Likely role | vs Odoo 20 native | Provisional action |
|--------|-------------|-------------------|--------------------|
| `masar_hr_yemen` | Yemen HR localization / contracts | Not in CE core | COPY & MIGRATE (after source read) |
| `masar_hr_employee_documents` | Employee documents | Partial native attachments | INVESTIGATE — keep only MASAR document types/workflow |
| `masar_hr_disciplinary` | Disciplinary | Not CE native | COPY & MIGRATE |
| `masar_hr_contract_sign` | Contract signing | Sign is Enterprise | COPY & MIGRATE / ADAPT |
| `masar_hr_payroll_yemen` | Yemen payroll rules | Payroll Enterprise | COPY & MIGRATE (CE custom) — note recent retire/revert PRs #164–#166 |

### OCA / third-party seen in logs
| Module | Notes | Action |
|--------|-------|--------|
| `hr_appraisal_oca` | CE appraisal alternative | INVESTIGATE Odoo 20 branch |
| `hr_personal_equipment` (+ request/stock) | Equipment requests | INVESTIGATE Odoo 20 |
| `hr_homeworking` | **Merged into `hr` in Odoo 20** | **NATIVE / DROP module** |
| `hr_org_chart` | Org chart | INVESTIGATE vs CE |

## Odoo 20 Community native baselines

| Topic | Native in 20 | MASAR implication |
|-------|--------------|-------------------|
| Remote work | Inside `hr` | Do not port `hr_homeworking` |
| Employee directory multi-company | Broader public directory | Re-check custom company rules |
| Variable working schedules | `calendar_type` | Prefer native before custom |
| Employee form layout | Core form | Follow MASAR #167–#170: native-first |
| Jobs website | `/jobs` | Prefer native + theme ADAPT |
| Payroll / Sign / Appraisals (Enterprise) | Not in CE | Keep CE/OCA substitutes only if MASAR still needs them |

## Still blocked for actual COPY

Railway token works for SMART read/write and MASAR **read**.  
GitHub `smartexsoftorg/masar` still **404** for this agent — cannot COPY module source into `masar_addons/` until repo read is granted.

## Workflow when GitHub read arrives

1. Clone MASAR read-only → inventory `custom_addons/`.
2. Diff employee form inherits after PR #170 vs Odoo 20 `hr` views.
3. COPY only modules decided COPY & MIGRATE into SMART `masar_addons/`.
4. Port manifests to `20.0.*`; fix XML/Python/JS; tighten ACL.
5. Install module-by-module on SMART via `SMART_INSTALL_MODULES=...` (never `-i all`).

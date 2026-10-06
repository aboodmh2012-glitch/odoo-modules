# Employee feature decisions — MASAR → Odoo 20 (SMART)

Goal: **do not blind-copy** MASAR employee customizations. For each feature,
prefer Odoo 20 Community native behavior when it covers the requirement.

Status: **framework ready — waiting for MASAR source** (`smartexsoftorg/masar`).

## Decision legend

| Decision | Meaning |
|----------|---------|
| NATIVE | Use Odoo 20 core; do not copy custom code |
| ADAPT | Keep a thin SMART module that wraps/extends native |
| COPY & MIGRATE | Feature is MASAR-specific; copy into `masar_addons/` and port to 20.0 |
| DROP | No longer needed |
| INVESTIGATE | Need to read MASAR code / confirm with stakeholder |

## Odoo 20 Community — known native HR changes (baseline)

| Topic | Odoo 20 native | Implication for MASAR custom |
|-------|----------------|------------------------------|
| Remote work / homeworking | Merged into `hr` (no `hr_homeworking`) | DROP dependency; use Work tab locations |
| Working schedules | `calendar_type`: fixed / variable / undefined | Prefer native variable calendars before custom rotation code |
| Employee directory | Broader multi-company visibility on `hr.employee.public` | Re-check any MASAR company-scoped directory rules — may be obsolete or need intentional domain |
| Salary simulation button | Enterprise-only | If MASAR CE had custom simulation → INVESTIGATE / ADAPT, not “native CE” |
| Recruitment website jobs | Core `/jobs` | Prefer theme/SEO ADAPT over duplicating job board logic |
| Attendance / Time Off / Expenses | Core CE apps present on SMART lab | Extend only for MASAR-specific rules |

## Pending rows (fill after MASAR COPY)

| Feature (from MASAR employees custom) | In Odoo 20 native? | Decision | SMART target module | Notes |
|---------------------------------------|--------------------|----------|---------------------|-------|
| *(awaiting MASAR module list)* | | INVESTIGATE | | |

## Workflow once MASAR is readable

1. Inventory all modules that inherit `hr.employee`, `hr.department`, `hr.job`, recruitment, attendance, leave.
2. For each inherited field/view/method: map to native Odoo 20 equivalent.
3. Only COPY remnants that still add MASAR-specific value into `masar_addons/`.
4. Set `__manifest__.py` `version` to `20.0.x.y.z`; fix XML/Python/JS; tighten ACL (no privilege expansion).
5. Install on SMART with `SMART_INSTALL_MODULES=<one_module>` against DB `odoo20`.

## Safety

- Never write to MASAR Production Railway / `smartexsoftorg/masar` main.
- Never `-i all` / `-u all`.
- No MASAR production DB clone in this phase.

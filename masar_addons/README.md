# MASAR → SMART addons (Odoo 20)

Modules here are **copied** from MASAR (`smartexsoftorg/masar`) for migration
and testing on SMART only. MASAR Production remains read-only / untouched.

## Rules

1. **Copy, never move** — do not edit MASAR in place.
2. **Native first** — before keeping a custom feature, check Odoo 20 Community.
3. **Employees first** — HR customizations are evaluated in
   `docs/migration/EMPLOYEE_FEATURE_DECISIONS.md`.
4. Install **module-by-module** on SMART (`SMART_INSTALL_MODULES=...`), never `-i all`.

## Layout

```
masar_addons/
  <module_technical_name>/
    __manifest__.py   # version must start with 20.0.
    ...
```

## Status

Waiting on read access to `smartexsoftorg/masar` (or an exported addon zip)
before the first COPY lands here.

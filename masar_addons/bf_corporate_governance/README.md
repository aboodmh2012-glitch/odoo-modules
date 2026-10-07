# Corporate Governance (MASAR)

AGPL-3 port of Blue Fox / Symbifox `bf_corporate_governance` for Odoo 19.

**Upstream source commit:** `4a0f40031978b7d639cf9b0bb3e4470a8c3cc783` (LGPL-3)  
**MASAR shipping license:** AGPL-3 (ADR-8 — depends on AGPL Knowledge / KC)  
**Copyright:** Les services de consultation Blue Fox, Inc. + MASAR  

See `docs/THIRD_PARTY_NOTICES.md` and `docs/MASAR_GOVERNANCE_KNOWLEDGE_ARCHITECTURE.md`.

## Semantics

| Field | Role |
|-------|------|
| `document_ids` | Navigation to Knowledge pages (mutable HEAD) — **not** evidence |
| `approved_history_ids` | Exact frozen `document.page.history` (`kc_frozen` + version numbers) — **evidence** |

## Install / upgrade (data integrity)

```bash
# Clean install
odoo -d <db> -i bf_corporate_governance --stop-after-init

# Upgrade (idempotent migrations under migrations/)
odoo -d <db> -u bf_corporate_governance --stop-after-init
```

Or: `MASAR_UPGRADE_MODULES=bf_corporate_governance`

Railway marker `.bf_corporate_governance_installed_19010` is **deploy orchestration only**.
It must never be treated as the migration/data-safety strategy. Rebuilds re-run
module install/upgrade via Odoo’s normal registry path.

## Tests

```bash
odoo -d <db> -i bf_corporate_governance --test-enable \
  --test-tags=/bf_corporate_governance --stop-after-init
```

## UI language

User-facing strings are **English-neutral** (no Quebec/REQ legal wording).
Arabic / English translations are a later i18n pass.

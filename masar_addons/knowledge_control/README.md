# Knowledge Control (MASAR)

Controlled-document layer on OCA Knowledge (`document.page`).

## Features (Phase 1)

- Document types (policy, procedure, …)
- Formal lifecycle with server-side transitions
- Structured versioning (Major / Minor / Editorial) on history snapshots
- Published immutability (no silent overwrite)
- Policy ↔ procedure links
- Distribution & per-version acknowledgment
- Tier Validation integration (optional definition, inactive by default)
- Review-due and ack-overdue crons

## Non-goals

Does not install Symbifox proprietary modules. See
`docs/MASAR_GOVERNANCE_KNOWLEDGE_ARCHITECTURE.md` and
`docs/THIRD_PARTY_NOTICES.md`.

Phase 2 Governance app: LGPL module `bf_corporate_governance`
(entrypoint marker `.bf_corporate_governance_installed_19010`).

## Install

Railway one-shot marker: `.knowledge_control_installed_19010`

Or: `MASAR_UPGRADE_MODULES=masar_knowledge,knowledge_control`

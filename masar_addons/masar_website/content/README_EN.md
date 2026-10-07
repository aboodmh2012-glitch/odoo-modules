# English website content — 2026-09-20

This release translates the existing Arabic editorial package, not a new set of products or a change in licensing status. `source_en_1.json` and `source_en_2.json` contain all 31 records, including SEO, CTAs, approval gates and internal editorial notes. Their source is the Arabic package with SHA256 `0352d26143649808f2412c0d75e87e37b2c90ca10f5f48c710286c6d995cc92c`.

## Publication scope

Keep the existing 17 public informational pages and 14 unpublished review drafts. Do not publish the drafts or overwrite the original contact, privacy, company or other legacy pages. Reuse the same `website.page` IDs, URLs and views. Only add the English branch and English SEO values; preserve the exact live Arabic layout and Arabic SEO. Existing English legacy fallbacks for the four core pages are backed up and replaced with the complete translation.

`english_content.py` reuses the original `content_engine.build_arch` and shared styles. There is no new app, model, controller, payment API, duplicate page, stylesheet or layout engine. Generated English links retain `/en`; the Odoo language selector retains page identity.

## Validation and rollout

The image build runs both Arabic and English unit tests. First deploy `import_english.py --inspect` as a read-only pre-deploy command. Read the reported `plan_hash` and page inventory. It makes zero changes.

Only after review, set `MASAR_CONTENT_EN_APPLY=2026-09-20-en-content-v1` and use `import_english.py --apply --expect-plan <observed-plan-hash>` for one deployment. A changed live plan is rejected instead of overwriting intervening edits. Use a fresh Git deployment so Railway picks up the current configuration rather than a previous deployment snapshot.

The importer checks the existing Arabic success marker, exact page/view identity, both installed website languages, publication and access state, unchanged Arabic body and SEO, and QWeb compilation in both languages. Backup, source register and success marker are stored in admin-only `ir.config_parameter` records in the same transaction.

For verification set `MASAR_CONTENT_EN_HTTP_PROBE=2026-09-20-en-content-v1`. The one-shot child makes anonymous HTTP GET requests only, checking the English body, H1, title, description, direction, related links and language-selector links. It verifies drafts remain hidden and runs the original Arabic regression checks against local and public URLs. It does not submit forms, move money or prove payment services are operational.

After confirmation, clear the pre-deploy command and both English apply/probe flags. Normal restarts must not reimport content.

## Rollback

Set `MASAR_CONTENT_EN_ROLLBACK=2026-09-20-en-content-v1` and execute `import_english.py --rollback` once. This uses the stored snapshot and refuses to overwrite pages edited after the translation. Keep the original Arabic rollback workflow separate. Do not roll back the Arabic release after this English release without first reviewing their dependency.

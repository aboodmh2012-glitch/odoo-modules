# Approved Arabic website editorial import

Source: MASAR_Website_Content_AR.json (2026-09-20-editorial-draft), 31 records.
SHA256: 0352d26143649808f2412c0d75e87e37b2c90ca10f5f48c710286c6d995cc92c.
The four source_ar.*.b64 files form one gzip/base64 archive of the exact source JSON, not executable content. They are deliberately outside static/.

## Scope

17 Arabic informational pages: home, solutions, six product pages, personal, business, institutions, developers, partners, pricing, help, FAQ and fraud-awareness guidance.
14 gated records stay unpublished and unindexed under /website-content-review/...: about, governance, leadership, security-compliance, complaints, contactus, news, careers, locations, status, privacy, terms, cookies and accessibility. Their review notes are restricted to website designers. Existing published originals at those paths are untouched.

No financial product is activated. No fees, licences, partnerships, API endpoints, certifications or availability metrics are invented. No forms are submitted by the verifier. Existing English templates are retained as fallbacks; newly-created pages explicitly say their content is currently available in Arabic.

The result uses native website.page and ir.ui.view records, native menus, and the existing MASAR design classes. Editable in Website > Site > Pages. Shared content styles are scoped centrally; no module upgrade or theme reset is needed.

## Controlled rollout

1. Build runs test_content.py and Python/shell syntax checks.
2. Pre-deploy: python3 /mnt/extra-addons/masar_website/content/import_content.py --inspect. It prints the actual serving pages and navigation without committing changes.
3. Only after checking the inventory, use --apply with MASAR_CONTENT_APPLY=2026-09-20-ar-content-v1. All writes are in one transaction, protected by an advisory lock, and compile checks precede commit.
4. Set MASAR_CONTENT_HTTP_PROBE=1 for the apply deployment. The optional wrapper keeps the original entrypoint and emits anonymous local and public-domain HTTP verification results, including draft non-disclosure and original English/contact routes.
5. Inspect both [masar-content] and [masar-content-http] logs. Railway SUCCESS alone is not application verification.
6. Clear the one-shot pre-deploy command and guards after successful verification.

Original views are not deleted or rewritten. Original page/menu pointers, translations and content are saved in the admin-only parameter masar_website.editorial_ar_20260920.backup; the source and result are also retained there.

Emergency rollback (only after reviewing subsequent edits): set MASAR_CONTENT_ROLLBACK=2026-09-20-ar-content-v1 and run rollback_content.py as a controlled pre-deploy. It restores original pointers and menus, hides/deactivates only newly-created records, and retains content and the rollback audit record. Do not run concurrently with editorial changes.

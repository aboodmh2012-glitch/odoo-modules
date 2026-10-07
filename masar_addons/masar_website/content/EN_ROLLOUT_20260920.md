# English publication rollout

Read-only inspection completed against production MASAR website 1 on 2026-09-20 at 06:36 UTC, deployment `76eacfef-b22a-41b3-b166-70df54fe2d63`.

- Enabled languages: ar_001 and en_US.
- 31 existing managed pages: 17 public, 14 private review drafts.
- 27 visitor-facing navigation entries checked; their English labels were already translated. The internal, non-visible root is intentionally excluded.
- English source hash: `df59011db12b4cfae32a1e5ca16f48082c0e564e3eac9ddfa785237a7ddc92a1`.
- Inspected live-plan hash: `5adbb56b6ad4a794fcfe1c422224774a28af9b1b1f876f6f4ea2f146bba76c5e`.

The next deployment is configured to apply the translation only if this plan still matches. The importer retains the Arabic layout and metadata, all page/view IDs, URL paths, publication state and access groups. Any failed invariant rolls back the transaction. The English and Arabic HTTP probes run after startup; this document is not yet a claim that those probes passed.

After successful application and HTTP verification, clear the one-shot pre-deploy command and English apply/probe flags. Preserve the source and admin-only backup for later review and controlled rollback.

# English verification in progress

The English translation was committed to Odoo on 2026-09-20 at 06:38:52 UTC. All 31 existing page/view identities and publication states were retained. The 17 public English pages passed body text, H1, SEO title and description, language and direction checks. Fourteen translated review drafts remain hidden. The original Arabic checks passed for 17 public pages, 14 hidden drafts and five existing routes both locally and on the public domain.

Language-switch verification is being checked against the installed Odoo 19 behavior. The native JavaScript does not simply follow the selector href: it calls `/website/lang/<url_code>?r=<href>` and relies on locale cookies and redirects. An empty homepage href is valid input to that handler. Read-only diagnostics inspect the returned locale preference and redirects, without recording session cookies or any credentials.

The English apply flag is disabled after the successful transaction. No further content writes are part of these diagnostics.

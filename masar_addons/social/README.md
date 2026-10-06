# Social — Odoo 19 Community

Native Social workspaces with optional integrations. Install `social` alone for
accounts, drafts, editorial review, targets, scheduling, inbox, connections and
publication count reports. No platform credentials are required to install.

Link platforms from **Configuration → Social Media** (same Link account layout as
Odoo Social Marketing). Connected records live under **Configuration → Social Accounts**.

Optional addons: `social_telegram`, `social_meta` (+ `social_facebook`,
`social_instagram`), `social_crm`, `social_helpdesk`, `social_mcp`.
CRM and Helpdesk actions create the original Odoo/OCA records under the caller's
permissions. Internal chatter notes never send a message to a social platform.

## Setup in a disposable database

1. Install Python dependency `openupgradelib`, plus the existing MCP dependencies
   if installing the MCP bridge. Odoo's `base_sparse_field` must be on addons_path.
2. Install `social` and the desired bridges. Assign Operator, explicit Publisher,
   Manager, and/or Connection Administrator. Connection administration alone
   does not confer permission to publish or reply.
3. Add an account's company and explicit account members. Configure Tier
   Validation rules for model `social.post` when editorial approval is required.
4. Configure the OCA queue_job runner: add `queue_job` to server-wide modules,
   configure workers and `root:2,root.social:1` channels. See vendored queue_job
   documentation. Production bootstrap/config changes are a separate rollout.
5. Draft a post, select accounts, request review when required, approve content,
   then Publish / schedule. Each account has its own delivery outcome.

## Social Accounts (one page)

**Social → Configuration → Social Accounts**

Platform cards with **Link account**. First time only (admin): enter Meta App ID +
Secret once, then Facebook Login → choose Page. Later clicks open Facebook directly.

Prefer Railway `SOCIAL_META_APP_ID` / `SOCIAL_META_APP_SECRET` so the form never appears.


## Telegram connection

Use a dedicated bot and a test channel where it has posting permission. A
Social account identifies a bot connection and its default publication chat;
do not configure the same bot on multiple Social account webhook routes.
Set token and webhook secret as server environment variables, e.g.
`SOCIAL_TELEGRAM_TOKEN` and `SOCIAL_TELEGRAM_WEBHOOK_SECRET`. In Social enter
only these variable **names**. Configure a random webhook route key, the target
chat ID, publishing/messaging capability flags, and a dedicated active internal
Webhook Operator who belongs to the account's company and member list.

Use Telegram `setWebhook` through a secure administrative client with URL
`https://your-host/social/telegram/<route-key>` and `secret_token` matching the
server secret. Do not paste tokens into chatter, source control or command logs.
This module does not register webhooks or send test messages during installation.

Supported: plain text publishing, one JPEG/PNG image or MP4 video with caption,
private incoming text updates and outgoing text replies. Telegram users must
initiate a bot conversation. Albums, incoming attachments, public comment
monitoring, editing/deletion, OAuth and advanced metrics are not implemented.

## Facebook Page and Instagram Business

Shared Meta helpers live in `social_meta`. Graph traffic goes through the official
**Facebook Business SDK for Python** (`facebook-business` **v26** → Graph **v26.0**),
not ad-hoc `requests` to `graph.facebook.com`. See
[facebook/facebook-python-business-sdk](https://github.com/facebook/facebook-python-business-sdk)
and `social_meta/models/sdk.py`.

Install `social_facebook` and/or `social_instagram` on top.

**Preferred:** Connect Facebook (OAuth) so Page ID + Page token are stored automatically.

**Legacy / Telegram-style env vars** (optional fallback when not using OAuth):

| Field | Example env name | Purpose |
| --- | --- | --- |
| Token | `SOCIAL_FACEBOOK_PAGE_TOKEN` / `SOCIAL_INSTAGRAM_PAGE_TOKEN` | Long-lived Page access token with publish + comment scopes |
| Webhook verify token | `SOCIAL_FACEBOOK_VERIFY_TOKEN` / `SOCIAL_INSTAGRAM_VERIFY_TOKEN` | Random string Meta sends as `hub.verify_token` on subscription |
| Meta app secret | `SOCIAL_META_APP_SECRET` | App Secret for `X-Hub-Signature-256` on POST webhooks |

Also set Page ID or Instagram Business Account ID as the external account ID, a
unique webhook route key, messaging/publishing flags, and a Webhook Operator who
is an active internal account member with Social User access.

Subscribe Meta webhooks to:

- Facebook: `https://your-host/social/facebook/<route-key>` (Page `feed` comments)
- Instagram: `https://your-host/social/instagram/<route-key>` (`comments` / `live_comments`)

Use the same verify token stored in the server env. Do not paste Page tokens or
the App Secret into the UI, chatter, git or command logs. Connectors never call
Meta during module install.

Supported today:

- Facebook: text feed posts; one JPEG/PNG or MP4 with caption; inbound Page feed
  comments and outbound comment replies.
- Instagram: one **JPEG** (Meta does not accept PNG) via Content Publishing API
  (public image URL from an Odoo attachment access token); inbound comment
  webhooks and comment replies. After publish, Social stores the Graph
  `permalink` when available (never a guessed shortcode URL).

Step-by-step Meta app, env, webhook and smoke-test checklist:
[`docs/SOCIAL_META_SETUP.md`](../../docs/SOCIAL_META_SETUP.md).
Research notes (Meta + Odoo + Zoho Link flow):
[`docs/META_FACEBOOK_LINK.md`](../../docs/META_FACEBOOK_LINK.md).

Not in this release: Messenger/IG Direct, OAuth in-app, media albums, story
publishing, insights/metrics, editing/deletion, or automatic webhook
subscription from Odoo.

Instagram publishing requires `web.base.url` to be a public HTTPS origin Meta
can fetch. Local or private hosts will fail at the container creation step.

## Delivery guarantees and recovery

All external sends and inbound processing run through queue_job. HTTP timeouts
and unknown responses become **Check platform**, never automatic resends.
A small private `social.attempt` checkpoint persists before outbound HTTP using
an independent database cursor (not the queue transaction). A successful provider
ID survives local rollback; worker crashes with an unknown outcome require manual
inspection. The table has no user ACL, bodies, credentials or foreign keys.
Confirmed rate limits retry with exponential delay up to five attempts. Known
permanent failures can be retried by a Publisher after fixing their cause.

If an outcome is uncertain, inspect the platform before creating a replacement
post or reply. This release deliberately has no button that blindly retries
unknown outcomes. Back up checkpoint data with the database; do not purge while
jobs can still be replayed. Configure proxy/access log redaction for provider URLs.

## MCP and later AI

`social_mcp` registers draft creation, an ACL-filtered work summary and review
requests with the existing MCP server. Enable the Social models and operations
using its normal permission configuration. No publish tool, LLM provider, auto
reply, or AI dependency is added. Use a dedicated non-Publisher MCP user for
assisted drafting; existing generic MCP tools remain governed by MCP permissions.

## Current scope

Dashboard is a native post work overview. Analytics are actual publication
counts/statuses, not engagement estimates. Monitor is a separate filtered public
interaction workspace; it stays empty until a suitable connector is installed.
**Inbox** is a unified interaction list (channel chips, type/priority/status
filters, avatar + platform badge, message preview) with native forms for reply.
Connections use native forms. Unified unread tracking, round robin, analyst-only
aggregates, contact matching suggestions, knowledge retrieval, meeting shortcuts,
sales attribution, extra platforms and advanced marketing AI remain subsequent
milestones.

## Validation

GitHub Actions installs the Social suite on Odoo 19/PostgreSQL, runs connector
and bridge tests, then upgrades the modules. Tests cover company/account access,
credential fields, workflow enforcement, tier review, independent targets,
scheduling, cancellation, uncertain outcomes, durable checkpoints, message
deduplication, explicit replies, contact conversion, original CRM/Helpdesk
permissions, Meta signature verification and Graph error classification.
No test requires production credentials or calls a live platform.

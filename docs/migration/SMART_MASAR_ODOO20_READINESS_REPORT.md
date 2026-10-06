# SMART / MASAR Odoo 20 Readiness Report

**Status:** AUDIT DONE → Phase A scaffold STARTED (awaiting MASAR source for COPY)  
**Date:** 2026-10-06  
**Scope:** Read-only audit of SMART lab + prepare SMART for MASAR module COPY (native-first)  
**Hard rules honored:**
- MASAR Production: **NOT TOUCHED** (no commit/push/PR/Railway/SQL/module ops)
- No MASAR DB clone / no Odoo 19→20 DB migration started
- No Railway service delete/stop/volume change
- No `-i all` / `-u all` executed by this audit

### Other agents — did they migrate MASAR modules?

| Agent | What it did | MASAR module COPY? |
|-------|-------------|--------------------|
| إعداد Odoo Railway smart | Odoo **18** SMART baseline + volumes | **No** |
| Railway browser login agents | Failed auth | **No** |
| This agent (جاهزية أودو 20 سمارت) | Audit report + SMART Odoo 20 scaffold | **Blocked** — no read access to `smartexsoftorg/masar` |

**Conclusion:** No other agent copied/migrated MASAR modules. This agent will do it **after** MASAR source is readable. Employee customizations will be evaluated **native-first** (see `EMPLOYEE_FEATURE_DECISIONS.md`), not blind-copied.

---

## Access limitations (blocking full live Railway inventory)

| Source | Access | Impact |
|--------|--------|--------|
| GitHub `aboodmh2012-glitch/odoo-modules` @ `odoo20-railway` | ✅ Full | Repo audit complete |
| Live SMART URL `odoo20-fixed-production.up.railway.app` | ✅ Public read-only HTTP | Version/DB/website confirmed |
| Railway API / project `smart` dashboard | ❌ No `RAILWAY_TOKEN` | Cannot list services/volumes/vars/logs via API |
| GitHub `smartexsoftorg/masar` | ❌ HTTP 404 (no read grant) | Full MASAR module inventory incomplete |

**Requested from owner (pending):**
1. `RAILWAY_TOKEN` scoped to SMART only (read audit)
2. Read-only GitHub access to `smartexsoftorg/masar` **or** export of installed-module list

Until those arrive, sections below mark **VERIFIED** vs **INFERRED** vs **BLOCKED**.

---

## 1. SMART Current Architecture

### 1.1 Known Railway project baseline (from prior SMART Odoo 18 agent + PR #1)

| Item | Value | Confidence |
|------|-------|------------|
| Railway project | `smart` | VERIFIED (prior agent + `deploy/RAILWAY.md`) |
| Project ID | `8a3a695d-b1e8-4f1a-8dfc-7c61cd9194a7` | VERIFIED (prior agent) |
| Environment | `production` | VERIFIED (prior agent) |
| Legacy Odoo 18 service | `odoo` | VERIFIED (prior agent) — may still exist |
| Legacy Postgres | `Postgres` / `postgres:16` (16.15) | VERIFIED (prior agent) |
| Legacy DB name | `smart` | VERIFIED (prior agent) |
| Legacy volumes | `postgres-data` → `/var/lib/postgresql/data` (+ `PGDATA=.../pgdata`); `odoo-data` → `/var/lib/odoo` | VERIFIED (prior agent / PR #1) |
| Legacy public URL | `https://odoo-production-3893.up.railway.app` | VERIFIED then; **now HTTP 404** (service removed or domain detached) |

### 1.2 Odoo 20 services observed / reported

| Service | Role (assessment) | Live public probe | Notes |
|---------|-------------------|-------------------|-------|
| **odoo20-fixed** | **Primary / active lab** | ✅ `https://odoo20-fixed-production.up.railway.app` → `/web/health` **pass** | Odoo **20.0-20260926**; DB selector shows only **`odoo20`**; website enabled (`data-website-id=1`); default site title “Home \| My Website” |
| **odoo20** | Experimental / earlier iteration | `odoo20-production.up.railway.app` → **timeout** | Likely stale or unhealthy; do not delete yet |
| **odoo20-module-installer** | Installer / one-shot style | public hostnames → **404** | Commit history shows start scripts that ran `-i base`, then `-i all`, then selected `-i` apps; user reports volume `odoo20-filestore` on this service at `/var/lib/odoo` |
| **Postgres20** | Intended Odoo 20 DB | API BLOCKED | Target design: PostgreSQL **17** |
| **Postgres** | Legacy Odoo 18 DB | API BLOCKED | Keep isolated from Odoo 20 |

### 1.3 Live SMART Odoo 20 facts (VERIFIED via public HTTP)

| Check | Result |
|-------|--------|
| Image/runtime series | Odoo **20.0** (`server_version`: `20.0-20260926`) |
| Database visible in selector | **`odoo20` only** |
| Website | Installed / active (homepage, `/shop`, `/slides`, `/event`, `/jobs`, `/contactus`) |
| Arabic / RTL on default site | **Not present** on clean lab site |
| Helpdesk public route | `/helpdesk` → 404 (not installed or no website page) |
| Database manager | **Exposed** (`list_db=True`); UI warns *“Odoo database manager is not protected”* |

### 1.4 Repo branch `odoo20-railway` (VERIFIED)

| Artifact | Path | Finding |
|----------|------|---------|
| Root Dockerfile | `Dockerfile` | `FROM odoo:20.0`; installs `gosu`; copies `odoo20/odoo.conf` + `odoo20/start.sh`; **does not bake custom addons** |
| Runtime Dockerfile | `odoo20/Dockerfile` | Clean `odoo:20.0` variant (also no addons bake) |
| Config | `odoo20/odoo.conf` | `data_dir=/var/lib/odoo`; `addons_path` core + `/mnt/extra-addons`; `proxy_mode=True`; `list_db=True`; `workers=0` |
| Entrypoint | `odoo20/start.sh` | **On every start:** `chown` `/var/lib/odoo`, then **`odoo -d odoo20 -i <long APPS list> --stop-after-init`**, then start server |
| Railway config | `railway.toml` | Dockerfile builder; healthcheck `/web/health`; restart on failure |
| Custom/OCA addons for MASAR | — | **Not present** on this branch for Odoo 20 (branch still contains Blue Fox Odoo 18 module tree from `main`, but Odoo 20 image **does not COPY them**) |
| Migration scripts | — | **None** for MASAR DB |

**Apps currently forced by `start.sh` (Community install list):**  
`account,crm,sale_management,purchase,stock,point_of_sale,project,hr,hr_recruitment,hr_holidays,hr_attendance,hr_expense,website,website_sale,website_slides,website_event,mass_mailing,mass_mailing_sms,calendar,contacts,survey,fleet,maintenance,repair,mrp,lunch,im_livechat,project_todo`

### 1.5 Why three Odoo 20 services exist (INFERRED)

| Service | Why it likely exists | Keep / retire recommendation |
|---------|----------------------|------------------------------|
| `odoo20` | First experimental deploy of `odoo:20.0` | Retire **after** confirming no unique volume/domain; not now |
| `odoo20-module-installer` | Used to run heavy `-i` installs; appears to hold **`odoo20-filestore`** volume | Treat as **volume owner** until filestore is re-attached to primary; then retire |
| `odoo20-fixed` | Stabilized runtime after permission/init issues; currently the only healthy public service | **Designate as primary Odoo 20** |

### 1.6 Database / filestore conflict risk

| Risk | Assessment |
|------|------------|
| Two Odoo services writing same DB `odoo20` | **HIGH if** `odoo20` and/or installer still share Postgres20 + DB name with `odoo20-fixed` |
| Installer re-running `-i` while primary serves traffic | **HIGH** — `start.sh` still runs selected `-i` on every boot |
| Filestore split | **HIGH** — volume reported on installer; **not** confirmed on `odoo20-fixed` → attachments may be ephemeral on primary |
| Legacy `Postgres` (16) vs `Postgres20` | OK if Odoo 20 only uses Postgres20; **do not** point Odoo 20 at legacy `smart` DB |

---

## 2. Problems Found

### P0 — Blocking / dangerous

1. **No Railway API token** → cannot complete authoritative service/volume/var/deployment audit.  
2. **No MASAR repo read access** → cannot build definitive module inventory / security ACL review.  
3. **`odoo20/start.sh` re-installs modules on every container start** (`-i` selected apps). Violates module-by-module policy; slows boots; can race if multiple services share DB.  
4. **Historical `-i all` was used** (commit `4e9c335` on `odoo20-railway`) — lab DB may be inconsistent; do not repeat.  
5. **Filestore persistence mismatch** — volume on installer, not confirmed on `odoo20-fixed`. Redeploy of primary may lose attachments/images/documents.  
6. **Database manager unprotected** on public URL (`list_db=True` + manager warning).

### P1 — Architecture debt

7. Three overlapping Odoo 20 services without documented single-writer ownership.  
8. Dual Postgres (`Postgres` + `Postgres20`) without published wiring diagram.  
9. Odoo 20 image does **not** bake MASAR-compatible custom addons; `/mnt/extra-addons` empty at runtime from current Dockerfile.  
10. `railway.toml` / branch mix: Odoo 18 deploy docs still describe Symbifox/`odoo:18.0` while `odoo20-railway` root Dockerfile is Odoo 20 — confusing for operators.  
11. Clean website has **no Arabic/RTL/MASAR theme** — expected for empty lab, but shows MASAR website work not started on SMART.

### P2 — Process

12. Legacy Odoo 18 public domain gone (404) while Postgres/volumes may still exist — clarify whether Odoo 18 service remains.  
13. No approved DB-clone phase gate artifact yet (correctly deferred).

---

## 3. Recommended SMART Architecture

```
SMART (Railway project: smart)
│
├── odoo20-fixed          ← SINGLE primary Odoo 20 service
│   image: custom build FROM odoo:20.0 (repo aboodmh2012-glitch/odoo-modules @ odoo20-railway)
│   start: normal server ONLY (no -i/-u on boot)
│   volume: odoo20-filestore → /var/lib/odoo   (attachments/sessions)
│   DB: Postgres20 / database odoo20 (lab) — later: odoo20_masar_clone (phase 2+)
│
├── Postgres20            ← PostgreSQL 17
│   volume: postgres20-data → /var/lib/postgresql/data
│
├── (optional) odoo20-installer  ← ONE-SHOT job service, STOPPED when idle
│   same image; runs explicit module-by-module -i under change control
│   MUST use same DB + same filestore volume as primary OR none at all
│
├── Postgres (legacy 16) + odoo (legacy 18)  ← freeze or delete later; never wire to Odoo 20
│
└── MASAR Railway project                 ← 🔒 READ-ONLY / NEVER MODIFY
```

**Design rules:**
- Exactly **one** long-running Odoo writer per database.  
- Filestore volume **must** mount on the primary (`odoo20-fixed`).  
- Installer must be stopped after use.  
- Never point SMART Odoo 20 at MASAR production DB.  
- Module installs: dependency-ordered, module-by-module — **never** `-i all` / `-u all`.

**Volume move recommendation (do not execute until approved):**  
Attach/move `odoo20-filestore` (or create new dedicated volume) to `odoo20-fixed` at `/var/lib/odoo`, confirm persistence with a test attachment + redeploy, **then** consider stopping installer/`odoo20`.

---

## 4. MASAR Module Inventory

### 4.1 Status

**BLOCKED for definitive list** — `smartexsoftorg/masar` not readable with current GitHub token.

### 4.2 Expected functional areas (from stakeholder brief — to verify against MASAR code)

| Area | Expected components | Inventory status |
|------|---------------------|------------------|
| HR | Employees, Contracts, Recruitment, Attendance, Leave, Payroll/salary rules, documents, Sign, appraisal, disciplinary, resignation, transfer, org chart | PENDING MASAR read |
| Website | MASAR theme, AR/EN, RTL/LTR, homepage, login, jobs, SEO/OG, favicon, mobile | PENDING |
| Communications | Email, Discuss, aliases, Unified Inbox, CRM, Helpdesk, external channels | PENDING |
| Governance / Knowledge | Governance, approvals, board/committees, Knowledge | PENDING |
| Import | `excel_import_mapper`, Import Hub, mappings, scheduled imports | PENDING |
| Security | ACL, record rules, groups, portal/public/employee/manager/HR/admin | PENDING |
| Integrations | Third-party / OCA / custom bridges | PENDING |

### 4.3 Provisional source classification (until MASAR tree is readable)

| Source bucket | Examples to expect | Action when found |
|---------------|--------------------|-------------------|
| MASAR custom | theme, HR extensions, website customizations, security hardenings | COPY → SMART → migrate (never edit MASAR) |
| OCA | whatever MASAR vendors via OCA | Pin Odoo 20-compatible fork/branch in SMART |
| Third-party | `excel_import_mapper`, Sign alternatives, Helpdesk CE, etc. | Check Odoo 20 release; else REPLACE/MIGRATE |
| Odoo Core | Community apps already in SMART `start.sh` list | KEEP / use native where sufficient |

---

## 5. Odoo 20 Compatibility Matrix

> Full per-module rows require MASAR inventory. Below: **confirmed SMART lab modules** + **priority MASAR capability rows** with provisional actions.

### 5.1 SMART lab — Community apps (present / targeted)

| Module | Source | MASAR 19 | Odoo 20 | Dependencies | Action |
|--------|--------|----------|---------|--------------|--------|
| base / web | Odoo Core | Y | Y (lab) | — | KEEP |
| contacts | Odoo Core | likely | Y | base | KEEP |
| hr | Odoo Core | Y | Y | base | KEEP — review Odoo 20 HR API changes |
| hr_recruitment | Odoo Core | Y | Y | hr, website* | KEEP |
| hr_holidays | Odoo Core | Y | Y | hr | KEEP — check day-count changes |
| hr_attendance | Odoo Core | Y | Y | hr | KEEP |
| hr_expense | Odoo Core | Y | Y | hr | KEEP |
| website | Odoo Core | Y | Y | — | KEEP — theme still custom |
| website_sale | Odoo Core | ? | Y (lab) | website | INVESTIGATE need for MASAR |
| website_slides | Odoo Core | ? | Y (lab) | website | INVESTIGATE |
| website_event | Odoo Core | ? | Y (lab) | website | INVESTIGATE |
| crm | Odoo Core | likely | Y | — | KEEP |
| project | Odoo Core | likely | Y | — | KEEP |
| mass_mailing (+ sms) | Odoo Core | likely | Y | — | KEEP |
| calendar | Odoo Core | likely | Y | — | KEEP |
| account / sale / purchase / stock / mrp / pos / fleet / maintenance / repair / lunch / survey / im_livechat / project_todo | Odoo Core | mixed | Y (forced by start.sh) | — | **INVESTIGATE** — shrink boot install list to MASAR-required only |

### 5.2 MASAR priority capabilities (provisional)

| Capability / Module | Source | MASAR 19 | Odoo 20 Community | Dependencies | Action |
|---------------------|--------|----------|-------------------|--------------|--------|
| MASAR website theme | MASAR custom | Y | N/A | website | COPY & MIGRATE |
| Arabic + English + RTL/LTR | MASAR / website | Y | Partial native i18n | website | COPY & MIGRATE (theme/layout) |
| Jobs / recruitment site | Core + custom | Y | Y core `/jobs` | hr_recruitment, website | MINOR FIX / keep custom only if MASAR-specific |
| Employee documents / attachments | Core + custom | Y | Y (filestore) | hr, attachment | KEEP core; ensure persistent volume |
| Org chart | Custom / OCA / Enterprise-ish | Y | Limited CE | hr | INVESTIGATE — may COPY & MIGRATE |
| Payroll / salary rules | Often Enterprise / custom | Y? | **Enterprise-only** in standard Odoo | hr | MAJOR MIGRATION or keep custom CE payroll — **INVESTIGATE** |
| Sign | Enterprise / custom CE (e.g. bf_sign-like) | Y? | Enterprise-only native | — | REPLACE WITH custom CE **or** INVESTIGATE MASAR’s current Sign stack |
| Appraisals | Enterprise | Y? | Enterprise-only | hr | INVESTIGATE / REPLACE |
| Approvals | Enterprise | Y? | Enterprise-only | — | INVESTIGATE / REPLACE (OCA or custom) |
| Knowledge | Enterprise | Y? | Enterprise-only | — | INVESTIGATE / REPLACE |
| Helpdesk | Enterprise / OCA/custom | Y? | Enterprise-only native | — | INVESTIGATE MASAR implementation |
| Governance / board / committees | Custom | Y? | N/A | — | COPY & MIGRATE if present |
| `excel_import_mapper` / Import Hub | Third-party / custom | Y? | ? | — | INVESTIGATE — do not auto-copy |
| Unified Inbox / mail aliases | Core + custom | Y | Y discuss/mail | mail | KEEP + review custom |
| Security groups / ACL / portal rules | Custom | Y | Y | base | COPY & MIGRATE carefully — **no privilege expansion** |
| `hr_homeworking` (Remote Work) | Odoo 19 module | maybe | **Merged into `hr` in Odoo 20** | hr | REPLACE WITH ODOO 20 NATIVE (`hr` / `hr_calendar`) |
| Public employee directory company rule | Core | Y | Changed in 20 | hr | MINOR FIX — company domain no longer on `hr.employee.public` by default |

---

## 6. Odoo 20 Native Replacements

Prefer **not** copying custom code when Community Odoo 20 covers the need:

| Odoo 19 / custom pattern | Odoo 20 native direction | Copy custom? |
|--------------------------|--------------------------|--------------|
| Separate Remote Work (`hr_homeworking`) | Built into Employees | **No** — retarget deps to `hr` / `hr_calendar` |
| Rigid working schedules only | `resource.calendar` `calendar_type` (fixed/variable/undefined) | Only if MASAR has special rotation logic beyond native |
| Basic jobs portal | `hr_recruitment` + website jobs | Only if MASAR theme/SEO/AR UX differs |
| Generic contacts/CRM/project/mail | Core Community apps | No |
| Multi-company public directory filtering assumptions | Core behavior changed | Fix consumers; don’t reintroduce old rule blindly |

**Still expect custom (not replaceable by CE native):** MASAR theme/branding, AR+EN UX, governance packs, import mappers, any CE substitutes for Enterprise Sign/Helpdesk/Knowledge/Payroll/Approvals.

---

## 7. Required Migrations (code — future SMART work only)

When MASAR modules are **copied** into `aboodmh2012-glitch/odoo-modules` (never moved from MASAR):

### Python
- Manifest `version` → `20.0.*`; drop removed deps (`hr_homeworking`, etc.)
- ORM/API: `sudo` usage review; `mail.thread` / activities; cron methods
- Field renames (e.g. schedule flexibility APIs → `calendar_type` / `_is_flexible()`)
- Controllers/auth routes; attachment/`ir.attachment` paths
- Create/write overrides, computes, constraints, onchange

### XML
- `tree` → `list` where still needed; form/kanban/search inheritance
- Broken xpath after core view changes; XML IDs; QWeb/website templates; reports; assets bundles

### JS / OWL
- Registry/service/hook import paths; patches; website frontend assets for theme RTL

### Security
- Re-diff every `ir.model.access.csv` + record rules vs MASAR 19  
- Ensure portal/public/employee/manager implications do **not** widen

---

## 8. Blocking Issues

| ID | Blocker | Needed to unblock |
|----|---------|-------------------|
| B1 | No Railway API token for SMART | Add `RAILWAY_TOKEN` (SMART-only) |
| B2 | No read access to `smartexsoftorg/masar` | Grant read-only GitHub access or export module list |
| B3 | Filestore not proven on primary service | After approval: attach volume to `odoo20-fixed`, persistence test |
| B4 | Boot-time `-i` in `start.sh` | After approval: change start to serve-only; installer as separate one-shot |
| B5 | Unprotected DB manager on public URL | After approval: set master password / `list_db=False` on lab |
| B6 | MASAR DB migration | Explicit human approval for Phase 2 only |

**Not blockers for lab bring-up:** missing MASAR theme (expected on clean DB).

---

## 9. Security Risks

| Risk | Severity | Notes |
|------|----------|-------|
| Public database manager unprotected | **Critical (lab)** | Anyone who can reach URL + guess master password can drop/restore DBs |
| `list_db=True` | High | Enables DB enumeration |
| Multi-service same DB | High | Corruption / race during installs |
| Ephemeral filestore on primary | High | Data loss of attachments/docs/images on redeploy |
| Privilege expansion during module port | High | Must diff ACL/rules module-by-module |
| Accidental MASAR production ops | Critical (prevented) | Continue hard isolation; no MASAR Railway credentials in SMART agents |
| Odoo 20 directory visibility change | Medium | Broader `hr.employee.public` visibility across companies — review MASAR multi-company expectations |

**MASAR Production:** no changes performed; treat as out-of-band forever for this lab.

---

## 10. Migration Sequence (proposed — not started)

### Phase A — Stabilize SMART lab (next approval gate)
1. Obtain Railway token → finish live service/volume/var map.  
2. Designate `odoo20-fixed` as sole writer; document DB=`odoo20`, Postgres20.  
3. Attach persistent filestore to primary; persistence test (upload → redeploy → verify).  
4. Change `start.sh` to **serve only** (no boot `-i`).  
5. Harden lab (`list_db`, master password).  
6. Stop/park installer + experimental `odoo20` **only after** filestore ownership clarified.

### Phase B — Module lab (clean DB)
1. Gain MASAR read inventory → finalize Compatibility Matrix.  
2. COPY modules MASAR→SMART (new paths under SMART repo).  
3. Install **module-by-module** in dependency order on clean `odoo20` (or fresh `odoo20_lab`).  
4. Fix Python/XML/JS/security per module; prefer native CE replacements.

### Phase C — Functional parity tests (still no prod DB)
HR, Website AR/EN, Communications, Governance/Knowledge substitutes, Import Hub.

### Phase D — DB migration rehearsal (**explicit approval required**)
1. Neutralized dump of MASAR (copy) → restore to SMART Postgres20 as `odoo20_masar_clone`.  
2. Filestore copy into SMART volume.  
3. OpenUpgrade / version upgrade path Odoo 19→20 on the **clone only**.  
4. Module update pass module-by-module (never `-u all`).  
5. Security regression + UAT.  
6. Only later: production cutover plan (separate approval).

---

## 11. Database Migration Plan (future only — DO NOT EXECUTE)

```
MASAR PROD (Odoo 19 + PG + filestore)
        │  READ-ONLY snapshot / neutralized dump
        │  (explicit approval)
        ▼
SMART Postgres20  ← restore as odoo20_masar_clone
SMART filestore volume ← copy attachments
        │
        ▼
Odoo 20 binary + migrated SMART addons
        │  module-by-module -u
        ▼
UAT on SMART URLs only
        │
        ✖  no write-back to MASAR
```

**Pre-reqs before Phase D:** Phase A+B green; Compatibility Matrix signed; security ACL diff signed; rollback drill on SMART.

---

## 12. SMART Repo Audit Summary (`odoo20-railway`)

| Topic | Finding |
|-------|---------|
| Dockerfile | Odoo 20 clean image; gosu; root entry for chown |
| requirements.txt | Still Odoo 18 / Blue Fox oriented on branch lineage — **not wired into Odoo 20 Dockerfile** |
| odoo.conf | Minimal; OK for lab; `list_db=True` too open |
| addons_path | core + `/mnt/extra-addons` (empty in image) |
| entrypoint | `start.sh` with boot-time `-i` ⚠️ |
| Railway config | Present; healthcheck OK |
| scripts | Only `odoo20/start.sh` for Odoo 20 |
| custom / OCA / third-party for MASAR | **Not yet copied** |
| migration scripts | **None** |

---

## 13. Recommendations (awaiting approval — not executed)

1. Provide `RAILWAY_TOKEN` (SMART) + MASAR GitHub read.  
2. Approve Phase A only: filestore on `odoo20-fixed`, serve-only start, lab hardening.  
3. Do **not** delete services until filestore/DB ownership map is API-confirmed.  
4. Do **not** clone MASAR DB yet.  
5. Keep MASAR Railway project credentials out of this lab workflow.

---

## 14. STOP

Per instructions:

- ✅ Audit artifacts produced  
- ⛔ No MASAR changes  
- ⛔ No DB migration  
- ⛔ No Railway mutations  
- ⛔ No volume moves  
- ⏳ Waiting for access + explicit approval before Phase A implementation

---

### Appendix A — Commit trail (Odoo 20 lab evolution)

| Commit | Meaning |
|--------|---------|
| `1e4af6e` / `79b7b6c` / `cc7b57b` | Add Odoo 20 Dockerfile/conf/start |
| `15d3900` | Boot `-i base` |
| `b856471` | Normal start |
| `58c452e` / `82bfc12` | gosu + volume chown |
| `4e9c335` | **`-i all`** (do not repeat) |
| `4557ea6` | Selected Community apps `-i` on every start (**current**) |

### Appendix B — Live URLs checked (read-only)

| URL | Result |
|-----|--------|
| `https://odoo20-fixed-production.up.railway.app/web/health` | pass |
| `https://odoo-production-3893.up.railway.app` | Application not found |
| `https://odoo20-module-installer-production.up.railway.app` | 404 |
| MASAR GitHub | inaccessible |
| MASAR Railway project | **not queried with write tools**; public hostnames only lightly checked |

### Appendix C — Safety confirmation

| Action | Done? |
|--------|-------|
| Modify `smartexsoftorg/masar` | No |
| Railway project MASAR changes | No |
| SMART Railway mutations | No |
| SQL writes / module install on any env | No |
| Production filestore changes | No |

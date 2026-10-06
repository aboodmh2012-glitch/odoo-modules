"""Controlled transactional import into the existing Odoo 19 MASAR website.
Run --inspect first, then --apply with MASAR_CONTENT_APPLY set to VERSION.
No modules, accounts, credentials or financial data are changed.
Backups and editorial notes remain in admin-only ir.config_parameter records.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote
from lxml import etree

from content_engine import (VERSION, SOURCE_SHA256, PUBLIC_SLUGS, REVIEW_PREFIX,
                            STYLE_KEY, MARKER_KEY, NAVIGATION,
                            load_source, target_url, view_key, build_arch, style_arch)


def log(event, **values):
    print("[masar-content] " + json.dumps({"event": event, **values}, ensure_ascii=False, default=str), flush=True)


def connect():
    import odoo
    from odoo.orm.registry import Registry
    uri = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_PRIVATE_URL")
    if uri:
        u = urlparse(uri)
        host, port = u.hostname, u.port or 5432
        user, password = unquote(u.username or ""), unquote(u.password or "")
        database_from_url = (u.path or "").lstrip("/")
    else:
        host = os.environ.get("PGHOST") or os.environ.get("POSTGRES_HOST")
        port = int(os.environ.get("PGPORT") or os.environ.get("POSTGRES_PORT") or "5432")
        user = os.environ.get("PGUSER") or os.environ.get("POSTGRES_USER") or "odoo"
        password = os.environ.get("PGPASSWORD") or os.environ.get("POSTGRES_PASSWORD") or ""
        database_from_url = os.environ.get("PGDATABASE") or ""
    # Match the dedicated application role selected by the existing entrypoint.
    if user == "postgres" or os.environ.get("ODOO_DB_USER"):
        user = os.environ.get("ODOO_DB_USER") or "masar"
        password = os.environ.get("ODOO_DB_PASSWORD") or password
    db = os.environ.get("ODOO_DB_NAME") or (database_from_url if database_from_url not in ("", "railway", "postgres") else "masar")
    if not host or not user or not password:
        raise RuntimeError("Required application database configuration is absent")
    odoo.tools.config.parse_config([
        "-c", "/dev/null", "-d", db, "--no-http", "--max-cron-threads=0",
        "--addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons",
        "--db_host=" + host, "--db_port=" + str(port), "--db_user=" + user,
        "--log-level=warn",
    ])
    odoo.tools.config["db_password"] = password
    return odoo, Registry.new(db)


def select_page(env, website, url):
    Page = env["website.page"].with_context(active_test=False)
    specific = Page.search([("url", "=", url), ("website_id", "=", website.id), ("active", "=", True)], order="id")
    if len(specific) > 1:
        raise RuntimeError("Multiple active website-specific pages at " + url + "; manual reconciliation required")
    if specific:
        return specific
    generic = Page.search([("url", "=", url), ("website_id", "=", False), ("active", "=", True)], order="id")
    if len(generic) > 1:
        raise RuntimeError("Ambiguous generic page at " + url)
    return generic


def inspect(env, source):
    website = env.ref("website.default_website")
    if website.name.upper() != "MASAR":
        raise RuntimeError("Target is not the expected MASAR website")
    if website.homepage_url not in (False, "", "/"):
        raise RuntimeError("A custom homepage URL needs review before import")
    arabic = website.language_ids.filtered(lambda lang: lang.code.startswith("ar"))
    if len(arabic) != 1:
        raise RuntimeError("Expected one enabled Arabic website language")
    log("inventory", website_id=website.id, languages=website.language_ids.mapped("code"),
        default_language=website.default_lang_id.code, source_sha256=SOURCE_SHA256,
        public_count=len(PUBLIC_SLUGS), draft_count=len(source["pages"])-len(PUBLIC_SLUGS))
    plan = []
    for record in source["pages"]:
        target = target_url(record)
        existing = select_page(env, website, target)
        if existing and target.startswith(REVIEW_PREFIX):
            raise RuntimeError("Review URL already occupied: " + target)
        if existing and existing.view_id.key == view_key(record["slug"]):
            raise RuntimeError("Existing managed view but missing success marker; inspect before reapplying")
        plan.append((record, target, existing))
        log("plan", url=target, name=record["name"], existing_page_id=existing.id if existing else None,
            existing_view_key=existing.view_id.key if existing else None,
            published=record["slug"] in PUBLIC_SLUGS)
    # Inspect navigation before any mutation as well.
    root = website.menu_id
    if not root:
        raise RuntimeError("The current website has no menu root")
    for menu in env["website.menu"].search([("website_id", "=", website.id), ("parent_id", "=", root.id)], order="sequence,id"):
        log("current_menu", id=menu.id, name=menu.name, url=menu.url, page_id=menu.page_id.id)
    return website, arabic, plan


def snapshot_view(view, languages):
    return {
        "id": view.id, "key": view.key, "name": view.name,
        "website_id": view.website_id.id, "inherit_id": view.inherit_id.id,
        "active": view.active,
        "arch_db": {lang: view.with_context(lang=lang).arch_db for lang in languages},
    }


def apply(env, source, website, arabic, plan):
    if os.environ.get("MASAR_CONTENT_APPLY") != VERSION:
        raise RuntimeError("Explicit content-apply guard is not enabled")
    Params = env["ir.config_parameter"]
    if Params.get_param(MARKER_KEY):
        log("already_applied", version=VERSION)
        return
    if env["ir.ui.view"].search_count([("key", "=", STYLE_KEY)]):
        raise RuntimeError("Unexpected existing shared styles view")
    languages = list(set(["en_US", arabic.code] + website.language_ids.mapped("code")))
    backup = {
        "version": VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
        "source_sha256": SOURCE_SHA256, "website_id": website.id,
        "old_pages": [], "old_menus": [], "new_page_ids": [], "new_view_ids": [], "new_menu_ids": [],
    }
    for record, target, existing in plan:
        if existing:
            backup["old_pages"].append({
                "id": existing.id, "url": existing.url, "view_id": existing.view_id.id,
                "website_published": existing.website_published,
                "website_indexed": existing.website_indexed,
                "view": snapshot_view(existing.view_id, languages),
            })
    Params.set_param(MARKER_KEY + ".editorial_register", json.dumps(source, ensure_ascii=False))
    Style = env["ir.ui.view"].create({
        "name": "MASAR Arabic editorial shared styles", "key": STYLE_KEY,
        "type": "qweb", "arch_db": style_arch(), "website_id": website.id,
    })
    backup["new_view_ids"].append(Style.id)
    current_contact = select_page(env, website, "/contactus")
    contact_available = bool(current_contact and current_contact.website_published)
    results = []
    for record, target, existing in plan:
        public = record["slug"] in PUBLIC_SLUGS
        prior = existing.view_id if existing else None
        prior_key = prior.key if prior else None
        if prior and not prior_key:
            raise RuntimeError("Existing page lacks a stable view key: " + target)
        hero_style = None
        if prior:
            try:
                arch = prior._get_combined_arch()
                sections = arch.xpath("//section[contains(@class, 'hero') or contains(@class, 's_cover')]")
                for section in sections:
                    candidate = section.get("style", "")
                    match = re.search(r"background-image\s*:\s*[^;]+", candidate)
                    if match:
                        hero_style = match.group(0)
                        break
            except (AttributeError, etree.XMLSyntaxError):
                pass
        arch = build_arch(record, source, existing_english_key=prior_key if public else None,
                          contact_available=contact_available, hero_style=hero_style)
        etree.fromstring(arch.encode())
        values = {
            "name": record["name"] if public else "مسودة محتوى — " + record["name"],
            "key": view_key(record["slug"]), "type": "qweb", "arch_db": arch,
            "website_id": website.id, "website_meta_title": record["seo_title"],
            "website_meta_description": record["meta_description"],
        }
        if prior:
            for field in ("website_meta_title", "website_meta_description"):
                values[field] = prior.with_context(lang="en_US")[field] or values[field]
        if not public and "group_ids" in env["ir.ui.view"]._fields:
            values["group_ids"] = [(6, 0, [env.ref("website.group_website_designer").id])]
        view = env["ir.ui.view"].with_context(website_id=website.id, lang="en_US").create(values)
        backup["new_view_ids"].append(view.id)
        view.with_context(lang=arabic.code).write({
            "website_meta_title": record["seo_title"],
            "website_meta_description": record["meta_description"],
        })
        if existing and existing.website_id:
            existing.write({"view_id": view.id, "website_published": public, "website_indexed": public})
            page = existing
        else:
            page = env["website.page"].create({
                "name": values["name"], "url": target, "view_id": view.id,
                "website_published": public, "website_indexed": public,
            })
            backup["new_page_ids"].append(page.id)
        env["ir.qweb"].with_context(website_id=website.id, lang=arabic.code)._compile(view.key)
        results.append({"name": record["name"], "url": target, "intended_url": record["slug"],
                        "page_id": page.id, "view_id": view.id, "published": public,
                        "english_preserved": bool(prior_key), "publishing_gate": record["publishing_gate"]})
        log("page_prepared", **results[-1])
    Menu = env["website.menu"]
    root = website.menu_id
    for seq, (ar_name, en_name, url) in enumerate(NAVIGATION, 20):
        live = select_page(env, website, url)
        if not live or not live.website_published:
            continue
        aliases = {"/solutions": ["/solutions", "/#services"], "/business": ["/business", "/#solutions"],
                   "/about": ["/about", "/#about"]}.get(url, [url])
        menu = Menu.search([("website_id", "=", website.id), ("parent_id", "=", root.id), ("url", "in", aliases)], order="id")
        if len(menu) > 1:
            raise RuntimeError("Duplicate marketing menu destinations require review: " + url)
        vals = {"name": en_name, "url": url, "page_id": live.id,
                "website_id": website.id, "parent_id": root.id, "sequence": seq}
        if menu:
            snapshot = menu.with_context(lang="en_US").read(["name", "url", "page_id", "parent_id", "sequence", "website_id"])[0]
            snapshot["names"] = {lang: menu.with_context(lang=lang).name for lang in languages}
            backup["old_menus"].append(snapshot)
            menu.with_context(lang="en_US").write(vals)
        else:
            menu = Menu.with_context(lang="en_US").create(vals)
            backup["new_menu_ids"].append(menu.id)
        menu.with_context(lang=arabic.code).write({"name": ar_name})
    for row in results:
        p = env["website.page"].browse(row["page_id"])
        if p.website_published != row["published"]:
            raise RuntimeError("Unexpected publication state")
        if not row["published"] and p.website_indexed:
            raise RuntimeError("A private draft must not be indexed")
        if select_page(env, website, row["url"]).id != p.id:
            raise RuntimeError("Another page shadows the imported destination")
    Params.set_param(MARKER_KEY + ".backup", json.dumps(backup, ensure_ascii=False))
    Params.set_param(MARKER_KEY, json.dumps({"version": VERSION, "source_sha256": SOURCE_SHA256,
                     "website_id": website.id, "ar_url_code": arabic.url_code, "results": results}, ensure_ascii=False))
    env.flush_all()
    log("validated", pages=len(results), public=sum(r["published"] for r in results),
        drafts=sum(not r["published"] for r in results), backup_key=MARKER_KEY + ".backup")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.inspect == args.apply:
        parser.error("Choose exactly one of --inspect or --apply")
    source = load_source()
    odoo, registry = connect()
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {"lang": "en_US"})
        cr.execute("SELECT pg_try_advisory_xact_lock(%s)", [2026092031])
        if not cr.fetchone()[0]:
            raise RuntimeError("Another content import is in progress")
        prior = env["ir.config_parameter"].get_param(MARKER_KEY)
        if prior:
            report = json.loads(prior)
            if report.get("source_sha256") != SOURCE_SHA256:
                raise RuntimeError("Stored source identity does not match")
            log("already_applied", report=report)
            return
        website, arabic, plan = inspect(env, source)
        if args.inspect:
            cr.rollback()
            log("inspection_complete", changes=0)
            return
        apply(env, source, website, arabic, plan)
        cr.commit()
        log("committed", version=VERSION)


if __name__ == "__main__":
    main()

"""Inspect, apply or roll back the English translation in the existing pages.

No new pages, publications, groups, modules, financial records or contact forms.
The original Arabic content is retained exactly. Changes are transactional.
"""
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timezone

from content_engine import MARKER_KEY, SOURCE_SHA256, PUBLIC_SLUGS, target_url, view_key
from import_content import connect, select_page
from english_content import (
    EN_VERSION, EN_MARKER, ARABIC, digest, load_english,
    bilingual_arch, arabic_layout, layout_bytes,
)


def log(event, **values):
    print('[masar-en] ' + json.dumps({'event': event, **values}, ensure_ascii=False, default=str), flush=True)


def view_snapshot(view, languages):
    fields = ['arch_db', 'website_meta_title', 'website_meta_description']
    if view._fields['name'].translate:
        fields.append('name')
    return {lang: {f: view.with_context(lang=lang)[f] for f in fields} for lang in languages}


def page_state(page):
    view = page.view_id
    return {
        'page_id': page.id, 'url': page.url, 'view_id': view.id,
        'key': view.key, 'website_id': page.website_id.id,
        'published': page.website_published, 'indexed': page.website_indexed,
        'active': view.active, 'inherit_id': view.inherit_id.id,
        'groups': sorted(view.group_ids.ids) if 'group_ids' in view._fields else [],
    }


def inventory(env, source):
    website = env.ref('base.default_website')
    if website.name.upper() != 'MASAR':
        raise RuntimeError('Wrong website')
    languages = website.language_ids.mapped('code')
    if 'en_US' not in languages or 'ar_001' not in languages:
        raise RuntimeError('Expected enabled English and Arabic languages')
    if website.homepage_url not in ('', '/', False):
        raise RuntimeError('Unexpected homepage destination')
    prior = json.loads(env['ir.config_parameter'].get_str(MARKER_KEY) or '{}')
    if prior.get('source_sha256') != SOURCE_SHA256 or prior.get('website_id') != website.id:
        raise RuntimeError('Approved Arabic release is missing or different')
    managed = {r['intended_url']: r for r in prior.get('results', [])}
    if len(managed) != 31:
        raise RuntimeError('Expected all 31 managed Arabic pages')
    contact = select_page(env, website, '/contactus')
    contact_available = bool(contact and contact.website_published)
    plans = []
    for entry in source['pages']:
        slug = entry['slug']
        page = select_page(env, website, target_url(entry))
        ref = managed[slug]
        if not page or page.id != ref['page_id'] or page.view_id.id != ref['view_id']:
            raise RuntimeError('Managed page identity changed: ' + slug)
        if page.view_id.key != view_key(slug) or page.website_id != website:
            raise RuntimeError('Managed view identity changed: ' + slug)
        state = page_state(page)
        public = slug in PUBLIC_SLUGS
        if state['published'] != public or (not public and state['indexed']):
            raise RuntimeError('Publication gate changed: ' + slug)
        before = view_snapshot(page.view_id, languages)
        current = before['ar_001']['arch_db']
        updated = bilingual_arch(current, entry, source, contact_available)
        plans.append({'slug': slug, 'state': state, 'before': before, 'arch': updated})
        log('page_plan', slug=slug, url=page.url, page_id=page.id, view_id=page.view_id.id,
            published=public, english_title=entry['seo_title'])
    menus = []
    by_url = {p['slug']: p['name'] for p in source['pages']}
    for menu in env['website.menu'].search([('website_id', '=', website.id)], order='id'):
        # Odoo's internal menu-root name is not a visitor-facing navigation label.
        if menu == website.menu_id:
            continue
        names = {lang: menu.with_context(lang=lang).name for lang in languages}
        replacement = None
        if ARABIC.search(names['en_US'] or ''):
            replacement = by_url.get(menu.url)
            if not replacement:
                log('unmapped_menu', id=menu.id, url=menu.url, names=names)
                raise RuntimeError('Untranslated menu needs explicit review: ' + str(menu.id))
        menus.append({'id': menu.id, 'url': menu.url, 'parent': menu.parent_id.id,
                      'names': names, 'replacement': replacement})
    plan_hash = digest({'pages': [{'slug': p['slug'], 'state': p['state'], 'before': p['before']} for p in plans],
                        'menus': menus, 'source': digest(source), 'languages': languages})
    log('inventory', website_id=website.id, languages=languages, pages=len(plans),
        public_pages=17, private_drafts=14, plan_hash=plan_hash, source_hash=digest(source),
        menu_count=len(menus), menu_translations=sum(bool(x['replacement']) for x in menus))
    return website, languages, plans, menus, plan_hash


def apply(env, source, expected):
    if os.environ.get('MASAR_CONTENT_EN_APPLY') != EN_VERSION:
        raise RuntimeError('Explicit English apply guard is not enabled')
    params = env['ir.config_parameter']
    if params.get_str(EN_MARKER):
        existing = json.loads(params.get_str(EN_MARKER))
        if existing.get('source_hash') != digest(source):
            raise RuntimeError('Different English source already applied')
        log('already_applied', version=EN_VERSION)
        return
    website, languages, plans, menus, plan_hash = inventory(env, source)
    if not expected or expected != plan_hash:
        raise RuntimeError('Live content changed since inspection; refusing to overwrite')
    backup = {'version': EN_VERSION, 'time': datetime.now(timezone.utc).isoformat(),
              'website_id': website.id, 'languages': languages, 'pages': [], 'menus': menus}
    by_slug = {p['slug']: p for p in source['pages']}
    for plan in plans:
        page = env['website.page'].browse(plan['state']['page_id'])
        view = page.view_id
        entry = by_slug[plan['slug']]
        backup['pages'].append({'slug': plan['slug'], 'state': plan['state'], 'before': plan['before']})
        vals = {'arch_db': plan['arch'], 'website_meta_title': entry['seo_title'],
                'website_meta_description': entry['meta_description']}
        if view._fields['name'].translate:
            vals['name'] = entry['name'] if plan['state']['published'] else 'Content draft — ' + entry['name']
        view.with_context(website_id=website.id, lang='en_US').write(vals)
        after_ar = view.with_context(lang='ar_001')
        if layout_bytes(arabic_layout(after_ar.arch_db)) != layout_bytes(arabic_layout(plan['before']['ar_001']['arch_db'])):
            raise RuntimeError('Arabic layout changed during ORM write: ' + plan['slug'])
        for field in ('website_meta_title', 'website_meta_description'):
            if after_ar[field] != plan['before']['ar_001'][field]:
                raise RuntimeError('Arabic metadata changed: ' + plan['slug'])
            if view.with_context(lang='en_US')[field] != entry['seo_title' if field.endswith('title') else 'meta_description']:
                raise RuntimeError('English metadata did not persist: ' + plan['slug'])
        if page_state(page) != plan['state']:
            raise RuntimeError('Page identity or publication permissions changed')
        for lang in ('en_US', 'ar_001'):
            env['ir.qweb'].with_context(website_id=website.id, lang=lang)._compile(view.key)
        backup['pages'][-1]['after_hash'] = digest(view_snapshot(view, languages))
        log('page_translated', slug=plan['slug'], page_id=page.id, published=page.website_published)
    for row in menus:
        if row['replacement']:
            menu = env['website.menu'].browse(row['id'])
            menu.with_context(lang='en_US').write({'name': row['replacement']})
            if menu.with_context(lang='ar_001').name != row['names']['ar_001']:
                raise RuntimeError('Arabic menu label changed')
    params.set_str(EN_MARKER + '.backup', json.dumps(backup, ensure_ascii=False))
    params.set_str(EN_MARKER + '.editorial_register', json.dumps(source, ensure_ascii=False))
    params.set_str(EN_MARKER, json.dumps({'version': EN_VERSION, 'source_hash': digest(source),
        'based_on_sha256': SOURCE_SHA256, 'website_id': website.id, 'page_count': 31,
        'public_count': 17, 'private_count': 14, 'plan_hash': plan_hash}))
    env.flush_all()
    log('validated', pages=31, public_pages=17, private_drafts=14, arabic_preserved=True,
        page_ids_unchanged=True, publication_unchanged=True)


def rollback(env):
    if os.environ.get('MASAR_CONTENT_EN_ROLLBACK') != EN_VERSION:
        raise RuntimeError('Explicit English rollback guard required')
    params = env['ir.config_parameter']
    backup = json.loads(params.get_str(EN_MARKER + '.backup') or '{}')
    if not params.get_str(EN_MARKER) or backup.get('version') != EN_VERSION:
        raise RuntimeError('No matching applied English backup')
    for row in backup['pages']:
        page = env['website.page'].browse(row['state']['page_id'])
        if page_state(page) != row['state'] or digest(view_snapshot(page.view_id, backup['languages'])) != row['after_hash']:
            raise RuntimeError('Page edited after translation; refusing destructive rollback')
    for row in backup['pages']:
        view = env['ir.ui.view'].browse(row['state']['view_id'])
        for lang in ['en_US'] + [x for x in backup['languages'] if x != 'en_US']:
            view.with_context(lang=lang, website_id=backup['website_id']).write(row['before'][lang])
    for row in backup['menus']:
        if row['replacement']:
            menu = env['website.menu'].browse(row['id'])
            if menu.url != row['url'] or menu.parent_id.id != row['parent'] or menu.with_context(lang='en_US').name != row['replacement']:
                raise RuntimeError('Menu edited since translation')
            for lang, name in row['names'].items():
                menu.with_context(lang=lang).write({'name': name})
    params.set_str(EN_MARKER + '.rolled_back', datetime.now(timezone.utc).isoformat())
    params.search([('key', '=', EN_MARKER)]).unlink()
    log('rollback_validated', restored_pages=len(backup['pages']))


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--inspect', action='store_true')
    group.add_argument('--apply', action='store_true')
    group.add_argument('--rollback', action='store_true')
    parser.add_argument('--expect-plan')
    args = parser.parse_args()
    source = load_english()
    odoo, registry = connect()
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'lang': 'en_US'})
        cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [2026092031])
        if not cr.fetchone()[0]:
            raise RuntimeError('Another editorial change is in progress')
        if args.inspect:
            inventory(env, source)
            cr.rollback()
            log('inspection_complete', changes=0)
            return
        if args.rollback:
            rollback(env)
        else:
            apply(env, source, args.expect_plan)
        cr.commit()
        log('committed', version=EN_VERSION, operation='rollback' if args.rollback else 'English translation')


if __name__ == '__main__':
    main()

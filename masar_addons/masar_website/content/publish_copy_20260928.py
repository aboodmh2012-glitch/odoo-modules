"""Publish catalog SEO and contact copy without a module upgrade or layout reset.

Run --inspect, then --apply. Uses the existing database connection helper.
Backs up only the records changed, in an admin-only configuration parameter.
No forms, financial operations, accounts or messages are created.
"""
import argparse
import json
from lxml import etree

from import_content import connect, select_page

VERSION = 'copy_20260928'
BACKUP = 'masar_website.' + VERSION + '.backup'
MARKER = 'masar_website.' + VERSION + '.applied'
PAGE_KEYS = {
    '/': 'home', '/about': 'about', '/solutions': 'services',
    '/business': 'business', '/individuals': 'individuals',
    '/developers': 'developers', '/support': 'support',
    '/security-compliance': 'security', '/contactus': 'contact',
    '/leadership': 'leadership', '/careers': 'careers',
    '/news': 'news', '/status': 'status',
}

def contact_arch(arch):
    root = etree.fromstring(arch.encode())
    replacements = [
        ("//h1", "['pages']['contact']['hero']['title']"),
        ("//p[contains(concat(' ', normalize-space(@class), ' '), ' lead ')]", "['contact_form']['intro']"),
    ]
    for number, key in enumerate(('name', 'phone', 'email', 'company', 'subject', 'message'), 1):
        replacements.append(("//label[@for='contact%d']/span[contains(@class, 's_website_form_label_content')]" % number, "['contact_form']['%s']" % key))
    replacements.append(("//a[contains(concat(' ', normalize-space(@class), ' '), ' s_website_form_send ')]", "['contact_form']['submit']"))
    for xpath, suffix in replacements:
        nodes = root.xpath(xpath)
        if len(nodes) != 1:
            raise RuntimeError('Contact content selector must match exactly once: ' + xpath)
        # Keep tags, classes, form semantics, targets and all other attributes.
        nodes[0].set('t-out', 'website.masar_public()' + suffix)
    return etree.tostring(root, encoding='unicode')

def main():
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--inspect', action='store_true')
    mode.add_argument('--apply', action='store_true')
    args=parser.parse_args()
    odoo, registry=connect()
    with registry.cursor() as cr:
        cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [9282026])
        if not cr.fetchone()[0]: raise RuntimeError('Another editorial publication is running')
        env=odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        website=env.ref('website.default_website')
        if 'MASAR' not in website.name.upper(): raise RuntimeError('Unexpected target website')
        params=env['ir.config_parameter'].sudo()
        if args.apply and params.get_param(MARKER):
            print('[masar-copy] Already applied; no changes.', flush=True)
            return
        contact=select_page(env, website, '/contactus')
        if not contact: raise RuntimeError('Contact page missing')
        view=contact.view_id
        langs=[lang.code for lang in website.language_ids if lang.code in ('en_US','ar_001')]
        if set(langs)!={'en_US','ar_001'}: raise RuntimeError('Expected both website languages')
        arches={lang:contact_arch(view.with_context(lang=lang).arch_db) for lang in langs}
        pages={url:select_page(env,website,url) for url in PAGE_KEYS}
        if any(not p for p in pages.values()): raise RuntimeError('An expected public page is missing')
        print('[masar-copy] ' + json.dumps({'mode':'apply' if args.apply else 'inspect','website_id':website.id,'contact_view_id':view.id,'pages':len(pages),'languages':langs,'selectors':'passed'},ensure_ascii=False),flush=True)
        if not args.apply:
            cr.rollback()
            return
        backup={'contact_view_id':view.id,'arches':{lang:view.with_context(lang=lang).arch_db for lang in langs},'seo':{}}
        for url,p in pages.items():
            backup['seo'][url]={'id':p.id,'values':{lang:p.with_context(lang=lang).read(['website_meta_title','website_meta_description'])[0] for lang in langs}}
        if params.get_param(BACKUP): raise RuntimeError('Backup already exists without marker; review before applying')
        params.set_param(BACKUP,json.dumps(backup,ensure_ascii=False))
        for lang in langs:
            catalog=website.with_context(lang=lang).masar_public()
            for url,key in PAGE_KEYS.items():
                doc=catalog['home'] if key=='home' else catalog['pages'][key]
                pages[url].with_context(lang=lang).write({'website_meta_title':doc['seo_title'],'website_meta_description':doc['seo_description']})
            view.with_context(lang=lang).write({'arch_db':arches[lang]})
        view._check_xml()
        params.set_param(MARKER,'1')
        cr.commit()
        print('[masar-copy] Published SEO and contact text; layout and module state untouched.',flush=True)

if __name__=='__main__':
    main()

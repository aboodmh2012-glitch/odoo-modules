"""Apply the inspected content and native menu structure atomically.
The initial read-only inventory is retained in deployment logs.
No financial activation, original-page deletion, or theme/module upgrade occurs.
"""
import json
import os
from content_engine import VERSION, MARKER_KEY, SOURCE_SHA256, load_source
from import_content import connect, inspect, apply, select_page, log


def finish_navigation(env, website):
    params = env['ir.config_parameter']
    if params.get_param(MARKER_KEY + '.navigation'):
        return
    backup = json.loads(params.get_param(MARKER_KEY + '.backup'))
    Menu = env['website.menu']
    root = website.menu_id
    languages = website.language_ids.mapped('code')

    def save(menu):
        if menu.id in backup['new_menu_ids'] or any(x['id'] == menu.id for x in backup['old_menus']):
            return
        row = menu.with_context(lang='en_US').read(['name', 'url', 'page_id', 'parent_id', 'sequence', 'website_id'])[0]
        row['names'] = {lang: menu.with_context(lang=lang).name for lang in languages}
        backup['old_menus'].append(row)

    def parent(url):
        rows = Menu.search([('website_id', '=', website.id), ('parent_id', '=', root.id), ('url', '=', url)])
        if len(rows) != 1:
            raise RuntimeError('Expected one top-level destination: ' + url)
        return rows

    def child(parent_menu, ar_name, en_name, url, sequence, reuse=None):
        page = select_page(env, website, url)
        if not page or not page.website_published:
            raise RuntimeError('Navigation destination is not published: ' + url)
        menu = reuse if reuse is not None else Menu.search([
            ('website_id', '=', website.id), ('parent_id', '=', parent_menu.id), ('url', '=', url)])
        if len(menu) > 1:
            raise RuntimeError('Duplicate child destination: ' + url)
        vals = {'name': en_name, 'url': url, 'page_id': page.id, 'parent_id': parent_menu.id,
                'website_id': website.id, 'sequence': sequence}
        if menu:
            save(menu)
            menu.with_context(lang='en_US').write(vals)
        else:
            menu = Menu.with_context(lang='en_US').create(vals)
            backup['new_menu_ids'].append(menu.id)
        for lang in languages:
            if lang.startswith('ar'):
                menu.with_context(lang=lang).write({'name': ar_name})

    solutions = parent('/solutions')
    legacy = Menu.search([('website_id', '=', website.id), ('parent_id', '=', root.id), ('url', '=', '/services')])
    if len(legacy) > 1:
        raise RuntimeError('Unexpected duplicate legacy Services menu')
    child(solutions, 'جميع الحلول', 'All solutions', '/solutions', 1, reuse=legacy if legacy else None)
    for seq, item in enumerate([
        ('الحسابات والبطاقات', 'Accounts & Cards', '/solutions/accounts-cards'),
        ('نقاط البيع', 'Point of Sale', '/solutions/pos'),
        ('بوابة الدفع', 'Payment Gateway', '/solutions/payment-gateway'),
        ('المدفوعات الجماعية', 'Bulk Payments', '/solutions/payouts'),
        ('سداد الفواتير والتحصيل', 'Bills & Collections', '/solutions/bill-payments'),
        ('الصرافات والخدمات النقدية', 'ATM & Cash Access', '/solutions/atm-cash'),
        ('مسار للأفراد', 'Personal', '/personal'),
    ], 2):
        child(solutions, *item, seq)
    help_menu = parent('/help')
    for seq, item in enumerate([
        ('مركز المساعدة', 'Help Center', '/help'),
        ('الأسئلة الشائعة', 'Frequently Asked Questions', '/help/faq'),
        ('التوعية الأمنية', 'Stay Safe', '/help/stay-safe'),
        ('الرسوم والحدود', 'Fees & Limits', '/pricing'),
    ], 1):
        child(help_menu, *item, seq)
    about = Menu.search([('website_id', '=', website.id), ('parent_id', '=', root.id), ('url', '=', '/about')])
    if len(about) == 1:
        child(about, 'عن مسار', 'About MASAR', '/about', 1)
        child(about, 'الشراكات', 'Partnerships', '/partners', 2)
    params.set_param(MARKER_KEY + '.backup', json.dumps(backup, ensure_ascii=False))
    params.set_param(MARKER_KEY + '.navigation', VERSION)
    log('navigation_prepared', top_level=[{'id': m.id, 'name': m.name, 'url': m.url}
        for m in Menu.search([('website_id', '=', website.id), ('parent_id', '=', root.id)], order='sequence,id')])


def main():
    if os.environ.get('MASAR_CONTENT_APPLY') != VERSION:
        raise RuntimeError('Explicit content-apply guard is not enabled')
    source = load_source()
    odoo, registry = connect()
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'lang': 'en_US'})
        cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [2026092031])
        if not cr.fetchone()[0]:
            raise RuntimeError('Another content import is in progress')
        prior = env['ir.config_parameter'].get_param(MARKER_KEY)
        if prior:
            if json.loads(prior).get('source_sha256') != SOURCE_SHA256:
                raise RuntimeError('Unexpected prior source')
            website = env.ref('base.default_website')
        else:
            website, arabic, plan = inspect(env, source)
            apply(env, source, website, arabic, plan)
        finish_navigation(env, website)
        cr.commit()
        log('committed', version=VERSION, public_pages=17, private_drafts=14)


if __name__ == '__main__':
    main()

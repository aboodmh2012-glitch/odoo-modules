"""Refresh only homepage asset URLs; never upgrade website views."""
import json
from lxml import etree
from import_content import connect

def update_arch(arch):
    root = etree.fromstring(arch.encode())
    links = root.xpath("//link[contains(@href, '/masar_website/static/src/css/masar_brand_fix.css')]")
    preloads = root.xpath("//link[@rel='preload'][@as='image'][contains(@t-att-href, 'hero-fintech-yemen-v2')]")
    if len(links) != 1 or len(preloads) != 1:
        raise RuntimeError('Unexpected homepage asset selectors; no changes applied')
    links[0].set('href', '/masar_website/static/src/css/masar_brand_fix.css?v=hero-mobile-fit-20260928')
    source = preloads[0].get('t-att-href')
    for name in ('hero-fintech-yemen-v2.webp', 'hero-fintech-yemen-v2-rtl.webp'):
        source = source.replace(name + "'", name + "?v=card-payment-20260928'")
    preloads[0].set('t-att-href', source)
    return etree.tostring(root, encoding='unicode')

def main():
    odoo, registry = connect()
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        view = env.ref('masar_website.masar_brand_fix_head')
        website = env.ref('base.default_website')
        if 'MASAR' not in website.name.upper():
            raise RuntimeError('Unexpected website')
        params = env['ir.config_parameter'].sudo()
        key = 'masar_website.hero_mobile_fit_20260928'
        if params.get_param(key + '.applied'):
            print('[masar-hero] Already applied', flush=True)
            return
        langs = [x.code for x in website.language_ids]
        originals = {lang: view.with_context(lang=lang).arch_db for lang in langs}
        updated = {lang: update_arch(arch) for lang, arch in originals.items()}
        params.set_param(key + '.backup', json.dumps({'view_id': view.id, 'arches': originals}))
        for lang, arch in updated.items():
            view.with_context(lang=lang).write({'arch_db': arch})
        view._check_xml()
        params.set_param(key + '.applied', '1')
        cr.commit()
        print('[masar-hero] Homepage image and stylesheet cache versions published', flush=True)

if __name__ == '__main__':
    main()

"""Publish only shared footer refinement styles without a module upgrade."""
import json
from lxml import etree
from import_content import connect
CSS = '/masar_website/static/src/css/masar_footer_polish.css?v=20260928-1'

def update_arch(arch):
    root = etree.fromstring(arch.encode())
    targets = root.xpath("//xpath[@expr='//head'][@position='inside']")
    if len(targets) != 1:
        raise RuntimeError('Expected one MASAR head insertion; no changes applied')
    target = targets[0]
    for tag, attr, path in (('link', 'href', CSS),):
        found = target.xpath("./%s[contains(@%s, 'masar_footer_polish.')]" % (tag, attr))
        if len(found) > 1:
            raise RuntimeError('Duplicate footer polish assets')
        element = found[0] if found else etree.SubElement(target, tag)
        element.set(attr, path)
        if tag == 'link':
            element.set('rel', 'stylesheet')
        else:
            element.set('defer', 'defer')
            element.text = ''
    return etree.tostring(root, encoding='unicode')

def main():
    odoo, registry = connect()
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        website = env.ref('base.default_website')
        if 'MASAR' not in website.name.upper():
            raise RuntimeError('Unexpected website')
        view = env.ref('masar_website.masar_brand_fix_head')
        params = env['ir.config_parameter'].sudo()
        key = 'masar_website.footer_polish_20260928'
        if params.get_param(key + '.applied'):
            print('[masar-footer] Already applied', flush=True)
            return
        originals = {lang.code:view.with_context(lang=lang.code).arch_db for lang in website.language_ids}
        updated = {lang:update_arch(arch) for lang,arch in originals.items()}
        params.set_param(key + '.backup', json.dumps({'view_id':view.id,'arches':originals}))
        for lang, arch in updated.items():
            view.with_context(lang=lang).write({'arch_db':arch})
        view._check_xml()
        params.set_param(key + '.applied', '1')
        cr.commit()
        print('[masar-footer] Footer styles published; forms, content, and other views preserved', flush=True)

if __name__ == '__main__':
    main()

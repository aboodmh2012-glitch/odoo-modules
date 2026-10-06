"""Emergency rollback of this import only. Does not delete content or original views.
Requires MASAR_CONTENT_ROLLBACK=2026-09-20-ar-content-v1.
Run only after reviewing the saved backup and any subsequent editorial changes.
"""
import json
import os
from datetime import datetime, timezone
from content_engine import VERSION, MARKER_KEY
from import_content import connect, log


def main():
    if os.environ.get('MASAR_CONTENT_ROLLBACK') != VERSION:
        raise RuntimeError('Explicit rollback guard is not enabled')
    odoo, registry = connect()
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'lang': 'en_US'})
        cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [2026092031])
        if not cr.fetchone()[0]:
            raise RuntimeError('Another content operation is in progress')
        params = env['ir.config_parameter']
        saved = params.get_str(MARKER_KEY + '.backup')
        report = params.get_str(MARKER_KEY)
        if not saved or not report:
            raise RuntimeError('No committed import with a backup was found')
        backup = json.loads(saved)
        if backup['version'] != VERSION:
            raise RuntimeError('Unexpected backup version')
        for old in backup['old_pages']:
            page = env['website.page'].browse(old['id']).exists()
            view = env['ir.ui.view'].browse(old['view_id']).exists()
            if not page or not view:
                raise RuntimeError('Original record is missing; refusing partial rollback')
            page.write({k: old[k] for k in ('url', 'view_id', 'website_published', 'website_indexed')})
        for old in backup['old_menus']:
            menu = env['website.menu'].browse(old['id']).exists()
            if not menu:
                raise RuntimeError('Original menu is missing')
            vals = {k: old[k] for k in ('name', 'url', 'sequence')}
            for field in ('page_id', 'parent_id', 'website_id'):
                vals[field] = old[field][0] if old[field] else False
            menu.with_context(lang='en_US').write(vals)
            for lang, name in old['names'].items():
                menu.with_context(lang=lang).write({'name': name})
        env['website.menu'].browse(backup['new_menu_ids']).exists().unlink()
        env['website.page'].browse(backup['new_page_ids']).exists().write({'website_published': False, 'website_indexed': False})
        env['ir.ui.view'].browse(backup['new_view_ids']).exists().write({'active': False})
        params.set_str(MARKER_KEY + '.rollback', json.dumps({'at': datetime.now(timezone.utc).isoformat(), 'report': json.loads(report)}))
        params.set_str(MARKER_KEY, False)
        cr.commit()
        log('rolled_back', version=VERSION, source_and_imported_content_retained=True)


if __name__ == '__main__':
    main()

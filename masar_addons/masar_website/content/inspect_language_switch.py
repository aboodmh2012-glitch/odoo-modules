"""Inspect public locale links and redirect behavior without changing Odoo.
Only frontend_lang (a locale preference) is logged; never session cookies.
"""
import json
from urllib.parse import urljoin, urlencode
import requests
from lxml import html

BASE = 'https://odoo-production-438a.up.railway.app'


def log(event, **data):
    print('[masar-lang-check] ' + json.dumps({'event': event, **data}, ensure_ascii=False), flush=True)


def get(client, path, label):
    url = urljoin(BASE, path)
    for hop in range(5):
        if not url.startswith(BASE + '/'):
            raise RuntimeError('Unexpected redirect host')
        r = client.get(url, allow_redirects=False, timeout=25)
        log('hop', label=label, path=url[len(BASE):], status=r.status_code,
            location=r.headers.get('Location'),
            language_cookies=[{'value': c.value, 'domain': c.domain, 'path': c.path, 'secure': c.secure}
                              for c in client.cookies if c.name == 'frontend_lang'])
        if r.is_redirect:
            url = urljoin(url, r.headers['Location'])
            continue
        tree = html.fromstring(r.content)
        log('page', label=label, html_lang=tree.get('lang'),
            h1=[' '.join(x.itertext()).strip() for x in tree.xpath('//h1')],
            selector=[{'href': x.get('href'), 'code': x.get('data-url_code'), 'class': x.get('class')}
                      for x in tree.xpath('//a[@data-url_code]')])
        return tree
    raise RuntimeError('Too many redirects')


def main():
    for path in ('/en', '/en/solutions'):
        s = requests.Session()
        s.trust_env = False
        s.headers.update({'User-Agent': 'MASAR-locale-diagnostic/1.0', 'Accept-Language': 'en-US,en;q=0.9'})
        tree = get(s, path, 'initial')
        links = tree.xpath('//a[@data-url_code="ar"]/@href')
        if links:
            get(s, '/website/lang/ar?' + urlencode({'r': links[0]}), 'native-Arabic')
        get(s, '/ar' + (path[3:] if path != '/en' else ''), 'explicit-Arabic')
    from pathlib import Path
    files = [
        ('controller', '/usr/lib/python3/dist-packages/odoo/addons/website/controllers/main.py', 'def change_lang'),
        ('client', '/usr/lib/python3/dist-packages/odoo/addons/website/static/src/js/content/website_root.js', '_onLangChangeClick: function'),
    ]
    for label, path, term in files:
        text = Path(path).read_text()
        index = text.find(term)
        log('installed_native_code', part=label, code=text[index:index+1200] if index >= 0 else 'not found')


if __name__ == '__main__':
    main()

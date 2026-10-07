"""One-shot anonymous HTTP GET checks. No form submissions or payment actions."""
import json
import os
import re
import time
from urllib.parse import urlparse, urljoin
import requests
from lxml import html
from content_engine import PUBLIC_SLUGS, target_url, VERSION as AR_VERSION
from english_content import EN_VERSION, ARABIC, load_english
from probe_content import verify as verify_arabic

DOMAIN = 'odoo-production-438a.up.railway.app'
PUBLIC = 'https://' + DOMAIN
LOCAL = 'http://127.0.0.1:' + os.environ.get('PORT', '8080')


def emit(event, **data):
    print('[masar-en-http] ' + json.dumps({'event': event, **data}, ensure_ascii=False), flush=True)


def session(locale='en_US', initial_cookie=True):
    s = requests.Session()
    s.trust_env = False
    s.headers.update({'User-Agent': 'MASAR-English-verifier/1.2', 'Accept-Language': locale, 'Host': DOMAIN})
    if initial_cookie:
        s.cookies.set('frontend_lang', locale)
    return s


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


def path_for(slug, prefix='/en'):
    return prefix if slug == '/' else prefix + slug


def native_switch(client, base, tree, code):
    """Follow WebsiteRoot._onLangChangeClick in the existing browsing session.

    Odoo 19 intercepts .js_change_lang, removes edit_translations and GETs
    /website/lang/<url_code>?r=<href>. This sets the locale cookie and handles
    an empty homepage href. Directly resolving an empty href to /en is wrong.
    Source: addons/website/static/src/js/content/website_root.js (19.0).
    """
    anchors = tree.xpath('//a[@data-url_code=$code]', code=code)
    if not anchors:
        raise ValueError('Language selector missing: ' + code)
    href = anchors[0].get('href', '')
    cleaned = re.sub(r'[&?]edit_translations[^&?]+', '', href)
    target = urlparse(urljoin(PUBLIC + '/', cleaned))
    if target.hostname != DOMAIN or target.scheme != 'https':
        raise ValueError('Unexpected language destination host')
    response = client.get(base + '/website/lang/' + code, params={'r': cleaned}, timeout=25)
    return response, href


def wait_ready(base, timeout):
    end = time.monotonic() + timeout
    s = session()
    while time.monotonic() < end:
        try:
            r = s.get(base + '/en', timeout=12)
            if r.status_code == 200 and EN_VERSION in r.text:
                return True
        except requests.RequestException:
            pass
        time.sleep(4)
    return False


def verify(base, origin):
    source = load_english()
    failures, public_ok, hidden, switches, roundtrips = [], 0, 0, 0, 0
    links = set()
    # Let the initial page set its real domain-scoped cookies, just as a browser
    # does. Do not invent a second session for a click on that same page.
    s = session(initial_cookie=False)
    for page in source['pages']:
        public = page['slug'] in PUBLIC_SLUGS
        path = path_for(target_url(page))
        errors = []
        start = time.monotonic()
        try:
            r = s.get(base + path, timeout=25)
            tree = html.fromstring(r.content)
            wraps = tree.xpath('//*[@data-masar-content-version=$v]', v=EN_VERSION)
            if not public:
                ok = not wraps and (r.status_code in (403, 404) or '/web/login' in r.url)
                hidden += int(ok)
            else:
                if r.status_code != 200 or len(wraps) != 1:
                    errors.append('status_or_content_version')
                else:
                    wrap = wraps[0]
                    expected = page['body'].splitlines()[0][2:].strip()
                    h1 = [norm(' '.join(n.itertext())) for n in wrap.xpath('.//h1')]
                    if h1 != [expected]:
                        errors.append('heading')
                    visible = norm(' '.join(wrap.itertext()))
                    if ARABIC.search(visible) or wrap.get('dir') != 'ltr' or wrap.get('lang') != 'en':
                        errors.append('untranslated_or_direction')
                    if not (tree.get('lang') or '').lower().startswith('en'):
                        errors.append('html_language')
                    for line in page['body'].splitlines():
                        line = re.sub(r'^#{1,2} ', '', line).replace('**', '').strip()
                        if line and norm(line) not in visible:
                            errors.append('missing_body_text')
                            break
                    if page['seo_title'] not in tree.xpath('//title/text()'):
                        errors.append('seo_title')
                    if page['meta_description'] not in tree.xpath('//meta[@name="description"]/@content'):
                        errors.append('meta_description')
                    if wrap.xpath('.//aside[contains(@class,"masar-editorial-review")]') or page['editorial_notes'] in visible:
                        errors.append('private_notes_exposed')
                    for href in wrap.xpath('.//a/@href'):
                        if not href.startswith('/en'):
                            errors.append('non_english_link')
                        else:
                            links.add(href)
                    # The same anonymous session follows the rendered link and
                    # retains Odoo's locale cookie across both native redirects.
                    ar, ar_href = native_switch(s, base, tree, 'ar')
                    ar_tree = html.fromstring(ar.content)
                    ar_wrap = ar_tree.xpath('//*[@data-masar-content-version=$v]', v=AR_VERSION)
                    result_path = urlparse(ar.url).path.rstrip('/') or '/'
                    valid_paths = {page['slug'], path_for(page['slug'], '/ar')}
                    ar_ok = ar.status_code == 200 and len(ar_wrap) == 1 and result_path in valid_paths
                    back_ok = False
                    if ar_ok:
                        switches += 1
                        back, en_href = native_switch(s, base, ar_tree, 'en')
                        back_tree = html.fromstring(back.content)
                        back_wrap = back_tree.xpath('//*[@data-masar-content-version=$v]', v=EN_VERSION)
                        back_path = urlparse(back.url).path.rstrip('/')
                        back_ok = back.status_code == 200 and len(back_wrap) == 1 and back_path == path
                        if back_ok:
                            roundtrips += 1
                        else:
                            errors.append('language_switch_back')
                    else:
                        errors.append('language_switch_to_arabic')
                    emit('language_switch', origin=origin, page=path, arabic_href=ar_href,
                         arabic_result=result_path, arabic_ok=ar_ok, roundtrip_ok=back_ok,
                         method='native_Odoo_language_route')
                ok = not errors
                public_ok += int(ok)
            emit('page', origin=origin, url=path, status=r.status_code, ok=ok,
                 errors=errors, seconds=round(time.monotonic()-start, 3))
            if not ok:
                failures.append(path)
        except Exception as exc:
            failures.append(path)
            emit('page_error', origin=origin, url=path, error=type(exc).__name__)
    links.add('/en/contactus')
    for path in sorted(links):
        try:
            r = s.get(base + path, timeout=20)
            if r.status_code != 200:
                failures.append('link:' + path)
            emit('link', origin=origin, url=path, status=r.status_code, ok=r.status_code == 200)
        except requests.RequestException:
            failures.append('link:' + path)
    emit('summary', origin=origin, english_public_ok=public_ok, private_drafts_hidden=hidden,
         language_switches_ok=switches, language_roundtrips_ok=roundtrips,
         links_checked=len(links), failures=failures, version=EN_VERSION)
    return not failures


def main():
    if not wait_ready(LOCAL, 240):
        emit('not_ready', origin='local')
        return
    local_en = verify(LOCAL, 'local')
    local_ar = verify_arabic(LOCAL, 'local-after-English')
    if not wait_ready(PUBLIC, 180):
        emit('not_ready', origin='public')
        return
    public_en = verify(PUBLIC, 'public')
    public_ar = verify_arabic(PUBLIC, 'public-after-English')
    emit('complete', ok=all([local_en, local_ar, public_en, public_ar]), version=EN_VERSION)


if __name__ == '__main__':
    main()

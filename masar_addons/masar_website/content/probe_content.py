"""One-shot read-only HTTP verification. Never submit forms or mutate Odoo."""
import json
import os
import time
import requests
from lxml import html
from content_engine import VERSION, PUBLIC_SLUGS, REVIEW_PREFIX, load_source

DOMAIN = "odoo-production-438a.up.railway.app"
BASE = "https://" + DOMAIN
LOCAL = "http://127.0.0.1:" + os.environ.get("PORT", "8080")


def emit(event, **data):
    print("[masar-content-http] " + json.dumps({"event": event, **data}, ensure_ascii=False), flush=True)


def session():
    s = requests.Session()
    s.trust_env = False
    s.headers.update({"User-Agent": "MASAR-content-verifier/1.0", "Accept-Language": "ar"})
    s.cookies.set("frontend_lang", "ar_001")
    return s


def wait_ready(base, timeout):
    end = time.monotonic() + timeout
    s = session()
    while time.monotonic() < end:
        try:
            r = s.get(base + "/ar", headers={"Host": DOMAIN}, timeout=12)
            if r.status_code == 200 and VERSION in r.text:
                return True
        except requests.RequestException:
            pass
        time.sleep(4)
    return False


def verify(base, origin):
    records = load_source()["pages"]
    s = session()
    failed, public, hidden = [], 0, 0
    for p in records:
        is_public = p["slug"] in PUBLIC_SLUGS
        path = p["slug"] if is_public else REVIEW_PREFIX + p["slug"]
        path = "/ar" + (path if path != "/" else "")
        start = time.monotonic()
        try:
            r = s.get(base + path, headers={"Host": DOMAIN}, timeout=25)
            tree = html.fromstring(r.content)
            containers = tree.xpath('//*[@data-masar-content-version="' + VERSION + '"]')
            h1 = [" ".join(x.itertext()).strip() for x in tree.xpath("//h1")]
            expected = p["body"].splitlines()[0][2:].strip()
            if is_public:
                ok = r.status_code == 200 and len(containers) == 1 and h1 == [expected]
                if p["editorial_notes"] in r.text or "[الجهة القانونية" in r.text:
                    ok = False
                public += bool(ok)
            else:
                ok = not containers and (r.status_code in (403, 404) or "/web/login" in r.url)
                hidden += bool(ok)
            emit("page", origin=origin, url=path, status=r.status_code, ok=bool(ok),
                 seconds=round(time.monotonic()-start, 3), h1=h1 if is_public else [])
            if not ok:
                failed.append(path)
        except Exception as exc:
            failed.append(path)
            emit("page_error", origin=origin, url=path, error=type(exc).__name__)
    for path in ("/en", "/en/solutions", "/en/business", "/en/developers", "/contactus"):
        try:
            r = s.get(base + path, headers={"Host": DOMAIN}, timeout=25)
            ok = r.status_code == 200
            emit("existing_route", origin=origin, url=path, status=r.status_code, ok=ok)
            if not ok:
                failed.append(path)
        except requests.RequestException:
            failed.append(path)
    emit("summary", origin=origin, public_ok=public, private_drafts_hidden=hidden, failures=failed,
         checked=len(records)+5, version=VERSION)
    return not failed


def main():
    if not wait_ready(LOCAL, 240):
        emit("not_ready", origin="local", version=VERSION)
        return
    verify(LOCAL, "local")
    if wait_ready(BASE, 180):
        verify(BASE, "public")
    else:
        emit("not_ready", origin="public", version=VERSION)


if __name__ == "__main__":
    main()

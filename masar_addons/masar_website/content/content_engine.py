"""Render the approved Arabic editorial source into native Odoo QWeb pages.

This is a data import, not a new app, controller, payment API, or security policy.
The source archive is immutable and verified against the approved file hash.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import html
import json
import re
from pathlib import Path

VERSION = "2026-09-20-ar-content-v1"
SOURCE_SHA256 = "0352d26143649808f2412c0d75e87e37b2c90ca10f5f48c710286c6d995cc92c"
PUBLIC_SLUGS = {
    "/", "/solutions", "/solutions/accounts-cards", "/solutions/pos",
    "/solutions/payment-gateway", "/solutions/payouts", "/solutions/bill-payments",
    "/solutions/atm-cash", "/personal", "/business", "/institutions",
    "/developers", "/partners", "/pricing", "/help", "/help/faq", "/help/stay-safe",
}
# Explicit missing-data, operational and legal gates stay private.
# Preserve already-published originals; create private review pages instead.
REVIEW_PREFIX = "/website-content-review"
STYLE_KEY = "masar_website.editorial_ar_styles"
MARKER_KEY = "masar_website.editorial_ar_20260920"
AUDIENCES = ["/personal", "/business", "/institutions", "/developers"]
SERVICES = ["/solutions/accounts-cards", "/solutions/pos", "/solutions/payment-gateway",
            "/solutions/payouts", "/solutions/bill-payments", "/solutions/atm-cash"]
NAVIGATION = [
    ("الحلول", "Solutions", "/solutions"),
    ("للأعمال", "Business", "/business"),
    ("للمؤسسات", "Institutions", "/institutions"),
    ("المطورون", "Developers", "/developers"),
    ("عن مسار", "About MASAR", "/about"),
    ("المساعدة", "Help", "/help"),
]
STYLE = """
.masar-editorial { /* typeface inherits from the website theme */ }
.masar-editorial .masar-hero__title {max-width:22ch;line-height:1.3;letter-spacing:0;}
.masar-editorial .masar-hero__brand {line-height:1.6;}
.masar-editorial--detail .masar-hero {min-height:0;}
.masar-editorial--detail .masar-hero__inner {padding:5.5rem 0 3.5rem;}
.masar-editorial--detail .masar-hero__title {font-size:2.5rem;}
.masar-editorial .masar-editorial-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.25rem;margin:0;}
.masar-editorial .masar-editorial-card {min-width:0;min-height:0;}
.masar-editorial .masar-editorial-card p {margin:0 0 .65rem;line-height:1.95;}
.masar-editorial .masar-editorial-card p:last-child {margin-bottom:0;}
.masar-editorial .masar-service__name {line-height:1.6;}
.masar-editorial .masar-editorial-related {margin-block-start:2rem;display:flex;flex-wrap:wrap;gap:.7rem;}
.masar-editorial .masar-reveal {opacity:1;transform:none;}
.masar-editorial a:focus-visible {outline:3px solid currentColor;outline-offset:4px;}
.masar-editorial .masar-editorial-notice {padding:.8rem 1rem;background:var(--masar-sand,#F4F7FB);border-inline-start:3px solid var(--masar-orange,#FF7A00);margin-bottom:1.5rem;}
.masar-editorial .masar-editorial-review {border:2px solid #0E1B2B;padding:1rem;margin:1rem;border-radius:.6rem;}
.masar-editorial details {padding:1.2rem;border:1px solid var(--masar-line,rgba(22,18,14,.12));border-radius:.75rem;margin-bottom:.8rem;}
.masar-editorial summary {font-weight:700;line-height:1.7;cursor:pointer;}
.masar-editorial details p {margin-top:.85rem;line-height:1.95;}
@media(max-width:767px) {
 .masar-editorial .masar-editorial-grid {grid-template-columns:minmax(0,1fr);}
 .masar-editorial--detail .masar-hero__inner {padding:3.5rem 0 2.5rem;}
 .masar-editorial--detail .masar-hero__title {font-size:2rem;}
 .masar-editorial .masar-hero__title {line-height:1.4;}
}
"""


def load_source(path=None):
    folder = Path(path or Path(__file__).parent)
    encoded = "".join((folder / f"source_ar.{i}.b64").read_text().strip() for i in range(4))
    raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Editorial source hash mismatch; refusing to import")
    source = json.loads(raw)
    pages = source["pages"]
    if len(pages) != 31 or len({p["slug"] for p in pages}) != 31:
        raise ValueError("Expected exactly 31 unique editorial records")
    for page in pages:
        if not re.fullmatch(r"/[a-z0-9/-]*", page["slug"]):
            raise ValueError("Unexpected page path")
        if not page["body"].startswith("# "):
            raise ValueError("Every page must have a source H1")
    return source


def target_url(page):
    return page["slug"] if page["slug"] in PUBLIC_SLUGS else REVIEW_PREFIX + page["slug"]


def view_key(slug):
    return "masar_website.editorial_ar_" + (slug.strip("/").replace("/", "_").replace("-", "_") or "home")


def inline(text):
    escaped = html.escape(text, quote=True)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)


def paragraphs(lines):
    chunks, buf = [], []
    for line in lines + [""]:
        if line.strip():
            buf.append(inline(line))
        elif buf:
            chunks.append("<p>" + "<br/>".join(buf) + "</p>")
            buf = []
    return "".join(chunks)


def split_body(body):
    lines = body.splitlines()
    title = lines.pop(0)[2:].strip()
    lead, sections, current = [], [], None
    for line in lines:
        if line.startswith("## "):
            current = [line[3:].strip(), []]
            sections.append(current)
        elif current is None:
            lead.append(line)
        else:
            current[1].append(line)
    return title, paragraphs(lead), sections


def related_slugs(slug):
    if slug in ("/", "/solutions"):
        return SERVICES + AUDIENCES
    if slug in ("/personal", "/business", "/institutions"):
        return SERVICES
    if slug in ("/help", "/help/faq", "/help/stay-safe"):
        return ["/help/faq", "/help/stay-safe", "/pricing", "/solutions"]
    if slug == "/developers":
        return ["/solutions/payment-gateway", "/solutions/payouts", "/business"]
    return ["/solutions", "/pricing", "/help/faq"]


def build_arch(page, source, *, existing_english_key=None, contact_available=False,
               hero_style=None, menu_note=False):
    slug = page["slug"]
    is_public = slug in PUBLIC_SLUGS
    title, lead, sections = split_body(page["body"])
    key = view_key(slug)
    records = {p["slug"]: p for p in source["pages"]}
    blocks = []
    for index, (heading, lines) in enumerate(sections):
        text = paragraphs(lines)
        if slug == "/help/faq":
            blocks.append(f'<details><summary>{inline(heading)}</summary>{text}</details>')
        else:
            anchor = f'content-{index + 1}'
            blocks.append(f'<article id="{anchor}" class="masar-service masar-editorial-card">'
                          f'<h2 class="masar-service__name">{inline(heading)}</h2>{text}</article>')
    related = "".join(
        f'<a class="masar-btn masar-btn--outline" href="{html.escape(s)}">{inline(records[s]["name"])}</a>'
        for s in dict.fromkeys(related_slugs(slug)) if s != slug and s in PUBLIC_SLUGS
    )
    actions = []
    for cta in page["cta"].split(" | "):
        if " → " not in cta:
            continue
        label, link = cta.split(" → ", 1)
        if link in PUBLIC_SLUGS or (link == "/contactus" and contact_available):
            actions.append(f'<a class="masar-btn masar-btn--primary" href="{html.escape(link, quote=True)}">{inline(label)}</a>')
    body_class = "masar-editorial--home" if slug == "/" else "masar-editorial--detail"
    style_attr = f' style="{html.escape(hero_style, quote=True)}"' if hero_style else ""
    review = ""
    if not is_public:
        review = ('<aside class="masar-editorial-review" role="note"><strong>مسودة داخلية — تحتاج اعتمادًا قبل النشر</strong>'
                  f'<p>{inline(page["publishing_gate"])}</p><p>{inline(page["editorial_notes"])}</p>'
                  f'<p>الرابط المقصود بعد الاعتماد: <bdi dir="ltr">{html.escape(slug)}</bdi></p></aside>')
    notice = ''
    if not existing_english_key and is_public:
        notice = '<p t-if="not (request.env.lang or \'\').startswith(\'ar\')" lang="en" dir="ltr" class="masar-editorial-notice">This page is currently available in Arabic.</p>'
    anchors = ''
    if slug == "/":
        anchors = ''.join(f'<span id="{anchor}"/>' for anchor in ["about", "services", "solutions", "technology", "security", "knowledge", "developers", "help", "vision", "values", "start"])
    grid_class = "" if slug == "/help/faq" else ' class="masar-editorial-grid"'
    ar_body = (
        '<t t-call="website.layout">'
        f'<t t-call="{STYLE_KEY}"/>'
        f'<div id="wrap" lang="ar" dir="rtl" class="oe_structure masar-site masar-editorial {body_class}" data-masar-content-version="{VERSION}">'
        f'{review}<section id="masar-content-top" class="masar-hero"{style_attr}>'
        '<div class="masar-hero__inner"><p class="masar-hero__brand">مسار — المدفوعات والبنية المالية</p>'
        f'<h1 class="masar-hero__title">{inline(title)}</h1><div class="masar-hero__lead">{lead}</div>'
        f'<div class="masar-hero__actions">{"".join(actions)}</div></div></section>'
        f'<section class="masar-section"><div class="masar-wrap">{notice}{anchors}<div{grid_class}>{"".join(blocks)}</div>'
        f'<nav class="masar-editorial-related" aria-label="صفحات ذات صلة">{related}</nav>'
        '</div></section></div></t>'
    )
    if existing_english_key:
        content = (f'<t t-if="(request.env.lang or \'\').startswith(\'ar\')">{ar_body}</t>'
                   f'<t t-else="" t-call="{html.escape(existing_english_key, quote=True)}"/>')
    else:
        content = ar_body
    return f'<t t-name="{key}">{content}</t>'


def style_arch():
    return f'<t t-name="{STYLE_KEY}"><style>{html.escape(STYLE)}</style></t>'

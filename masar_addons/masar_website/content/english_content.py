"""English localization of the approved 31-page Arabic content package.

Reuse the existing renderer and shared styling. Do not change URL identity,
publication gates or the live Arabic layout. No new models or public APIs.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from lxml import etree

from content_engine import (
    VERSION as AR_VERSION, SOURCE_SHA256, PUBLIC_SLUGS, REVIEW_PREFIX,
    build_arch, load_source, target_url, view_key,
)

EN_VERSION = "2026-09-20-en-content-v1"
EN_MARKER = "masar_website.editorial_en_20260920"
ARABIC = re.compile(r"[\u0600-\u06ff]")
REQUIRED_FIELDS = {"slug", "name", "seo_title", "meta_description", "body", "cta", "publishing_gate", "editorial_notes"}


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_english(folder=None):
    folder = Path(folder or Path(__file__).parent)
    pages = []
    for part in (1, 2):
        pages.extend(json.loads((folder / f"source_en_{part}.json").read_text(encoding="utf-8")))
    original = load_source(folder)
    ar_pages = {p["slug"]: p for p in original["pages"]}
    if len(pages) != 31 or {p["slug"] for p in pages} != set(ar_pages):
        raise ValueError("English scope must match all 31 original pages")
    for page in pages:
        if set(page) != REQUIRED_FIELDS or not all(isinstance(v, str) and v.strip() for v in page.values()):
            raise ValueError("Invalid or incomplete English record")
        if any(ARABIC.search(v) for v in page.values()):
            raise ValueError("Untranslated Arabic in English source: " + page["slug"])
        ar = ar_pages[page["slug"]]
        for prefix in ("# ", "## "):
            if sum(x.startswith(prefix) for x in page['body'].splitlines()) != sum(x.startswith(prefix) for x in ar['body'].splitlines()):
                raise ValueError("Heading structure differs from Arabic: " + page['slug'])
        if len(page['body'].split('\n\n')) != len(ar['body'].split('\n\n')):
            raise ValueError("Content section missing: " + page['slug'])
        def paths(cta):
            return re.findall(r"\u2192 (/[^\s|]*)", cta)
        if paths(page['cta']) != paths(ar['cta']):
            raise ValueError("CTA destinations differ: " + page['slug'])
    return {"version": EN_VERSION, "locale": "en_US", "based_on_sha256": SOURCE_SHA256, "pages": pages}


def parse(arch):
    return etree.fromstring(arch.encode(), etree.XMLParser(resolve_entities=False, no_network=True))


def arabic_layout(arch):
    root = parse(arch)
    wraps = root.xpath('.//div[@id="wrap"][@data-masar-content-version=$v]', v=AR_VERSION)
    if len(wraps) != 1:
        raise ValueError("Expected one preserved Arabic editorial body")
    layout = wraps[0].getparent()
    if layout.tag != 't' or layout.get('t-call') != 'website.layout':
        raise ValueError("Unexpected Arabic layout structure; inspect before changing")
    return layout


def layout_bytes(layout):
    node = copy.deepcopy(layout)
    node.tail = None
    return etree.tostring(node, method='c14n')


def english_layout(page, source, contact_available=True, hero_style=None):
    # The original renderer remains the single owner of layout and styling.
    root = parse(build_arch(page, source, contact_available=contact_available, hero_style=hero_style))
    layout = root.find('t')
    wrap = layout.find("div[@id='wrap']")
    wrap.set('lang', 'en')
    wrap.set('dir', 'ltr')
    wrap.set('data-masar-content-version', EN_VERSION)
    wrap.set('data-masar-content-locale', 'en')
    for notice in wrap.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " masar-editorial-notice ")]'):
        notice.getparent().remove(notice)
    brand = wrap.xpath('.//p[@class="masar-hero__brand"]')[0]
    brand.text = 'MASAR — Payments & Financial Infrastructure'
    for nav in wrap.xpath('.//nav[@aria-label]'):
        nav.set('aria-label', 'Related pages')
    for aside in wrap.xpath('.//aside[contains(@class,"masar-editorial-review")]'):
        aside.find('strong').text = 'Internal draft — approval required before publication'
        for paragraph in aside.findall('p'):
            if paragraph.find('bdi') is not None:
                paragraph.text = 'Intended URL after approval: '
    for anchor in wrap.xpath('.//a[@href]'):
        href = anchor.get('href')
        if href.startswith('/') and not href.startswith('//'):
            anchor.set('href', '/en' if href == '/' else '/en' + href)
    if ARABIC.search(''.join(wrap.itertext())):
        raise ValueError('Untranslated generated content: ' + page['slug'])
    return layout


def bilingual_arch(current, page, source, contact_available=True):
    root = parse(current)
    if root.get('t-name') != view_key(page['slug']):
        raise ValueError('Unexpected managed view key')
    preserved = copy.deepcopy(arabic_layout(current))
    hero = preserved.xpath('.//section[@id="masar-content-top"]')
    hero_style = hero[0].get('style') if hero else None
    translated = english_layout(page, source, contact_available, hero_style)
    result = etree.Element('t', attrib=dict(root.attrib))
    en = etree.SubElement(result, 't', {'t-if': "(request.env.lang or '').startswith('en')"})
    en.append(translated)
    ar = etree.SubElement(result, 't', {'t-else': ''})
    ar.append(preserved)
    encoded = etree.tostring(result, encoding='unicode')
    if layout_bytes(arabic_layout(encoded)) != layout_bytes(arabic_layout(current)):
        raise ValueError('Arabic layout changed unexpectedly')
    return encoded

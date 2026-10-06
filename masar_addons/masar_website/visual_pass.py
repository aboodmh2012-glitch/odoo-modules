"""Patch live website views for the MASAR visual pass.

Pure string transforms live here so they can be tested without Odoo.
``visual_seed.py`` calls ``apply(env)`` from an Odoo shell.
"""
from __future__ import annotations

import re

HERO_BY_URL = {
    "/about": "about",
    "/business": "business",
    "/personal": "personal",
    "/institutions": "institutions",
    "/developers": "developers",
    "/security-compliance": "security",
    "/solutions": "solutions",
    "/solutions/accounts-cards": "accounts",
    "/solutions/pos": "pos",
    "/solutions/payment-gateway": "gateway",
    "/solutions/payouts": "payouts",
    "/solutions/bill-payments": "bills",
    "/solutions/atm-cash": "atm",
    "/partners": "institutions",
    "/pricing": "business",
    "/help": "personal",
    "/help/faq": "personal",
    "/help/stay-safe": "security",
}

# Longer phrases first so a heading maps to one image.
SOLUTION_NEEDLES = (
    ("الحسابات والبطاقات", "accounts"),
    ("accounts & cards", "accounts"),
    ("accounts and cards", "accounts"),
    ("نقاط البيع", "pos"),
    ("قبول المدفوعات", "pos"),
    ("point of sale", "pos"),
    ("payment acceptance", "pos"),
    ("بوابة الدفع", "gateway"),
    ("payment gateway", "gateway"),
    ("المدفوعات الجماعية", "payouts"),
    ("bulk payments", "payouts"),
    ("سداد الفواتير", "bills"),
    ("bill payments", "bills"),
    ("الصرافات", "atm"),
    ("الوصول النقدي", "atm"),
    ("atms and cash", "atm"),
    ("atm & cash", "atm"),
    ("atm", "atm"),
)

ABOUT_INTRO = """<section class="masar-hero masar-hero--about" id="about-hero">
<div class="masar-hero__glow" aria-hidden="true"/>
<div class="masar-hero__inner">
<p class="masar-hero__brand"><t t-if="(lang or '').startswith('ar')">عن مسار</t><t t-else="">About MASAR</t></p>
<h1 class="masar-hero__title"><t t-if="(lang or '').startswith('ar')">نبني مسارًا أبسط لحركة الأموال.</t><t t-else="">Building a simpler path for money.</t></h1>
<p class="masar-hero__lead"><t t-if="(lang or '').startswith('ar')">مسار شركة تقنية مالية تطور خدمات وبنية دفع رقمية للأفراد والأعمال والمؤسسات.</t><t t-else="">MASAR is a financial technology company developing payment services and financial infrastructure for people, businesses, and institutions.</t></p>
</div>
</section>
<section class="masar-highlights">
<div class="masar-wrap masar-highlights__grid">
<div class="masar-highlight"><span>01</span><b><t t-if="(lang or '').startswith('ar')">الموثوقية</t><t t-else="">Reliability</t></b></div>
<div class="masar-highlight"><span>02</span><b><t t-if="(lang or '').startswith('ar')">الأمان</t><t t-else="">Security</t></b></div>
<div class="masar-highlight"><span>03</span><b><t t-if="(lang or '').startswith('ar')">الشفافية</t><t t-else="">Transparency</t></b></div>
<div class="masar-highlight"><span>04</span><b><t t-if="(lang or '').startswith('ar')">التكامل</t><t t-else="">Interoperability</t></b></div>
</div>
</section>
"""

_FONT_RULE = re.compile(
    r"font-family\s*:\s*(?:var\(\s*--masar-(?:display|font)\s*\)|'Cairo'[^;]*|\"Cairo\"[^;]*)\s*(?:!important\s*)?;",
    re.I,
)
_CAIRO_IMPORT = re.compile(
    r"@import\s+url\(\s*['\"][^'\"]*Cairo[^'\"]*['\"]\s*\)\s*;",
    re.I,
)
_OVERLAY_STOP = {
    "rgba(0,0,0,.92)": "rgba(0,0,0,.78)",
    "rgba(0,0,0,.78)": "rgba(0,0,0,.60)",
    "rgba(0,0,0,.35)": "rgba(0,0,0,.26)",
    "rgba(0,0,0,.15)": "rgba(0,0,0,.08)",
    "rgba(0,0,0,0.92)": "rgba(0,0,0,.78)",
    "rgba(0,0,0,0.78)": "rgba(0,0,0,.60)",
    "rgba(0,0,0,0.35)": "rgba(0,0,0,.26)",
    "rgba(0,0,0,0.15)": "rgba(0,0,0,.08)",
}
_OVERLAY_RE = re.compile(r"rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0?\.(?:92|78|35|15)\s*\)")
_BANNER_MARKER = "masar-banner-overlay-soft"


def strip_forced_fonts(arch):
    if "font-family" not in arch and "Cairo" not in arch:
        return arch
    arch = _CAIRO_IMPORT.sub("", arch)
    return _FONT_RULE.sub("", arch)


def lighten_banner_css(arch):
    if "masar-banner" not in arch or _BANNER_MARKER in arch:
        return arch

    def repl(match):
        raw = re.sub(r"\s+", "", match.group(0))
        return _OVERLAY_STOP.get(raw, match.group(0))

    arch = _OVERLAY_RE.sub(repl, arch)
    arch = re.sub(
        r"(\.masar-banner__bg\s*\{[^}]*?opacity\s*:\s*)0?\.55",
        r"\g<1>.68",
        arch,
    )
    if "/* ===== Banner slider ===== */" in arch:
        arch = arch.replace(
            "/* ===== Banner slider ===== */",
            "/* ===== Banner slider ===== */ /* %s */" % _BANNER_MARKER,
            1,
        )
    else:
        arch += "\n/* %s */" % _BANNER_MARKER
    return arch


def ensure_hero_class(arch, slug):
    token = "masar-hero--%s" % slug
    if token in arch:
        return arch

    def repl(match):
        classes = match.group(1)
        if token in classes or not re.search(r"(?:^|\s)masar-hero(?:\s|$)", classes):
            return match.group(0)
        return 'class="%s %s"' % (classes, token)

    return re.sub(r'class="([^"]*)"', repl, arch)


def enrich_about(arch):
    if "masar-highlights" not in arch and 'id="about"' in arch:
        arch, count = re.subn(
            r'<section\b[^>]*\bid="about"[^>]*>',
            ABOUT_INTRO + r"\g<0>",
            arch,
            count=1,
        )
        if not count and "<div" in arch:
            arch = ABOUT_INTRO + arch
    return ensure_hero_class(arch, "about")


def _solution_slug(title):
    folded = re.sub(r"\s+", " ", title).strip().lower()
    for needle, slug in SOLUTION_NEEDLES:
        if needle.lower() in folded:
            return slug
    return None


def retarget_solution_images(arch):
    heads = list(re.finditer(r"<h2\b[^>]*>(.*?)</h2>", arch, flags=re.I | re.S))
    for head in reversed(heads):
        title = re.sub(r"<[^>]+>", "", head.group(1))
        slug = _solution_slug(title)
        if not slug:
            continue
        start = max(0, head.start() - 1600)
        window = arch[start:head.start()]
        srcs = list(re.finditer(r'src="[^"]*"', window))
        if not srcs:
            continue
        last = srcs[-1]
        new = 'src="/masar_website/static/src/img/solutions/%s.jpg"' % slug
        abs_start = start + last.start()
        abs_end = start + last.end()
        if arch[abs_start:abs_end] == new:
            continue
        arch = arch[:abs_start] + new + arch[abs_end:]
    return arch


def transform_page(url, arch):
    arch = strip_forced_fonts(arch)
    arch = lighten_banner_css(arch)
    if url == "/about":
        arch = enrich_about(arch)
    else:
        slug = HERO_BY_URL.get(url)
        if slug:
            arch = ensure_hero_class(arch, slug)
    if url == "/solutions":
        arch = retarget_solution_images(arch)
    return arch


def _languages(env):
    langs = list(env["res.lang"].sudo().search([]).mapped("code"))
    for extra in ("en_US", "ar_001"):
        if extra not in langs:
            langs.append(extra)
    return langs


def _read_arch(view, lang):
    try:
        arch = view.with_context(lang=lang).arch_db
    except Exception:
        return None
    return arch if isinstance(arch, str) else None


def apply(env):
    View = env["ir.ui.view"].sudo()
    Page = env["website.page"].sudo()
    langs = _languages(env)
    changed = 0
    seen = set()

    pages = Page.search([("url", "in", list(HERO_BY_URL))])
    for page in pages:
        view = page.view_id
        if not view:
            continue
        seen.add(view.id)
        for lang in langs:
            arch = _read_arch(view, lang)
            if not arch:
                continue
            new = transform_page(page.url, arch)
            if new != arch:
                try:
                    view.with_context(lang=lang).write({"arch_db": new})
                except Exception as exc:
                    print("MASAR_VISUAL_PASS_SKIP page=%s lang=%s %s" % (page.url, lang, exc))
                    continue
                changed += 1

    extras = View.search([
        "|",
        ("arch_db", "ilike", "masar-banner__overlay"),
        "&",
        ("arch_db", "ilike", "masar-site"),
        "|",
        ("arch_db", "ilike", "--masar-display"),
        ("arch_db", "ilike", "Cairo"),
    ])
    for view in extras:
        if view.id in seen:
            continue
        for lang in langs:
            arch = _read_arch(view, lang)
            if not arch:
                continue
            new = lighten_banner_css(strip_forced_fonts(arch))
            if new != arch:
                try:
                    view.with_context(lang=lang).write({"arch_db": new})
                except Exception as exc:
                    print("MASAR_VISUAL_PASS_SKIP view=%s lang=%s %s" % (view.id, lang, exc))
                    continue
                changed += 1

    print("MASAR_VISUAL_PASS=%s" % changed)
    return changed


# Orange hex only. Do not flip stored black surfaces or white type here:
# header, footer, and heroes share those tokens, and a blind swap paints
# navy text on a navy bar. masar_brand_fix.css owns the light/dark split.
_BRAND_REPLACEMENTS = (
    ("#ff5a1f", "#FF7A00"),
    ("#f2681e", "#FF7A00"),
    ("#F2681E", "#FF7A00"),
    ("#e04812", "#FF5A00"),
    ("#d45512", "#FF5A00"),
    ("242,104,30", "255, 122, 0"),
    ("242, 104, 30", "255, 122, 0"),
)


def retint_stored_brand(arch):
    lowered = arch.lower()
    if (
        "masar-site-overrides" not in arch
        and "masar_brand_colors" not in arch
        and "#ff5a1f" not in lowered
        and "#f2681e" not in lowered
    ):
        return arch
    for old, new in _BRAND_REPLACEMENTS:
        arch = arch.replace(old, new)
    return arch


def apply_brand(env):
    View = env["ir.ui.view"].sudo()
    langs = _languages(env)
    changed = 0
    views = View.search([
        "|",
        "|",
        "|",
        ("arch_db", "ilike", "masar-site-overrides"),
        ("arch_db", "ilike", "masar_brand_colors"),
        ("arch_db", "ilike", "#ff5a1f"),
        ("arch_db", "ilike", "#F2681E"),
    ])
    for view in views:
        for lang in langs:
            arch = _read_arch(view, lang)
            if not arch:
                continue
            new = retint_stored_brand(arch)
            if new != arch:
                try:
                    view.with_context(lang=lang).write({"arch_db": new})
                except Exception as exc:
                    print("MASAR_BRAND_SKIP view=%s lang=%s %s" % (view.id, lang, exc))
                    continue
                changed += 1
    print("MASAR_BRAND_COLORS=%s" % changed)
    return changed

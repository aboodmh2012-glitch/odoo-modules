"""Resolve public-site copy for the active language.

English (``en``) is the base catalog. Every other language is a partial or
full overlay of the same shape. Missing keys fall back to English, so a new
language can be added before every sentence is translated.

Add a language:

1. Create ``copy/locales/<prefix>.py`` exporting ``OVERLAY`` (same shape as
   ``en.CATALOG``; lists replace the English list, dicts merge).
2. Register it in ``LOCALES`` below. Pass ``rtl=True`` for right-to-left
   languages.
3. Enable that language on the website. The header switcher lists whatever
   languages the website has; it does not hardcode English and Arabic.
"""

from __future__ import annotations

import copy
from datetime import date

from .locales import ar, en

DEFAULT_LOCALE = "en"
RTL_LOCALES = {"ar", "fa", "he", "ur"}

LOCALES = {
    DEFAULT_LOCALE: en.CATALOG,
    "ar": ar.OVERLAY,
}


def register_locale(code, catalog, rtl=False):
    """Register ``code`` (a language prefix such as ``fr``) at runtime.

    Used by tests and by any later locale module that should not edit this
    file's import list. Production locales should still be added to
    ``LOCALES`` so they load with the addon.
    """
    prefix = (code or "").split("_")[0].lower()
    if not prefix or prefix == DEFAULT_LOCALE:
        raise ValueError("Register an overlay prefix, not the default locale")
    LOCALES[prefix] = catalog
    if rtl:
        RTL_LOCALES.add(prefix)
    return prefix


def locale_for(lang_code):
    """Map an Odoo lang code (``ar_001``, ``en_US``) to a catalog prefix."""
    code = (lang_code or "").replace("-", "_").lower()
    if code in LOCALES:
        return code
    prefix = code.split("_")[0]
    if prefix in LOCALES:
        return prefix
    return DEFAULT_LOCALE


def _deep_merge(base, overlay):
    """Merge overlay onto base. Dicts merge; lists and scalars replace."""
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = {}
        for key, value in base.items():
            if key in overlay:
                merged[key] = _deep_merge(value, overlay[key])
            else:
                merged[key] = copy.deepcopy(value)
        for key, value in overlay.items():
            if key not in base:
                merged[key] = copy.deepcopy(value)
        return merged
    return copy.deepcopy(overlay)


def get_copy(lang_code=None):
    """Return a fresh catalog for ``lang_code``, with English fallback."""
    locale = locale_for(lang_code)
    merged = _deep_merge(LOCALES[DEFAULT_LOCALE], LOCALES.get(locale) or {})
    merged["_meta"] = {
        "locale": locale,
        "dir": "rtl" if locale in RTL_LOCALES else "ltr",
        "year": date.today().year,
    }
    return merged


def normalize_public_path(path, lang_prefixes):
    """Strip a leading website language prefix from a request path."""
    raw = (path or "/").split("?", 1)[0].split("#", 1)[0]
    if not raw.startswith("/"):
        raw = "/" + raw
    parts = [part for part in raw.split("/") if part]
    prefixes = {prefix.lower() for prefix in (lang_prefixes or []) if prefix}
    if parts and parts[0].lower() in prefixes:
        parts = parts[1:]
    if not parts:
        return "/"
    return "/" + "/".join(parts)


def is_current(path, href):
    """True when ``href`` is the active page, ignoring a hash anchor."""
    here = path or "/"
    target = (href or "/").split("#", 1)[0].rstrip("/") or "/"
    if target == "/":
        return here == "/"
    return here == target or here.startswith(target + "/")

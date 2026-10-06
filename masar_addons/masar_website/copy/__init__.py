"""Public-site copy catalogs.

English is the default locale. Other languages are overlays registered in
``registry.LOCALES``. See ``registry.py`` for how to add a language.
"""

from .registry import get_copy, is_current, locale_for, normalize_public_path, register_locale

__all__ = [
    "get_copy",
    "is_current",
    "locale_for",
    "normalize_public_path",
    "register_locale",
]

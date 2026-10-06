{
    "name": "MASAR UI Tweaks",
    "summary": "Tidy backend systray for MASAR Pay (no web_responsive)",
    "version": "20.0.2.0.0",
    "category": "Extra Tools",
    "author": "MASAR",
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    "depends": ["web", "masar_theme"],
    "description": """
MASAR UI Tweaks
===============
- Hides non-essential systray quick-action icons when present.
- No longer depends on web_responsive apps-menu preferences (launcher is native).
""",
    "data": [],
    "assets": {
        "web.assets_backend": [
            "masar_ui_tweaks/static/src/scss/systray.scss",
        ],
    },
}

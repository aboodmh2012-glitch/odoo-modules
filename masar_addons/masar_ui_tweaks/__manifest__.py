{
    "name": "MASAR UI Tweaks",
    "summary": "Tidy backend systray for MASAR Pay (no web_responsive)",
    "version": "20.0.2.3.0",
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
- Shortens the company switcher label in the navy topbar.
- Turns off first-run tours and public signup leftovers.
- No longer depends on web_responsive apps-menu preferences (launcher is native).
""",
    "data": [
        "views/res_users_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "assets": {
        "web.assets_backend": [
            "masar_ui_tweaks/static/src/scss/systray.scss",
        ],
    },
}

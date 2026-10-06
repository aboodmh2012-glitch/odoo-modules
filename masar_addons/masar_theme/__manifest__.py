{
    "name": "MASAR Theme",
    "summary": "MASAR Pay Application Design System for Odoo 20 backend",
    "version": "20.0.2.0.0",
    "category": "Themes/Backend",
    "author": "MASAR",
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    "depends": ["web", "auth_passkey", "website"],
    "description": """
MASAR Theme
===========
Odoo 20 MASAR Pay backend design system:

- Layered design tokens (primitive → semantic → component → state)
- Spacing / radius / elevation / typography / density scales
- App shell, native Owl 3 apps launcher, forms, lists, kanban, control panel
- Fintech numeric UX + accessibility focus/touch rules
- Branded /web/login with official artwork + official M icon
- Backend PWA manifest + favicon / apple-touch branding

Does not vendor web_responsive — launcher is built on Odoo 20 NavBar.
Does not modify the public website (masar_website).
Login is username/password only.
    """,
    "data": [
        "views/login_templates.xml",
        "views/webclient_templates.xml",
        "views/branding_templates.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            ("prepend", "masar_theme/static/src/scss/primary_variables.scss"),
        ],
        "web.assets_backend": [
            "masar_theme/static/src/js/navigation.js",
            "masar_theme/static/src/xml/navigation.xml",
            "masar_theme/static/src/scss/brand_tokens.scss",
            "masar_theme/static/src/scss/masar_colors.scss",
            "masar_theme/static/src/scss/backend_shell.scss",
            "masar_theme/static/src/scss/backend_control_panel.scss",
            "masar_theme/static/src/scss/backend_forms.scss",
            "masar_theme/static/src/scss/backend_lists.scss",
            "masar_theme/static/src/scss/backend_kanban.scss",
            "masar_theme/static/src/scss/backend_components.scss",
            "masar_theme/static/src/scss/backend_finance.scss",
            "masar_theme/static/src/scss/backend_a11y.scss",
            "masar_theme/static/src/scss/app_menu.scss",
        ],
        "web.assets_frontend": [
            "masar_theme/static/src/scss/brand_tokens.scss",
            "masar_theme/static/src/scss/login.scss",
        ],
    },
}

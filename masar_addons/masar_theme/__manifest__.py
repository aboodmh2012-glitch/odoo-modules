{'application': False,
 'assets': {'web._assets_primary_variables': [('prepend',
                                               'masar_theme/static/src/scss/primary_variables.scss')],
            'web.assets_backend': ['masar_theme/static/src/js/navigation.js',
                                   'masar_theme/static/src/xml/navigation.xml',
                                   'masar_theme/static/src/scss/brand_tokens.scss',
                                   'masar_theme/static/src/scss/masar_colors.scss',
                                   'masar_theme/static/src/scss/backend_shell.scss',
                                   'masar_theme/static/src/scss/backend_control_panel.scss',
                                   'masar_theme/static/src/scss/backend_forms.scss',
                                   'masar_theme/static/src/scss/backend_lists.scss',
                                   'masar_theme/static/src/scss/backend_kanban.scss',
                                   'masar_theme/static/src/scss/backend_components.scss',
                                   'masar_theme/static/src/scss/backend_finance.scss',
                                   'masar_theme/static/src/scss/backend_a11y.scss',
                                   'masar_theme/static/src/scss/app_menu.scss'],
            'web.assets_frontend': ['masar_theme/static/src/scss/brand_tokens.scss',
                                    'masar_theme/static/src/scss/login.scss']},
 'author': 'MASAR',
 'auto_install': False,
 'category': 'Themes/Backend',
 'data': ['views/login_templates.xml',
          'views/webclient_templates.xml',
          'views/branding_templates.xml'],
 'depends': ['web', 'web_responsive', 'auth_passkey', 'website'],
 'description': '\n'
                'MASAR Theme\n'
                '===========\n'
                'Maintainable MASAR Pay backend design system for Odoo 19:\n'
                '\n'
                '- Layered design tokens (primitive → semantic → component → state)\n'
                '- Spacing / radius / elevation / typography / density scales\n'
                '- App shell, apps launcher, forms, lists, kanban, control panel\n'
                '- Fintech numeric UX + accessibility focus/touch rules\n'
                '- Branded /web/login with official artwork + official M icon\n'
                '\n'
                'Does not modify the public website (masar_website).\n'
                'Does not vendor Monodoo or third-party theme packs — architecture adapted '
                'in-house.\n'
                'Login is username/password only.\n'
                '    ',
 'installable': True,
 'license': 'LGPL-3',
 'name': 'MASAR Theme',
 'summary': 'MASAR Pay Application Design System for Odoo 19 backend',
 'version': '20.0.1.15.0'}

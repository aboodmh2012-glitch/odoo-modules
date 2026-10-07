{'application': True,
 'author': 'Les services de consultation Blue Fox, Inc.; MASAR',
 'auto_install': False,
 'category': 'Governance',
 'data': ['security/corporate_security.xml',
          'security/ir.access.csv',
          'data/corporate_cron.xml',
          'data/corporate_meeting_data.xml',
          'report/corporate_resolution_templates.xml',
          'views/corporate_resolution_views.xml',
          'views/corporate_director_views.xml',
          'views/corporate_officer_views.xml',
          'views/corporate_committee_views.xml',
          'views/corporate_meeting_views.xml',
          'views/corporate_compliance_views.xml',
          'views/document_page_views.xml',
          'views/report_drilldown_actions.xml',
          'views/corporate_menus.xml'],
 'depends': ['mail', 'contacts', 'hr', 'document_page', 'knowledge_control'],
 'description': '\n'
                'Corporate Governance (MASAR port of Blue Fox / Symbifox bf_corporate_governance)\n'
                '================================================================================\n'
                '\n'
                'Upstream source: Blue Fox ``bf_corporate_governance`` @ 4a0f400 (was LGPL-3).\n'
                '\n'
                'MASAR shipping license: **AGPL-3** (ADR-8) because this module depends on and\n'
                'extends AGPL Knowledge / Knowledge Control. Blue Fox copyright retained.\n'
                '\n'
                'Adaptations:\n'
                '* Odoo 19 compatibility\n'
                '* Depends on ``mail``, ``contacts``, ``document_page``, ``knowledge_control``\n'
                '* Minute Book on OCA ``document.page``; evidence = frozen '
                '``document.page.history``\n'
                '* ``document_ids`` = navigation only; ``approved_history_ids`` = exact evidence\n'
                '* No Quebec/REQ seed data; English-neutral UI (AR/EN i18n later)\n'
                '* Resolution PDF uses company logo + neutral palette (no bf_lexend / _pkm_brand)\n'
                '* Multi-company record rules; idempotent compliance reminder cron\n'
                '\n'
                'See docs/THIRD_PARTY_NOTICES.md.\n'
                '    ',
 'installable': True,
 'license': 'AGPL-3',
 'name': 'Corporate Governance',
 'summary': 'Resolutions, directors/officers, board committees, compliance, Minute Book',
 'version': '20.0.1.3.1',
 'website': 'https://masar.sa'}

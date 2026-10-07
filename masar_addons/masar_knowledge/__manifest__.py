{'application': False,
 'author': 'MASAR',
 'auto_install': False,
 'category': 'Knowledge',
 'data': ['security/ir.access.csv',
          'data/knowledge_tags.xml',
          'views/knowledge_tag_views.xml',
          'views/document_page_views.xml'],
 'depends': ['document_page', 'hr'],
 'description': '\n'
                'MASAR Knowledge — document control\n'
                '==================================\n'
                'Adds structured governance metadata to Knowledge pages (``document.page``)\n'
                'instead of burying it in the page body, following information-architecture\n'
                'best practice (Microsoft IA), knowledge-base conventions (Atlassian) and the\n'
                'knowledge-management lifecycle of ISO 30401:\n'
                '\n'
                '- Owner department + document owner (accountability).\n'
                '- Document code and classification (public / internal / confidential /\n'
                '  restricted).\n'
                '- Effective date and next-review date (lifecycle).\n'
                '- Lifecycle status (draft / active / under review / retired).\n'
                '- Cross-cutting tags for topics that span several manuals (AML, KYC,\n'
                '  information security, data protection, SLA, …).\n'
                '\n'
                'Self-contained: adds fields, a "Document control" page on the Knowledge form,\n'
                'search filters/group-bys, and a tags configuration menu. It does not modify\n'
                'existing content or other modules.\n',
 'installable': True,
 'license': 'LGPL-3',
 'name': 'MASAR Knowledge',
 'summary': 'Document control metadata for the MASAR knowledge base (owner, code, classification, '
            'effective/review dates, lifecycle, tags)',
 'version': '20.0.1.0.0',
 'website': 'https://masar.sa'}

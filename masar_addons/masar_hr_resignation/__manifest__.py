# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MASAR HR Resignation',
    'summary': 'Employee resignation / termination workflow with deferred archive',
    'version': '20.0.1.0.1',
    'author': 'MASAR',
    'website': 'https://masar.sa',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': ['hr', 'mail'],
    'data': ['security/ir.access.csv', 'data/ir_sequence_data.xml', 'data/ir_cron_data.xml', 'views/hr_resignation_views.xml', 'views/menus.xml'],
    'installable': True,
    'application': False,
}

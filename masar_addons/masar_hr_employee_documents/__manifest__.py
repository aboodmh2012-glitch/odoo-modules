# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MASAR HR Employee Documents',
    'summary': 'Employee documents with expiry notifications and entry/exit checklist',
    'version': '20.0.1.1.0',
    'author': 'MASAR',
    'website': 'https://masar.sa',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': ['hr', 'mail'],
    'data': ['security/ir.access.csv', 'data/ir_cron_data.xml', 'views/hr_employee_document_type_views.xml', 'views/hr_employee_document_views.xml', 'views/menus.xml'],
    'installable': True,
    'application': False,
}

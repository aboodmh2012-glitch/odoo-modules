# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MASAR HR Disciplinary',
    'summary': 'Employee disciplinary cases with regulation catalog, investigation, approval, appeal and financial impact tracking',
    'version': '20.0.1.1.1',
    'author': 'MASAR',
    'website': 'https://masar.sa',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': ['hr', 'mail', 'document_page'],
    'data': ['security/hr_disciplinary_security.xml', 'security/ir.access.csv', 'data/ir_sequence_data.xml', 'data/mail_activity_data.xml', 'views/hr_discipline_offense_type_views.xml', 'views/hr_discipline_sanction_type_views.xml', 'views/hr_disciplinary_case_views.xml', 'views/hr_employee_views.xml', 'views/menus.xml'],
    'installable': True,
    'application': False,
    'demo': [],
}

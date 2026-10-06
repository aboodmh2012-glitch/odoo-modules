# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MASAR HR Attendance Regularization',
    'summary': 'Request and approve attendance corrections linked to hr.attendance',
    'version': '20.0.1.0.0',
    'author': 'MASAR',
    'website': 'https://masar.sa',
    'license': 'AGPL-3',
    'category': 'Human Resources/Attendances',
    'depends': ['hr_attendance', 'mail'],
    'data': ['security/ir.access.csv', 'data/ir_sequence_data.xml', 'views/hr_attendance_regularization_views.xml', 'views/menus.xml'],
    'installable': True,
    'application': False,
}

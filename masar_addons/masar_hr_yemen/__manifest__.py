# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MASAR HR Yemen Configuration',
    'summary': 'Yemen Labor Law-oriented seeds, company HR policy settings, and light extensions on existing MASAR HR modules',
    'version': '20.0.1.2.0',
    'author': 'MASAR',
    'website': 'https://msarpay.com',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': ['hr', 'hr_holidays', 'hr_attendance', 'hr_recruitment', 'mail', 'document_page', 'helpdesk_mgmt', 'helpdesk_type', 'masar_hr_disciplinary', 'masar_hr_employee_documents', 'masar_hr_attendance_regularization', 'masar_hr_employee_transfer', 'masar_hr_resignation'],
    'data': ['security/ir.access.csv', 'data/hr_discipline_sanction_data.xml', 'data/hr_discipline_offense_data.xml', 'data/hr_document_type_data.xml', 'data/hr_attendance_regularization_category_data.xml', 'data/hr_leave_type_data.xml', 'data/helpdesk_grievance_type_data.xml', 'data/mail_activity_data.xml', 'data/mail_activity_plan_data.xml', 'data/ir_cron_data.xml', 'report/service_certificate_report.xml', 'views/res_config_settings_views.xml', 'views/hr_discipline_type_views.xml', 'views/hr_disciplinary_case_views.xml', 'views/hr_employee_transfer_views.xml', 'views/hr_resignation_views.xml', 'wizard/leave_allocation_preview_views.xml', 'views/menus.xml'],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'demo': [],
}

# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MASAR HR Employee Transfer",
    "summary": "Transfer employees between companies/departments without cloning",
    "version": "20.0.1.0.0",
    "author": "MASAR",
    "website": "https://masar.sa",
    "license": "AGPL-3",
    "category": "Human Resources",
    "depends": ["hr", "mail"],
    "data": [
        "security/hr_employee_transfer_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/hr_employee_transfer_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": False,
}

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Date
from odoo.tests.common import TransactionCase


class TestMasarSalaryFormula(TransactionCase):
    def test_one_million_basic_matches_masar_card(self):
        structure = self.env.ref("payroll.structure_base")
        employee = self.env["hr.employee"].create({"name": "MASAR Formula Check"})
        employee.version_id.write(
            {
                "contract_date_start": Date.today(),
                "wage": 1000000.0,
                "struct_id": structure.id,
                "schedule_pay": "monthly",
            }
        )
        payslip = self.env["hr.payslip"].create({"employee_id": employee.id})
        payslip.onchange_employee()
        payslip.compute_sheet()
        totals = {line.code: line.total for line in payslip.line_ids}
        self.assertAlmostEqual(totals["BASIC"], 1000000.0)
        self.assertAlmostEqual(totals["APPEARANCE"], 250000.0)
        self.assertAlmostEqual(totals["TRANSPORT"], 200000.0)
        self.assertAlmostEqual(totals["GROSS"], 1450000.0)
        self.assertAlmostEqual(totals["CINS"], 90000.0)
        self.assertAlmostEqual(totals["TAX"], -148500.0)
        self.assertAlmostEqual(totals["EINS"], -60000.0)
        self.assertAlmostEqual(totals["NET"], 1241500.0)
        self.assertAlmostEqual(totals["ECOST"], 1540000.0)

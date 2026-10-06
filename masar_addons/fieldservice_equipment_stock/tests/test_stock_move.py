# Copyright (C) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestStockMove(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Move = cls.env["stock.move"]
        cls.stock_location = cls.env.ref("stock.stock_location_customers")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

    def test_action_done(self):
        # Create product template
        templateAB = self.env["product.template"].create(
            {
                "name": "templAB",
                "uom_id": self.uom_unit.id,
                "type": "consu",
                "is_storable": True,
                "tracking": "none",
            }
        )

        # Create product A and B
        productA = self.env["product.product"].create(
            {
                "name": "product A",
                "standard_price": 1,
                "type": "consu",
                "is_storable": True,
                "tracking": "none",
                "uom_id": self.uom_unit.id,
                "default_code": "A",
                "product_tmpl_id": templateAB.id,
            }
        )

        # Create a stock move from INCOMING to STOCK
        move_vals = {
            "location_id": self.supplier_location.id,
            "location_dest_id": self.stock_location.id,
            "product_id": productA.id,
            "product_uom_qty": 2,
        }
        Move = self.env["stock.move"]
        if "product_uom_id" in Move._fields:
            move_vals["product_uom_id"] = productA.uom_id.id
        elif "uom_id" in Move._fields:
            move_vals["uom_id"] = productA.uom_id.id
        else:
            move_vals["product_uom"] = productA.uom_id.id
        stockMoveInA = Move.create(move_vals)

        stockMoveInA.quantity = stockMoveInA.product_uom_qty
        stockMoveInA._action_confirm()
        stockMoveInA._action_assign()
        stockMoveInA.picked = True
        stockMoveInA._action_done()

        self.assertEqual("done", stockMoveInA.state)

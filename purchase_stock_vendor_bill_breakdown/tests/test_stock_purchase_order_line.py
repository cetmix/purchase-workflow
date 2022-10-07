from odoo.tests import Form, tagged

from odoo.addons.purchase_vendor_product_breakdown.tests.common import (
    PurchaseTransactionCase,
)


@tagged("post_install", "-at_install")
class TestStockPurchaseOrderLine(PurchaseTransactionCase):
    # purchase_vendor_product_breakdown
    # product_product_test_1
    def setUp(self):
        super(TestStockPurchaseOrderLine, self).setUp()
        self.purchase_order_1 = self.get_create_order(self.res_partner_supplier)
        self.purchase_order_2 = self.get_create_order(
            self.res_partner_test_not_supplier
        )

    def get_create_order(self, partner):
        form = Form(self.env["purchase.order"])
        form.partner_id = partner
        with form.order_line.new() as line:
            line.name = self.product_product_test_1.name
            line.product_id = self.product_product_test_1
            line.product_qty = 10.0
        record = form.save()
        record.button_confirm()
        return record

    def test_stock_purchase_order_line_with_bill_components(self):
        order = self.purchase_order_1

        self.assertEqual(
            order.order_line.qty_received,
            0,
            msg="Received Qty must be equal 0",
        )

        components = order.order_line.mapped("component_ids")
        self.assertEqual(len(components), 2, msg="Components count must be equal 2")
        component_1, component_2 = list(order.order_line.mapped("component_ids"))
        self.assertEqual(component_1.total_qty, 0, msg="Total Qty must be equal 0")
        self.assertEqual(component_2.total_qty, 0, msg="Total Qty must be equal 0")

        picking = order.picking_ids[0]
        # Progress 6.0 out of the 10.0 ordered qty
        picking.move_lines.quantity_done = 6
        result_dict = picking.button_validate()
        # Create backorder
        self.env["stock.backorder.confirmation"].with_context(
            result_dict["context"]
        ).process()

        self.assertEqual(
            order.order_line.qty_received,
            6,
            msg="Received Qty must be equal 6",
        )

        # Get Product Components
        components = order.order_line.mapped("component_ids")
        component_1, component_2 = list(components)
        self.assertEqual(
            component_1.total_qty, 18.0, msg="Total Qty must be equal 18.0"
        )
        self.assertEqual(
            component_2.total_qty, 12.0, msg="Total Qty must be equal 12.0"
        )
        order.action_create_invoice()
        self.assertEqual(
            len(order.invoice_ids),
            1,
            msg="Invoice Count must be equal 1",
        )
        line = order.order_line
        self.assertEqual(line.qty_invoiced, 6, msg="Qty Invoiced must be equal 6")
        invoice_line_component_1 = line.invoice_lines.filtered(
            lambda invoice_line: invoice_line.product_id
            == self.product_product_component_test_1
        )
        self.assertEqual(
            round(invoice_line_component_1.quantity, 2), 18, msg="Qty must be equal 18"
        )
        invoice_line_component_2 = line.invoice_lines.filtered(
            lambda invoice_line: invoice_line.product_id
            == self.product_product_component_test_2
        )
        self.assertEqual(
            round(invoice_line_component_2.quantity, 2), 12, msg="Qty must be equal 12"
        )

        picking = order.picking_ids[1]
        # Progress 4.0 out of the 4.0 ordered qty
        picking.move_lines.quantity_done = 4.0
        result_dict = picking.button_validate()
        self.assertTrue(result_dict, msg="Result must be equal True")

        self.assertEqual(
            order.order_line.qty_received,
            10,
            msg="Received Qty must be equal 10",
        )

        components = order.order_line.mapped("component_ids")
        order.order_line._compute_qty_received()
        component_1, component_2 = list(components)
        self.assertEqual(
            component_1.total_qty, 30.0, msg="Total Qty must be equal 30.0"
        )
        self.assertEqual(
            component_2.total_qty, 20.0, msg="Total Qty must be equal 20.0"
        )
        order.action_create_invoice()

        self.assertEqual(
            len(order.invoice_ids),
            2,
            msg="Invoice Count must be equal 1",
        )
        line = order.order_line
        self.assertEqual(line.qty_invoiced, 10, msg="Qty Invoiced must be equal 10")
        invoice_line_component_1 = line.invoice_lines.filtered(
            lambda invoice_line: invoice_line.product_id
            == self.product_product_component_test_1
            and invoice_line.id != invoice_line_component_1.id
        )
        self.assertEqual(
            round(invoice_line_component_1.quantity, 2), 12, msg="Qty must be equal 12"
        )
        invoice_line_component_2 = line.invoice_lines.filtered(
            lambda invoice_line: invoice_line.product_id
            == self.product_product_component_test_2
            and invoice_line.id != invoice_line_component_2.id
        )
        self.assertEqual(
            round(invoice_line_component_2.quantity, 2), 8, msg="Qty must be equal 8"
        )

    def test_stock_purchase_order_line_without_bill_components(self):
        order = self.purchase_order_2
        self.assertEqual(
            order.order_line.qty_received,
            0,
            msg="Received Qty must be equal 0",
        )

        components = order.order_line.mapped("component_ids")
        self.assertEqual(len(components), 0, msg="Components count must be equal 0")
        picking = order.picking_ids[0]
        # Progress 10.0 out of the 10.0 ordered qty
        picking.move_lines.quantity_done = 10.0
        result_dict = picking.button_validate()
        order.action_create_invoice()
        self.assertTrue(result_dict, msg="Result must be equal True")
        self.assertEqual(
            order.order_line.qty_received,
            10,
            msg="Received Qty must be equal 0",
        )
        invoice_line_product = order.order_line.invoice_lines
        self.assertEqual(
            len(invoice_line_product), 1, msg="Invoice Qty must be equal 1"
        )
        self.assertEqual(
            round(invoice_line_product.quantity, 2), 10, msg="Qty must be equal 10"
        )

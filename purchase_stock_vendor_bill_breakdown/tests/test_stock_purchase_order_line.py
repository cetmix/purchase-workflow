from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockPurchaseOrderLine(TransactionCase):
    def setUp(self):
        super(TestStockPurchaseOrderLine, self).setUp()
        ResPartner = self.env["res.partner"]
        ProductProduct = self.env["product.product"]
        ProductSupplierInfo = self.env["product.supplierinfo"]
        uom_unit_id = self.ref("uom.product_uom_unit")
        currency_id = self.ref("base.EUR")

        self.res_partner_with_bill = ResPartner.create(
            {"name": "Bob", "bill_components": True}
        )
        self.res_partner_without_bill = ResPartner.create(
            {"name": "Bill", "bill_components": True}
        )

        self.product_product_for_supplierinfo = ProductProduct.create(
            {
                "name": "Product for SupplierInfo",
                "standard_price": 100.0,
                "type": "product",
                "uom_id": uom_unit_id,
            }
        )

        self.product_component_1 = ProductProduct.create(
            {
                "name": "Product Component #1",
                "standard_price": 3.0,
                "type": "product",
                "uom_id": uom_unit_id,
            }
        )

        self.product_component_2 = ProductProduct.create(
            {
                "name": "Product Component #2",
                "standard_price": 2.0,
                "type": "product",
                "uom_id": uom_unit_id,
            }
        )

        self.product_supplierinfo = ProductSupplierInfo.create(
            {
                "name": self.res_partner_with_bill.id,
                "product_id": self.product_product_for_supplierinfo.id,
                "currency_id": currency_id,
                "component_ids": [
                    (
                        0,
                        0,
                        {
                            "component_id": self.product_component_1.id,
                            "product_uom_qty": 3.0,
                            "product_uom_id": uom_unit_id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "component_id": self.product_component_2.id,
                            "product_uom_qty": 2.0,
                            "product_uom_id": uom_unit_id,
                        },
                    ),
                ],
            }
        )

        self.product_product_for_supplierinfo.write(
            {"seller_ids": [(6, 0, self.product_supplierinfo.ids)]}
        )

    def test_stock_purchase_order_line_with_bill_components(self):
        PurchaseOrder = self.env["purchase.order"]
        StockBackorderConfirmation = self.env["stock.backorder.confirmation"]

        form = Form(PurchaseOrder)
        form.partner_id = self.res_partner_with_bill
        with form.order_line.new() as line:
            line.name = (self.product_product_for_supplierinfo.name,)
            line.product_id = self.product_product_for_supplierinfo
            line.product_qty = 10.0
        purchase_order_record = form.save()
        purchase_order_record.button_confirm()

        self.assertEqual(
            purchase_order_record.order_line.qty_received,
            0,
            msg="Received Qty must be equal 0",
        )

        components = purchase_order_record.order_line.mapped("component_ids")
        self.assertEqual(len(components), 2, msg="Components count must be equal 2")
        component_1, component_2 = list(
            purchase_order_record.order_line.mapped("component_ids")
        )
        self.assertEqual(component_1.total_qty, 0, msg="Total Qty must be equal 0")
        self.assertEqual(component_2.total_qty, 0, msg="Total Qty must be equal 0")

        picking = purchase_order_record.picking_ids[0]
        # Progress 6.0 out of the 10.0 ordered qty
        picking.move_lines.quantity_done = 6
        result_dict = picking.button_validate()
        # Create backorder
        StockBackorderConfirmation.with_context(result_dict["context"]).process()

        self.assertEqual(
            purchase_order_record.order_line.qty_received,
            6,
            msg="Received Qty must be equal 6",
        )

        # Get Product Components
        components = purchase_order_record.order_line.mapped("component_ids")
        component_1, component_2 = list(components)
        self.assertEqual(
            component_1.total_qty, 18.0, msg="Total Qty must be equal 18.0"
        )
        self.assertEqual(
            component_2.total_qty, 12.0, msg="Total Qty must be equal 12.0"
        )
        purchase_order_record.action_create_invoice()
        self.assertEqual(
            len(purchase_order_record.invoice_ids),
            1,
            msg="Invoice Count must be equal 1",
        )
        line = purchase_order_record.order_line
        self.assertEqual(line.qty_invoiced, 6, msg="Qty Invoiced must be equal 6")
        invoice_line_component_1 = line.invoice_lines.filtered(
            lambda invoice_line: invoice_line.product_id == self.product_component_1
        )
        self.assertEqual(
            round(invoice_line_component_1.quantity, 2), 18, msg="Qty must be equal 18"
        )
        invoice_line_component_2 = line.invoice_lines.filtered(
            lambda invoice_line: invoice_line.product_id == self.product_component_2
        )
        self.assertEqual(
            round(invoice_line_component_2.quantity, 2), 12, msg="Qty must be equal 12"
        )

        picking = purchase_order_record.picking_ids[1]
        # Progress 4.0 out of the 4.0 ordered qty
        picking.move_lines.quantity_done = 4.0
        result_dict = picking.button_validate()
        self.assertTrue(result_dict, msg="Result must be equal True")

        self.assertEqual(
            purchase_order_record.order_line.qty_received,
            10,
            msg="Received Qty must be equal 10",
        )

        components = purchase_order_record.order_line.mapped("component_ids")
        purchase_order_record.order_line._compute_qty_received()
        component_1, component_2 = list(components)
        self.assertEqual(
            component_1.total_qty, 30.0, msg="Total Qty must be equal 30.0"
        )
        self.assertEqual(
            component_2.total_qty, 20.0, msg="Total Qty must be equal 20.0"
        )
        purchase_order_record.action_create_invoice()

        self.assertEqual(
            len(purchase_order_record.invoice_ids),
            2,
            msg="Invoice Count must be equal 1",
        )
        line = purchase_order_record.order_line
        self.assertEqual(line.qty_invoiced, 10, msg="Qty Invoiced must be equal 10")
        invoice_line_component_1 = line.invoice_lines.filtered(
            lambda invoice_line: invoice_line.product_id == self.product_component_1
            and invoice_line.id != invoice_line_component_1.id
        )
        self.assertEqual(
            round(invoice_line_component_1.quantity, 2), 12, msg="Qty must be equal 12"
        )
        invoice_line_component_2 = line.invoice_lines.filtered(
            lambda invoice_line: invoice_line.product_id == self.product_component_2
            and invoice_line.id != invoice_line_component_2.id
        )
        self.assertEqual(
            round(invoice_line_component_2.quantity, 2), 8, msg="Qty must be equal 8"
        )

    def test_stock_purchase_order_line_without_bill_components(self):
        PurchaseOrder = self.env["purchase.order"]

        form = Form(PurchaseOrder)
        form.partner_id = self.res_partner_without_bill
        with form.order_line.new() as line:
            line.name = (self.product_product_for_supplierinfo.name,)
            line.product_id = self.product_product_for_supplierinfo
            line.product_qty = 10.0
        purchase_order_record = form.save()
        purchase_order_record.button_confirm()

        self.assertEqual(
            purchase_order_record.order_line.qty_received,
            0,
            msg="Received Qty must be equal 0",
        )

        components = purchase_order_record.order_line.mapped("component_ids")
        self.assertEqual(len(components), 0, msg="Components count must be equal 0")
        picking = purchase_order_record.picking_ids[0]
        # Progress 10.0 out of the 10.0 ordered qty
        picking.move_lines.quantity_done = 10.0
        result_dict = picking.button_validate()
        purchase_order_record.action_create_invoice()
        self.assertTrue(result_dict, msg="Result must be equal True")
        self.assertEqual(
            purchase_order_record.order_line.qty_received,
            10,
            msg="Received Qty must be equal 0",
        )
        line = purchase_order_record.order_line
        invoice_line_product = line.invoice_lines
        self.assertEqual(
            len(invoice_line_product), 1, msg="Invoice Qty must be equal 1"
        )
        self.assertEqual(
            round(invoice_line_product.quantity, 2), 10, msg="Qty must be equal 10"
        )

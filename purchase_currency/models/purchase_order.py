# Copyright (C) 2025 Cetmix OÜ
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        # Check currency_id field exists
        if "currency_id" not in fields_list:
            return result
        default_purchase_currency = self.env.company.default_purchase_currency_id
        if default_purchase_currency:
            result["currency_id"] = default_purchase_currency.id
        return result

    @api.onchange("partner_id", "company_id")
    def onchange_partner_id(self):
        default_currency_id = self.env.company.default_purchase_currency_id.id
        if not default_currency_id:
            return super().onchange_partner_id()
        return super(
            PurchaseOrder, self.with_context(default_currency_id=default_currency_id)
        ).onchange_partner_id()

# © 2016 Chafique DELLI @ Akretion
# © 2017 Today Mourad EL HADJ MIMOUNE @ Akretion
# 2020 Manuel Calero - Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Purchase and Invoice Allowed Product",
    "summary": "This module allows to select only products that can be "
    "supplied by the vendor",
    "version": "14.0.2.3.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/purchase-workflow",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["aleuffre", "renda-dev"],
    "license": "AGPL-3",
    "depends": ["purchase", "base_view_inheritance_extension"],
    "data": [
        "security/purchase_security.xml",
        "views/res_partner_view.xml",
        "views/account_move_views.xml",
        "views/purchase_order_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}

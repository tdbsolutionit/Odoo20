from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_saleorder_modal(self):
        self.ensure_one()
        if hasattr(self, 'action_preview_sale_order'):
            return self.action_preview_sale_order()
        return True

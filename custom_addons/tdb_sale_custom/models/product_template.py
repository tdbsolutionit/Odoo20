from odoo import models
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_custom_delete(self):
        """Kiểm tra ràng buộc chi tiết trước khi xóa"""
        for product in self:
            # 1. Kiểm tra sản phẩm có nằm trong gói Combo nào không
            combo_items = self.env['product.combo.item'].sudo().search([
                ('product_id', 'in', product.product_variant_ids.ids)
            ])
            if combo_items:
                combo_names = ", ".join(combo_items.mapped('combo_id.name'))
                raise UserError(
                    f" KHÔNG THỂ XÓA SẢN PHẨM: '{product.name}'\n\n"
                    f" Lý do: Sản phẩm này đang nằm trong gói Combo: [{combo_names}].\n\n"
                    f" Hướng xử lý: Bạn cần vào gói Combo trên để xóa sản phẩm này ra trước, sau đó mới xóa sản phẩm được."
                )

            # 2. Kiểm tra sản phẩm đã phát sinh đơn bán hàng nào chưa
            sale_lines = self.env['sale.order.line'].sudo().search([
                ('product_template_id', '=', product.id)
            ], limit=1)
            if sale_lines:
                raise UserError(
                    f" KHÔNG THỂ XÓA SẢN PHẨM: '{product.name}'\n\n"
                    f" Lý do: Sản phẩm này đã phát sinh trong đơn bán hàng ({sale_lines.order_id.name}).\n\n"
                    f" Hướng xử lý: Để bảo vệ lịch sử hóa đơn và kế toán, hệ thống không cho phép xóa vĩnh viễn sản phẩm đã bán."
                )

            # Nếu không vướng gì thì xóa bình thường
            try:
                product.unlink()
            except Exception as e:
                raise UserError(f"Không thể xóa sản phẩm '{product.name}' do đang liên kết ở bảng khác: {e}")

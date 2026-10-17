from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection_add=[
            ('order_placed', 'Đơn đặt hàng'),
        ],
        ondelete={'order_placed': 'cascade'},
    )

    def action_place_order(self):
        """Khách chốt đặt hàng -> Chuyển sang trạng thái Đơn đặt hàng"""
        for order in self:
            order.state = "order_placed"

    def _confirmation_error_message(self):
        """Cho phép xác nhận đơn hàng khi đang ở trạng thái draft, sent hoặc order_placed"""
        self.ensure_one()
        if self.state not in {"draft", "sent", "order_placed"}:
            return self.env._("Some orders are not in a state requiring confirmation.")
        return False

    @api.model
    def _register_hook(self):
        res = super()._register_hook()
        try:
            # Tự động ẩn hoàn toàn báo cáo gốc 'Quotation / Order' khỏi menu Print để chỉ còn 'Báo giá đơn hàng (TDB)'
            report = self.env.ref("sale.action_report_saleorder", raise_if_not_found=False)
            if report and report.binding_model_id:
                report.sudo().write({"binding_model_id": False})
        except Exception:
            pass
        return res

    # === POPUP PREVIEW BÁO GIÁ ===#
    preview_html = fields.Html(compute="_compute_preview_html", sanitize=False)

    def _compute_preview_html(self):
        for order in self:
            ts = int(fields.Datetime.now().timestamp())
            pdf_url = f"/report/pdf/sale.report_saleorder/{order.id}?v={ts}"
            order.preview_html = (
                f'<iframe src="{pdf_url}" style="width: 100%; height: 86vh; border: none; display: block; background: #525659;"></iframe>'
            )

    def action_preview_sale_order(self):
        self.ensure_one()
        view_id = self.env.ref("tdb_sale_custom.view_sale_order_preview_modal", raise_if_not_found=False)
        view_id_val = view_id.id if view_id else False
        return {
            "name": f"{self.name} - Báo giá đơn hàng",
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(view_id_val, "form")],
            "target": "new",
            "context": {"dialog_size": "extra-large"},
        }

    def action_open_terms_modal(self):
        self.ensure_one()
        # Nếu chưa có điều khoản, tự động nạp mẫu 4 mục vào trước
        if not self.note:
            default_template = """
                <p><strong>1. Thông tin sản phẩm:</strong><br/>
                1.1. Sản phẩm mới 100%, đúng theo tiêu chuẩn kỹ thuật của nhà sản xuất.<br/>
                1.2. Hỗ trợ kỹ thuật và hướng dẫn sử dụng trong suốt quá trình triển khai.<br/>
                1.3. Bảo hành theo chính sách tiêu chuẩn của TDB Solution.</p>

                <p><strong>2. Điều khoản và phương thức thanh toán:</strong><br/>
                <em>2.1. Điều khoản thanh toán:</em><br/>
                • Thanh toán lần 1: Thanh toán 50% giá trị đơn hàng trong vòng 07 ngày khi ký hợp đồng.<br/>
                • Thanh toán lần 2: Thanh toán 50% giá trị đơn hàng trong vòng 07 ngày sau khi có biên bản nghiệm thu hoàn thành công việc.<br/>
                <em>2.2. Phương thức &amp; thông tin thanh toán: Chuyển khoản</em><br/>
                [Ngân hàng]: <strong>Ngân Hàng TMCP va PT VN CN Gia Định (BIDV)</strong><br/>
                [Người thụ hưởng]: <strong>Công ty TNHH Ứng dụng kỹ thuật và Giải pháp số TDB</strong><br/>
                [Số tài khoản]: <strong>8601216868</strong></p>

                <p><strong>3. Thời gian thực hiện:</strong><br/>
                3.1. Thời gian triển khai công việc: Dựa theo trao đổi trong hợp đồng.</p>

                <p><strong>4. Chú ý:</strong><br/>
                4.1. [Xác nhận báo giá]: Vui lòng xác nhận báo giá này bằng việc gửi đơn đặt hàng cho chúng tôi qua email.<br/>
                4.2. [Hủy báo giá]: Sau khi ký xác nhận đặt hàng, đối phương tự ý hủy đơn hàng trước thì phải có trách nhiệm bồi thường 100% giá trị đơn hàng như đã thỏa thuận.<br/>
                4.3. [Hiệu lực báo giá]: Báo giá này có hiệu lực trong vòng 15 ngày, được tính từ ngày phát hành.</p>
            """
            self.note = default_template

        view_id = self.env.ref("tdb_sale_custom.view_sale_order_terms_modal", raise_if_not_found=False)
        view_id_val = view_id.id if view_id else False
        return {
            "name": "Chỉnh sửa Điều khoản & Điều kiện",
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(view_id_val, "form")],
            "target": "new",
            "context": {"dialog_size": "large"},
        }

    def action_save_terms_modal(self):
        # Khi ấn Lưu & Áp dụng trên popup, Odoo tự lưu trường note, ta chỉ việc đóng popup
        return {"type": "ir.actions.act_window_close"}

    def action_open_pdf_tab(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/report/pdf/sale.report_saleorder/{self.id}",
            "target": "new",
        }


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    @api.model
    def get_bindings(self, model_name):
        res = super().get_bindings(model_name)
        if model_name == 'sale.order' and isinstance(res, dict) and 'report' in res:
            res['report'] = [
                r for r in res['report']
                if r.get('xml_id') != 'sale.action_report_saleorder'
                and r.get('name') not in ('Quotation / Order', 'Báo giá / Đơn hàng')
            ]
        return res

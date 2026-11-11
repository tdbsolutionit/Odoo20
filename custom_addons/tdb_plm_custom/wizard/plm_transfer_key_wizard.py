# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Wizard Bàn giao & Chuyển giao Key (Force Unlock & Key Transfer):
1. Quản trị viên / Trưởng phòng: Cưỡng chế chuyển giao Key (Force Unlock) khi kỹ sư vắng mặt hoặc đổi nhân sự.
2. Kỹ sư đang giữ Key: Tự nguyện bàn giao Key cho kỹ sư khác hoặc nhả Key tự do khi hoàn tất phần việc.
"""
import logging
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PlmTransferKeyWizard(models.TransientModel):
    _name = "plm.transfer.key.wizard"
    _description = "Wizard bàn giao và chuyển giao quyền giữ Key tài liệu PLM"

    document_id = fields.Many2one(
        "ir.attachment",
        string="Tài liệu",
        required=True,
        readonly=True,
        help="Tài liệu CAD đang thực hiện chuyển giao quyền giữ Key."
    )
    document_name = fields.Char(
        related="document_id.name",
        string="Tên tài liệu",
        readonly=True
    )
    current_key_holder_id = fields.Many2one(
        "res.users",
        string="Kỹ sư đang giữ Key",
        readonly=True,
        help="Kỹ sư hiện tại đang nắm giữ quyền Check-in độc quyền."
    )
    transfer_type = fields.Selection(
        [
            ('to_user', 'Chuyển giao cho kỹ sư khác'),
            ('release', 'Nhả Key tự do (Người check-in tiếp theo sẽ nhận Key)'),
        ],
        string="Hình thức",
        default='to_user',
        required=True
    )
    new_key_holder_id = fields.Many2one(
        "res.users",
        string="Kỹ sư nhận Key mới",
        domain="[('share', '=', False)]",
        help="Chọn kỹ sư sẽ tiếp quản quyền Check-in tài liệu này."
    )
    reason = fields.Text(
        string="Lý do chuyển giao",
        required=True,
        placeholder="Nhập lý do chuyển giao (ví dụ: Kỹ sư phụ trách bận việc, bàn giao bản vẽ cho kỹ sư mới tiếp quản)..."
    )
    release_all_checkouts = fields.Boolean(
        string="Giải phóng toàn bộ phiên Check-out hiện tại",
        default=True,
        help="Tự động hủy các phiên Check-out cũ để tài liệu sẵn sàng cho kỹ sư mới thao tác."
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        doc_id = res.get('document_id') or self.env.context.get('default_document_id')
        if doc_id:
            doc = self.env['ir.attachment'].browse(doc_id)
            is_admin = self.env.user.has_group('plm.group_plm_admin') or self.env.user.has_group('base.group_system')
            is_holder = (doc.key_holder_id == self.env.user)
            if not is_admin and not is_holder:
                raise UserError(_("Bạn không có quyền chuyển giao Key cho tài liệu này."))
            res['current_key_holder_id'] = doc.key_holder_id.id if doc.key_holder_id else False
        return res

    def action_confirm_transfer(self):
        """Xác nhận chuyển giao quyền giữ Key và ghi nhận nhật ký kiểm toán."""
        self.ensure_one()
        doc = self.document_id
        is_admin = self.env.user.has_group('plm.group_plm_admin') or self.env.user.has_group('base.group_system')
        is_holder = (doc.key_holder_id == self.env.user)

        if not is_admin and not is_holder:
            raise UserError(_("Bạn không có quyền chuyển giao Key. Chỉ Quản trị viên PLM hoặc người đang giữ Key mới được phép thực hiện."))

        prev_holder = self.current_key_holder_id or doc.key_holder_id
        prev_name = prev_holder.name if prev_holder else _("Chưa xác định")

        if self.transfer_type == 'to_user':
            if not self.new_key_holder_id:
                raise UserError(_("Vui lòng chọn kỹ sư tiếp nhận Key mới."))
            if prev_holder and prev_holder == self.new_key_holder_id:
                raise UserError(_("Kỹ sư tiếp nhận phải khác với kỹ sư đang giữ Key hiện tại."))

            new_holder = self.new_key_holder_id
            new_name = new_holder.name

            # 1. Cập nhật quyền giữ Key mới trên tài liệu
            doc.sudo().write({
                'key_holder_id': new_holder.id,
                'engineering_writable': False,
            })

            # 2. Giải phóng các phiên Check-out nếu được chọn
            if self.release_all_checkouts:
                self.env['plm.checkout'].sudo().search([('documentid', '=', doc.id)]).unlink()

            # 3. Tạo snapshot dự phòng nếu tài liệu đang có file
            if doc.raw or (doc.file_size and doc.file_size > 0):
                doc._create_document_history_snapshot(
                    description=_("Snapshot lưu trước khi chuyển giao Key cho %s") % new_name,
                    user_id=self.env.user
                )

            # 4. Ghi nhận nhật ký kiểm toán vào Chatter
            audit_msg = Markup(_(
                "<p>"
                "Chuyển giao quyền giữ Key (Force Unlock)<br/>"
                "Người thực hiện: %s<br/>"
                "Kỹ sư từng giữ Key: %s<br/>"
                "Kỹ sư nhận Key mới: %s<br/>"
                "Lý do: %s<br/>"
                "Trạng thái: Đã chuyển giao Key thành công."
                "</p>"
            )) % (self.env.user.name, prev_name, new_name, self.reason.strip())

            doc.message_post(body=audit_msg, message_type='notification')
            _logger.warning(
                f">>> [TDB PLM TRANSFER KEY] {self.env.user.name} đã chuyển giao Key tài liệu "
                f"{doc.name} (ID {doc.id}) từ '{prev_name}' sang '{new_name}'"
            )

        else:
            # Nhả Key tự do
            doc.sudo().write({
                'key_holder_id': False,
                'engineering_writable': False,
            })

            if self.release_all_checkouts:
                self.env['plm.checkout'].sudo().search([('documentid', '=', doc.id)]).unlink()

            audit_msg = Markup(_(
                "<p>"
                "Nhả quyền giữ Key<br/>"
                "Người thực hiện: %s<br/>"
                "Kỹ sư từng giữ Key: %s<br/>"
                "Lý do: %s<br/>"
                "Trạng thái: Đã nhả quyền giữ Key tự do thành công."
                "</p>"
            )) % (self.env.user.name, prev_name, self.reason.strip())

            doc.message_post(body=audit_msg, message_type='notification')
            _logger.warning(
                f">>> [TDB PLM RELEASE KEY] {self.env.user.name} đã nhả Key tài liệu {doc.name} (ID {doc.id})"
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model plm.checkout:
1. Gỡ bỏ ràng buộc unique 1 người để cho phép nhiều kỹ sư cùng Check-out tải file về máy trạm.
2. Tích hợp chuyển giao Key (Force Unlock) có ghi nhận nhật ký kiểm toán vào Chatter.
"""
import logging
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TdbPlmCheckout(models.Model):
    _inherit = "plm.checkout"

    # Ghi đè ràng buộc _documentid gốc của Omnia PLM để cho phép nhiều kỹ sư cùng Check-out (chỉ chặn 1 kỹ sư check-out 2 lần cùng 1 tài liệu)
    _documentid = models.Constraint(
        "unique (documentid, userid)",
        "Tài liệu này đã được bạn Check-out trên máy trạm!"
    )

    def init(self):
        super().init()
        # Cho phép nhiều kỹ sư cùng Check-out để lấy file về máy trạm tham chiếu
        try:
            self.env.cr.execute("""
                ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout_documentid;
                ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout__documentid;
                ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout_documentid_uniq;
                CREATE UNIQUE INDEX IF NOT EXISTS plm_checkout_doc_user_uniq ON plm_checkout (documentid, userid);
            """)
        except Exception as e:
            _logger.info(f"[TDB PLM] Drop old checkout unique constraint: {e}")

    def action_force_unlock(self):
        """Phá khóa cưỡng chế / Chuyển giao Key ngay trên danh sách hoặc form bản ghi plm.checkout."""
        self.ensure_one()
        is_admin = self.env.user.has_group('plm.group_plm_admin') or self.env.user.has_group('base.group_system')
        if not is_admin:
            raise UserError(_("Chỉ Quản trị viên PLM hoặc Trưởng phòng mới có quyền thực hiện Phá khóa cưỡng chế."))

        if self.documentid:
            return self.documentid.action_open_transfer_key_wizard()

        self.with_context(skip_checkin_audit=True).unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Phá khóa thành công"),
                'message': _("Đã giải phóng bản ghi check-out."),
                'type': 'success',
                'sticky': False,
            }
        }

# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model plm.checkout:
Bổ sung tính năng Phá khóa cưỡng chế (Force Unlock) có ghi nhận nhật ký kiểm toán (Audit Log).
"""
import logging
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TdbPlmCheckout(models.Model):
    _inherit = "plm.checkout"

    def action_force_unlock(self):
        """Phá khóa cưỡng chế ngay trên danh sách hoặc form bản ghi plm.checkout."""
        is_admin = self.env.user.has_group('plm.group_plm_admin') or self.env.user.has_group('base.group_system')
        if not is_admin:
            raise UserError(_("Chỉ Quản trị viên PLM hoặc Trưởng phòng mới có quyền thực hiện Phá khóa cưỡng chế."))

        for co in self:
            doc = co.documentid
            prev_user = co.userid.name if co.userid else _("Không rõ")
            prev_host = co.hostname or _("Không rõ")

            co.unlink()

            if doc:
                doc.write({'engineering_writable': False})
                doc.assign_must_update_flag()
                audit_msg = Markup(_(
                    "<p><strong>🚨 CƯỠNG CHẾ MỞ KHÓA (FORCE UNLOCK)</strong></p>"
                    "<ul>"
                    "<li>Người thực hiện: <b>%s</b></li>"
                    "<li>Kỹ sư từng giữ khóa: <b>%s</b> (Máy trạm: <b>%s</b>)</li>"
                    "<li>Trạng thái tài liệu: Đã giải phóng khóa cưỡng chế thành công.</li>"
                    "</ul>"
                )) % (self.env.user.name, prev_user, prev_host)
                doc.message_post(body=audit_msg, message_type='notification')
                _logger.warning(f">>> [TDB PLM FORCE UNLOCK] {self.env.user.name} đã phá khóa bản vẽ {doc.name} (Doc ID {doc.id})")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Phá khóa thành công"),
                'message': _("Đã giải phóng khóa cưỡng chế thành công."),
                'type': 'success',
                'sticky': False,
            }
        }


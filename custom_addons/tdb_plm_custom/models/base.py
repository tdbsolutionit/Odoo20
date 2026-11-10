# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Chốt chặn tầng ORM Cốt lõi (base / models.AbstractModel):
Bắt toàn bộ thao tác ghi (create, write, unlink) mang cờ định danh CAD Add-in:
context={'odooPLM': True}

Lợi ích tuyệt đối:
1. SolidWorks CAD Add-in luôn gắn cờ odooPLM=True trên mọi request.
2. Web Browser của Admin và người dùng ERP thông thường không bao giờ có cờ này -> Hoàn toàn không bị ảnh hưởng.
3. Chặn đứng 100% mọi hành vi sửa, lưu, tạo mới linh kiện/bản vẽ/BOM khi token 180 ngày hết hạn hoặc bị thu hồi.
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BaseCadSecurity(models.AbstractModel):
    _inherit = 'base'

    def _check_cad_active_token(self):
        """Kiểm tra token cho mọi thao tác từ CAD Client (SolidWorks / Inventor qua RPC).
        Bỏ qua hoàn toàn đối với các thao tác từ Web Browser của Admin / Kỹ sư.
        """
        # 1. Bỏ qua nếu có cờ định danh thao tác Web
        if self.env.context.get('is_web_operation'):
            return

        # 2. Bỏ qua hoàn toàn nếu request xuất phát từ trình duyệt Web (/web, /odoo)
        try:
            from odoo.http import request
            if request and hasattr(request, 'httprequest'):
                path = getattr(request.httprequest, 'path', '') or ''
                if path.startswith('/web') or path.startswith('/odoo'):
                    return
        except Exception:
            pass

        # 3. Chỉ kiểm tra khi có cờ CAD Client (odooPLM=True)
        if not self.env.context.get('odooPLM'):
            return

        if 'plm.desktop.token' not in self.env.registry:
            return

        token_model = self.env['plm.desktop.token'].sudo()
        tokens = token_model.search([('user_id', '=', self.env.uid)], order='id desc')
        if tokens:
            if any(t.is_revoked for t in tokens):
                _logger.warning(f">>> [TDB PLM ORM BASE] Chặn thao tác CAD bị thu hồi: User ID {self.env.uid}")
                raise UserError(_("Thiết bị CAD đã bị Quản trị viên thu hồi quyền truy cập. Vui lòng liên hệ Quản trị viên."))

            now = fields.Datetime.now()
            active = [t for t in tokens if (not t.is_revoked) and t.expires_at and (t.expires_at > now)]
            if not active:
                _logger.warning(f">>> [TDB PLM ORM BASE] Chặn thao tác CAD hết hạn 180 ngày: User ID {self.env.uid}")
                raise UserError(_("Phiên làm việc CAD 180 ngày đã HẾT HẠN. Vui lòng bấm 'Execute New Login' từ SolidWorks để gia hạn."))
        else:
            _logger.warning(f">>> [TDB PLM ORM BASE] Chặn thao tác CAD chưa có token: User ID {self.env.uid}")
            raise UserError(_("Phiên làm việc CAD chưa được kích hoạt hoặc đã hết hạn. Vui lòng bấm 'Execute New Login' từ SolidWorks."))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_cad_active_token()
        return super().create(vals_list)

    def write(self, vals):
        self._check_cad_active_token()
        return super().write(vals)

    def unlink(self):
        self._check_cad_active_token()
        return super().unlink()


# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model ir.attachment cho phân hệ OdooPLM.
Tuân thủ Layer 2: Quản lý business logic cốt lõi.
Bảo vệ tầng ORM: Chặn đứng lưu/sửa bản vẽ, check-in, check-out khi token 180 ngày hết hạn hoặc bị thu hồi.
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _check_cad_access_token(self):
        """Kiểm tra token thiết bị CAD tại tầng ORM:
        Chặn tuyệt đối mọi thao tác lưu bản vẽ, check-in, check-out nếu token bị thu hồi hoặc hết hạn.
        """
        if 'plm.desktop.token' in self.env.registry:
            token_model = self.env['plm.desktop.token'].sudo()
            tokens = token_model.search([('user_id', '=', self.env.uid)], order='id desc')
            if tokens:
                if any(t.is_revoked for t in tokens):
                    raise UserError(_("Thiết bị CAD đã bị Quản trị viên thu hồi quyền truy cập. Vui lòng liên hệ Quản trị viên."))
                now = fields.Datetime.now()
                active = [t for t in tokens if (not t.is_revoked) and t.expires_at and (t.expires_at > now)]
                if not active:
                    raise UserError(_("Phiên làm việc CAD 180 ngày đã hết hạn. Vui lòng bấm 'Execute New Login' từ SolidWorks để tiếp tục."))

    @api.model
    def SaveOrUpdate(self, documents, default=None):
        """Chặn lưu/cập nhật tài liệu CAD khi token hết hạn."""
        self._check_cad_access_token()
        return super().SaveOrUpdate(documents, default=default)

    @api.model
    def CheckSaveUpdate(self, documents, default=None):
        """Chặn kiểm tra lưu tài liệu CAD khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckSaveUpdate(documents, default=default)

    def CheckIn(self, attrs):
        """Chặn Check-in đơn lẻ khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckIn(attrs)

    def CheckInRecursive(self, request, default=None):
        """Chặn Check-in đệ quy khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckInRecursive(request, default=default)

    def checkout(self, hostName, hostPws, showError=True, user_id=False):
        """Chặn Check-out đơn lẻ khi token hết hạn."""
        self._check_cad_access_token()
        return super().checkout(hostName, hostPws, showError=showError, user_id=user_id)

    def CheckOutRecursive(self, structure, pws_path="", hostname="", force=False):
        """Chặn Check-out đệ quy cây lắp ráp khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckOutRecursive(structure, pws_path=pws_path, hostname=hostname, force=force)

    def saveStructure(self, arguments):
        """Chặn lưu cấu trúc lắp ráp CAD khi token hết hạn."""
        self._check_cad_access_token()
        return super().saveStructure(arguments)

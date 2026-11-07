# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model product.product cho phân hệ Engineering Parts (PLM).
Tuân thủ Layer 2: Quản lý schema dữ liệu và business logic cốt lõi.
Bảo vệ tầng ORM: Chặn đứng lưu/sửa linh kiện khi token 180 ngày hết hạn hoặc bị thu hồi.
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """
    Kế thừa product.product để quản lý thông tin linh kiện kỹ thuật (Engineering Parts).
    Chuẩn hóa nhãn chuỗi gốc tiếng Anh (Revision, CAD Raw Material, CAD Surface Finishing).
    Kiểm soát quyền truy cập thực thi theo Access Token 180 ngày từ máy trạm CAD.
    """
    _inherit = "product.product"

    engineering_revision = fields.Integer(string="Revision")
    engineering_material = fields.Char(string="CAD Raw Material")
    engineering_surface = fields.Char(string="CAD Surface Finishing")

    def _check_cad_access_token(self):
        """Kiểm tra token thiết bị CAD tại tầng ORM:
        Chặn tuyệt đối mọi thao tác tạo/sửa linh kiện nếu token bị thu hồi hoặc hết hạn 180 ngày.
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
    def SaveOrUpdate(self, vals):
        """Chặn đứng lưu/sửa linh kiện từ CAD Client nếu token hết hạn hoặc bị thu hồi."""
        self._check_cad_access_token()
        return super().SaveOrUpdate(vals)

    @api.model
    def ConvertToPlmProduct(self, attributes_list=[]):
        """Chặn chuyển đổi linh kiện PLM nếu token hết hạn hoặc bị thu hồi."""
        self._check_cad_access_token()
        return super().ConvertToPlmProduct(attributes_list)

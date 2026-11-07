# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Middleware tầng HTTP (ir.http):
Kiểm soát toàn bộ request liên quan đến phân hệ PLM / CAD Desktop Add-in (SolidWorks).
Tuyệt đối không gây ảnh hưởng đến phiên làm việc Web Browser của Quản trị viên.
"""
import logging
from odoo import models
from odoo.http import request
from werkzeug.exceptions import Unauthorized, Forbidden

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint=''):
        super()._authenticate(endpoint)

        # 1. Chỉ áp dụng kiểm tra cho các endpoint của CAD Add-in (/plm_document_upload/*)
        # Các request của Web Browser (/web, /odoo, backend) hoàn toàn bỏ qua, không bị ảnh hưởng.
        if not hasattr(request, 'httprequest') or not request.httprequest:
            return

        path = request.httprequest.path or ''
        if not path.startswith('/plm_document_upload/'):
            return

        # Đường dẫn đăng nhập /plm_document_upload/login được xử lý riêng bởi controller để cấp token
        if path == '/plm_document_upload/login':
            return

        # 2. Kiểm tra token cho các thao tác CAD (upload, download, isalive, etc.)
        if 'plm.desktop.token' not in request.env.registry:
            return

        token_model = request.env['plm.desktop.token'].sudo()
        session_id = getattr(request.session, 'sid', None)
        uid = getattr(request.session, 'uid', None)

        if not session_id or not uid:
            raise Unauthorized("CAD Session is invalid. Please log in again from SolidWorks.")

        token = token_model.search([
            ('user_id', '=', uid),
            ('session_id', '=', session_id),
        ], limit=1)

        if not token:
            # Fallback theo user nếu session đã bị đổi
            token = token_model.search([
                ('user_id', '=', uid),
            ], order='id desc', limit=1)

        if token:
            if token.is_revoked:
                _logger.warning(f">>> [TDB PLM Middleware] Chặn CAD đã bị thu hồi: Máy '{token.machine_name}'")
                raise Forbidden("CAD Workstation access has been REVOKED by Administrator. Please contact Admin to restore access.")

            from odoo import fields
            now = fields.Datetime.now()
            if token.expires_at and token.expires_at <= now:
                _logger.warning(f">>> [TDB PLM Middleware] Chặn CAD đã hết hạn: Máy '{token.machine_name}'")
                raise Unauthorized("CAD 180-day Session has EXPIRED. Please use 'Execute New Login' from SolidWorks to renew.")

            token.update_last_used()
        else:
            raise Unauthorized("CAD workstation token not found. Please log in again from SolidWorks.")

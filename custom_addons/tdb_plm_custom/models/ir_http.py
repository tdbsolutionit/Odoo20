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

        # 0. Tự động dọn dẹp triệt để ghost menu trên Top Bar khỏi bảng ir_ui_menu và thu hồi quyền admin của kỹ sư
        if not getattr(cls, '_top_menu_cleaned', False) and hasattr(request, 'env') and request.env and request.env.cr:
            cls._top_menu_cleaned = True
            try:
                request.env.cr.execute("""
                    DELETE FROM ir_ui_menu_group_rel
                    WHERE menu_id IN (
                        SELECT id FROM ir_ui_menu
                        WHERE parent_id = (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu')
                          AND (name ILIKE '%desktop%access%token%' OR name ILIKE '%quản lý thiết bị%')
                    );
                    DELETE FROM ir_ui_menu
                    WHERE parent_id = (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu')
                      AND (name ILIKE '%desktop%access%token%' OR name ILIKE '%quản lý thiết bị%');

                    -- Thu hồi nhóm Quản trị Administrator (base.group_system) khỏi mọi tài khoản Kỹ sư
                    DELETE FROM res_groups_users_rel
                    WHERE gid IN (
                        SELECT res_id FROM ir_model_data
                        WHERE module = 'base' AND name IN ('group_system', 'group_erp_manager')
                    )
                    AND uid NOT IN (
                        SELECT res_id FROM ir_model_data
                        WHERE module = 'base' AND name = 'user_admin'
                    )
                    AND uid != 2
                    AND uid IN (
                        SELECT id FROM res_users WHERE login != 'admin'
                    );
                """)
                _logger.info(">>> [TDB PLM] Đã dọn dẹp triệt để ghost menu Top Bar và thu hồi quyền Admin của Kỹ sư.")
            except Exception as e:
                _logger.debug(f"[TDB PLM] Dọn dẹp menu trong ir.http: {e}")

        # 1. Chỉ áp dụng kiểm tra cho các endpoint của CAD Add-in (/plm_document_upload/* và /plm/*)
        # Các request của Web Browser (/web, /odoo, backend) hoàn toàn bỏ qua, không bị ảnh hưởng.
        if not hasattr(request, 'httprequest') or not request.httprequest:
            return

        path = request.httprequest.path or ''
        if not (path.startswith('/plm_document_upload/') or path.startswith('/plm/')):
            return

        # Các endpoint công khai hoặc handshake (login, isalive) không bị chặn tại middleware này
        if path in ('/plm_document_upload/login', '/plm_document_upload/isalive'):
            return

        # 2. Kiểm tra token cho các thao tác CAD (upload, download, v.v.)
        if 'plm.desktop.token' not in request.env.registry:
            return

        token_model = request.env['plm.desktop.token'].sudo()
        session_id = getattr(request.session, 'sid', None)
        uid = getattr(request.session, 'uid', None)

        if not session_id or not uid:
            raise Forbidden("CAD Session is invalid. Please log in again from SolidWorks.")

        tokens = token_model.search([
            ('user_id', '=', uid),
        ], order='id desc')

        if tokens:
            if any(t.is_revoked for t in tokens):
                _logger.warning(f">>> [TDB PLM Middleware] Chặn CAD đã bị thu hồi: User ID {uid}")
                raise Forbidden("CAD Workstation access has been REVOKED by Administrator. Please contact Admin to restore access.")

            from odoo import fields
            now = fields.Datetime.now()
            active_tokens = [t for t in tokens if (not t.is_revoked) and t.expires_at and (t.expires_at > now)]
            if not active_tokens:
                _logger.warning(f">>> [TDB PLM Middleware] Chặn CAD đã hết hạn: User ID {uid}")
                raise Forbidden("CAD 180-day Session has EXPIRED. Please use 'Execute New Login' from SolidWorks to renew.")

            tokens[0].update_last_used()
        else:
            raise Forbidden("CAD workstation token not found. Please log in again from SolidWorks.")

# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Layer bảo vệ xác thực: Tự động ngắt kết nối và trả về 401/403
khi Client gửi request từ một máy trạm CAD hoặc phiên Desktop Token đã bị thu hồi hoặc quá hạn 180 ngày.
"""
import logging
from odoo import models
from odoo.http import request
from werkzeug.exceptions import Unauthorized

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        super()._authenticate(endpoint)

        # Nếu request có session hợp lệ và đã đăng nhập tài khoản
        if hasattr(request, 'session') and request.session and request.session.uid:
            try:
                # Kiểm tra an toàn xem model và bảng dữ liệu đã tồn tại trong database chưa (tránh crash khi chưa upgrade DB)
                if 'plm.desktop.token' not in request.env.registry:
                    return

                with request.env.cr.savepoint():
                    request.env.cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                    row = request.env.cr.fetchone()
                    if not row or not row[0]:
                        return

                    client_ip = request.httprequest.headers.get('X-Forwarded-For') or request.httprequest.remote_addr or '127.0.0.1'
                    if client_ip and ',' in client_ip:
                        client_ip = client_ip.split(',')[0].strip()

                    token_model = request.env['plm.desktop.token'].sudo()

                    # Tìm token tương ứng với session_id hoặc IP của user CAD
                    token = token_model.search([
                        ('user_id', '=', request.session.uid),
                        '|',
                        ('session_id', '=', request.session.sid),
                        ('client_ip', '=', client_ip),
                    ], limit=1)

                    if token:
                        if token.is_revoked or not token.is_active:
                            _logger.warning(
                                f">>> [TDB PLM] Chặn phiên CAD đã bị thu hồi/quá hạn: "
                                f"User ID {request.session.uid}, Máy '{token.machine_name}', IP {client_ip}, Session {str(request.session.sid)[:10]}..."
                            )
                            request.session.logout(keep_db=True)
                            raise Unauthorized("CAD workstation access has been revoked or expired by Administrator.")
                        else:
                            token.update_last_used()
            except Unauthorized:
                raise
            except Exception as e:
                # Tránh làm gián đoạn các request thông thường của hệ thống
                _logger.debug(f"[TDB PLM] Kiểm tra desktop token: {e}")

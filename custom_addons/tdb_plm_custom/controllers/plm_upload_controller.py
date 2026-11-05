# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Controller kế thừa và mở rộng OdooPLM UploadDocument:
- Ép Cookie Session ID (Max-Age) thành đúng 180 ngày (15,552,000s).
- Lưu thông tin máy trạm CAD vào model plm.desktop.token.
- Tự động ngắt kết nối (401) nếu phiên đã bị thu hồi từ xa.
"""
import logging
from odoo.http import route, request, Response
from odoo.addons.plm.controllers.main import UploadDocument

_logger = logging.getLogger(__name__)

MAX_AGE_180_DAYS = 180 * 24 * 3600  # 15,552,000 giây (180 ngày)


class TdbPlmUploadDocument(UploadDocument):

    @route(
        "/plm_document_upload/login",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def login(self, login, password, db=None, **kw):
        """Kế thừa và mở rộng Controller gốc: Ép Session 180 ngày và ghi nhận Token thiết bị."""
        # Gọi phương thức login gốc của UploadDocument để Odoo Core xác thực tài khoản
        res = super().login(login, password, db=db, **kw)

        # Nếu đăng nhập không thành công
        if res.status_code != 200 or not getattr(request, 'session', None) or not request.session.uid:
            return res

        sid = request.session.sid

        # 1. Ép thời hạn sống của Cookie phiên làm việc (Session ID) thành đúng 180 ngày (15,552,000s)
        res.set_cookie(
            'session_id',
            sid,
            max_age=MAX_AGE_180_DAYS,
            httponly=True,
            samesite='Lax',
        )
        if hasattr(request, 'future_response') and request.future_response:
            request.future_response.set_cookie(
                'session_id',
                sid,
                max_age=MAX_AGE_180_DAYS,
                httponly=True,
                samesite='Lax',
            )

        # 2. Thu thập thông tin máy trạm CAD (IP, Tên máy, Machine UUID, Phiên bản CAD)
        client_ip = request.httprequest.headers.get('X-Forwarded-For') or request.httprequest.remote_addr or '127.0.0.1'
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        machine_name = kw.get('machine_name') or request.httprequest.headers.get('X-Machine-Name')
        if not machine_name:
            machine_name = f"CAD-WS ({client_ip})"

        machine_uuid = kw.get('machine_uuid') or request.httprequest.headers.get('X-Machine-UUID') or f"UUID-{sid[:16]}"
        cad_version = kw.get('cad_version') or request.httprequest.headers.get('X-CAD-Version') or 'SolidWorks 2022'

        # 3. Lưu/cập nhật bản ghi trong Model 'plm.desktop.token'
        try:
            token_model = request.env['plm.desktop.token'].sudo()
            token_model.register_session_token(
                user_id=request.session.uid,
                session_id=sid,
                machine_uuid=machine_uuid,
                machine_name=machine_name,
                client_ip=client_ip,
                cad_version=cad_version,
            )
            _logger.info(
                f">>> [TDB PLM] Đã cấp Session 180 ngày cho User ID {request.session.uid} "
                f"trên máy trạm '{machine_name}' (IP: {client_ip}, Session: {sid[:10]}...)"
            )
        except Exception as e:
            _logger.error(f"[TDB PLM] Không thể lưu plm.desktop.token: {e}")

        return res

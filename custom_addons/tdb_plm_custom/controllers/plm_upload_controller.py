# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Controller kế thừa và mở rộng OdooPLM UploadDocument:
- Ép Cookie Session ID (Max-Age) thành đúng 180 ngày (15,552,000s).
- Lưu thông tin máy trạm CAD vào model plm.desktop.token.
- Tự động chặn và từ chối kết nối (403/401) nếu máy trạm CAD đã bị thu hồi quyền từ xa.
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
        """Kế thừa và mở rộng Controller gốc: Kiểm tra thu hồi, ép Session 180 ngày và ghi nhận Token thiết bị."""
        # 1. Thu thập thông tin máy trạm CAD (IP, Tên máy, UUID, Phiên bản)
        client_ip = request.httprequest.headers.get('X-Forwarded-For') or request.httprequest.remote_addr or '127.0.0.1'
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        machine_name = kw.get('hostname') or kw.get('host_name') or kw.get('machine_name') or request.httprequest.headers.get('X-Machine-Name')
        if not machine_name:
            machine_name = f"CAD WS ({client_ip})"

        machine_uuid = kw.get('machine_uuid') or request.httprequest.headers.get('X-Machine-UUID') or f"WS_{machine_name}"
        cad_version = kw.get('cad_version') or request.httprequest.headers.get('X-CAD-Version') or 'SolidWorks 2022'

        # 2. Kiểm tra xem thiết bị CAD này hoặc User này đã bị Quản trị viên THU HỒI quyền chưa
        try:
            if 'plm.desktop.token' in request.env.registry:
                token_model = request.env['plm.desktop.token'].sudo()
                tokens = token_model.search([('user_id.login', '=', login)], order='id desc')
                if tokens and any(t.is_revoked for t in tokens):
                    _logger.warning(
                        f">>> [TDB PLM] CHẶN ĐĂNG NHẬP: Máy trạm '{machine_name}' (IP: {client_ip}) "
                        f"của tài khoản '{login}' ĐÃ BỊ THU HỒI quyền truy cập bởi Quản trị viên."
                    )
                    return Response(
                        response="CAD Workstation access has been REVOKED by Administrator. Please contact Admin to restore access.",
                        status=403,
                    )
        except Exception as e:
            _logger.debug(f"[TDB PLM] Lỗi kiểm tra revoked token trước login: {e}")

        # 3. Gọi phương thức login gốc của UploadDocument để Odoo Core xác thực tài khoản
        res = super().login(login, password, db=db)

        # Nếu đăng nhập không thành công
        if res.status_code != 200 or not getattr(request, 'session', None) or not request.session.uid:
            return res

        sid = request.session.sid

        # 4. Lưu/cập nhật bản ghi trong Model 'plm.desktop.token'
        try:
            token_model = request.env['plm.desktop.token'].sudo()
            token = token_model.register_session_token(
                user_id=request.session.uid,
                session_id=sid,
                machine_uuid=machine_uuid,
                machine_name=machine_name,
                client_ip=client_ip,
                cad_version=cad_version,
            )

            if not token:
                # Nếu thiết bị đang bị thu hồi bởi Quản trị viên
                request.session.clear()
                return Response(
                    response="CAD Workstation access has been REVOKED by Administrator. Please contact Admin to restore access.",
                    status=403,
                )

            # 5. Ép thời hạn sống của Cookie phiên làm việc (Session ID) thành đúng 180 ngày (15,552,000s)
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

            _logger.info(
                f">>> [TDB PLM] Đã cấp Session 180 ngày cho User ID {request.session.uid} "
                f"trên máy trạm '{machine_name}' (IP: {client_ip}, Session: {sid[:10]}...)"
            )
        except Exception as e:
            _logger.error(f"[TDB PLM] Không thể lưu plm.desktop.token: {e}")

        return res

    @route(
        "/plm_document_upload/upload",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def upload(self, mod_file=None, doc_id=False, filename="", **kw):
        """Kế thừa Upload: Kiểm tra thu hồi/hết hạn và cập nhật tên máy thực tế nếu SolidWorks truyền hostname."""
        if getattr(request, 'session', None) and request.session.uid:
            try:
                from odoo import fields
                token_model = request.env['plm.desktop.token'].sudo()
                tokens = token_model.search([('user_id', '=', request.session.uid)], order='id desc')

                if tokens:
                    if any(t.is_revoked for t in tokens):
                        return Response("CAD Workstation access has been REVOKED by Administrator.", status=403)

                    now = fields.Datetime.now()
                    active_tokens = [t for t in tokens if (not t.is_revoked) and t.expires_at and (t.expires_at > now) and t.session_id]
                    if not active_tokens:
                        return Response("CAD 180-day Session has EXPIRED. Please use 'Execute New Login' from SolidWorks to renew.", status=401)

                    hostname = kw.get('hostname')
                    client_ip = request.httprequest.headers.get('X-Forwarded-For') or request.httprequest.remote_addr or '127.0.0.1'
                    if client_ip and ',' in client_ip:
                        client_ip = client_ip.split(',')[0].strip()
                    if hostname and (tokens[0].machine_name.startswith("CAD-WS") or tokens[0].machine_name.startswith("CAD WS")):
                        tokens[0].write({'machine_name': f"{hostname} ({client_ip})"})
            except Exception as e:
                _logger.debug(f"[TDB PLM] Không thể kiểm tra token/cập nhật tên máy trong upload: {e}")

        return super().upload(mod_file=mod_file, doc_id=doc_id, filename=filename, **kw)

# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Layer 3: Tầng Controller điều phối & Khắc phục tương thích RPC cho OdooPLM Client (SolidWorks / Inventor)
======================================================================================================
Bối cảnh kỹ thuật:
- Trên Odoo 20, dịch vụ 'db' đã bị loại bỏ khỏi hàm dispatch_rpc (chỉ còn 'common' và 'object').
- Khi CAD Client (SolidWorks OdooPLM) kết nối, client thực hiện gọi RPC service 'db', method 'list'
  để lấy danh sách Database hiển thị lên combobox đăng nhập.
- Controller này cung cấp bản vá (patch) hàm dispatch_rpc nhằm phục hồi khả năng phản hồi danh mục database cho CAD Client,
  đồng thời chặn các thao tác PLM qua XML-RPC nếu thiết bị CAD của user đã bị Admin thu hồi quyền hoặc chưa đăng nhập lại.
"""
import sys
import logging
import odoo
from odoo.http import router

_logger = logging.getLogger(__name__)

# Lưu lại hàm dispatch_rpc nguyên bản của Odoo
_original_dispatch_rpc = getattr(router, '_tdb_original_dispatch_rpc', None)
if not _original_dispatch_rpc:
    _original_dispatch_rpc = router.dispatch_rpc
    router._tdb_original_dispatch_rpc = _original_dispatch_rpc

CAD_OPERATIONAL_MODELS = (
    'product.product',
    'product.template',
    'ir.attachment',
    'ir.attachment.relation',
    'mrp.bom',
    'mrp.bom.line',
    'plm.checkout',
    'plm.backup.document',
    'plm.cad.open',
    'plm.temporary',
    'plm.client',
    'plm.component',
    'plm.description',
    'plm.material',
    'plm.finishing',
    'plm.treatment',
)


HANDSHAKE_METHODS = (
    'getServerTime',
    'getUserSign',
    'getMacros',
    'getCustomProcedure',
)


def _cad_dispatch_rpc(service_name, method, params):
    """Điều phối RPC tùy biến:
    1. Phục hồi service 'db' cho các ứng dụng CAD Client (SolidWorks/Inventor).
    2. Chặn các thao tác PLM qua XML-RPC (linh kiện product.product, bản vẽ, bom, checkin, checkout)
       nếu thiết bị CAD của user đã bị Admin thu hồi quyền hoặc phiên đã bị hủy và yêu cầu đăng nhập lại.
    """
    if service_name == 'db':
        if method in ('list', 'list_db'):
            try:
                from odoo.http import db_list
                dbs = db_list()
                if dbs:
                    return dbs
            except Exception:
                pass
            # Fallback nếu db_list bị chặn hoặc rỗng: lấy từ cấu hình hoặc mặc định
            cfg_db = odoo.tools.config.get('db_name')
            if cfg_db:
                if isinstance(cfg_db, (list, tuple, set)):
                    return [str(d).strip() for d in cfg_db if d]
                elif isinstance(cfg_db, str):
                    return [d.strip(" '\"[]()") for d in cfg_db.split(',') if d.strip(" '\"[]()")]
            return ['odoo20_dev']
        elif method == 'db_exist':
            target_db = params[0] if params else ''
            cfg_db = odoo.tools.config.get('db_name') or 'odoo20'
            return target_db in (cfg_db, 'odoo20')
        elif method == 'server_version':
            return odoo.release.version
        elif method == 'server_environment':
            return 'production'

    elif service_name == 'common' and method == 'authenticate':
        # Bắt sự kiện đăng nhập lại từ hộp thoại CAD (Execute New Login / Use new login)
        db, login, password = params[:3]
        from odoo.modules.registry import Registry
        from odoo import api, fields
        from datetime import timedelta

        client_ip = None
        try:
            from odoo.http import request
            if request and hasattr(request, 'httprequest'):
                client_ip = request.httprequest.headers.get('X-Forwarded-For') or request.httprequest.remote_addr
                if client_ip and ',' in client_ip:
                    client_ip = client_ip.split(',')[0].strip()
        except Exception:
            pass

        # 1. Kiểm tra trước: Nếu thiết bị đang bị Admin THU HỒI -> CHẶN ĐỨNG KHÔNG CHO ĐĂNG NHẬP
        with Registry(db).cursor() as cr:
            env = api.Environment(cr, api.SUPERUSER_ID, {})
            if 'plm.desktop.token' in env.registry:
                cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                row = cr.fetchone()
                if row and row[0]:
                    user = env['res.users'].search([('login', '=', login)], limit=1)
                    if user:
                        domain = [('user_id', '=', user.id)]
                        if client_ip:
                            domain.append(('client_ip', '=', client_ip))
                        tokens = env['plm.desktop.token'].search(domain, order='id desc')
                        if not tokens:
                            tokens = env['plm.desktop.token'].search([('user_id', '=', user.id)], order='id desc')
                        if tokens and any(t.is_revoked for t in tokens):
                            _logger.warning(
                                f">>> [TDB PLM] TỪ CHỐI ĐĂNG NHẬP: Thiết bị của user '{login}' (IP: {client_ip}) "
                                f"đang ở trạng thái BỊ THU HỒI bởi Quản trị viên."
                            )
                            raise odoo.exceptions.AccessDenied("CAD Workstation access has been REVOKED by Administrator. Please contact Admin to restore access.")

        # 2. Cho phép Odoo xác thực tài khoản / mật khẩu
        uid = _original_dispatch_rpc(service_name, method, params)

        # 3. Nếu đăng nhập thành công qua hộp thoại CAD: MỞ KHÓA VÀ GIA HẠN 180 NGÀY CHO THIẾT BỊ
        if uid:
            with Registry(db).cursor() as cr:
                env = api.Environment(cr, api.SUPERUSER_ID, {})
                if 'plm.desktop.token' in env.registry:
                    cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                    row = cr.fetchone()
                    if row and row[0]:
                        domain = [('user_id', '=', int(uid))]
                        if client_ip:
                            domain.append(('client_ip', '=', client_ip))
                        tokens = env['plm.desktop.token'].search(domain, order='id desc')
                        if not tokens:
                            tokens = env['plm.desktop.token'].search([('user_id', '=', int(uid))], order='id desc')
                        if tokens:
                            now = fields.Datetime.now()
                            tokens[0].write({
                                'expires_at': now + timedelta(days=180),
                                'is_revoked': False,
                                'last_used_date': now,
                            })
                            cr.commit()
                            _logger.info(
                                f">>> [TDB PLM] Kỹ sư '{login}' (UID {uid}) đã đăng nhập lại qua Execute New Login: "
                                f"Đã gia hạn 180 ngày cho thiết bị '{tokens[0].machine_name}'."
                            )
        return uid

    elif service_name == 'object':
        try:
            db, uid, passwd, model, method_ = params[:5]
            # Bỏ qua không chặn các hàm handshake/đăng nhập của client CAD (getServerTime, getUserSign, res.users...)
            is_handshake = (method_ in HANDSHAKE_METHODS) or (model in ('plm.desktop.token', 'plm.access'))
            is_cad_operational = (model in CAD_OPERATIONAL_MODELS) or str(model).startswith('plm.')

            if is_cad_operational and not is_handshake:
                from odoo.modules.registry import Registry
                from odoo import api
                with Registry(db).cursor() as cr:
                    env = api.Environment(cr, api.SUPERUSER_ID, {})
                    if 'plm.desktop.token' in env.registry:
                        cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                        row = cr.fetchone()
                        if row and row[0]:
                            client_ip = None
                            try:
                                from odoo.http import request
                                if request and hasattr(request, 'httprequest'):
                                    client_ip = request.httprequest.headers.get('X-Forwarded-For') or request.httprequest.remote_addr
                                    if client_ip and ',' in client_ip:
                                        client_ip = client_ip.split(',')[0].strip()
                            except Exception:
                                pass

                            domain = [('user_id', '=', int(uid))]
                            if client_ip:
                                domain.append(('client_ip', '=', client_ip))

                            tokens = env['plm.desktop.token'].search(domain, order='id desc')
                            if not tokens:
                                tokens = env['plm.desktop.token'].search([('user_id', '=', int(uid))], order='id desc')

                            if tokens:
                                # 1. Nếu thiết bị đã bị Thu hồi: Chặn tuyệt đối mọi thao tác can thiệp dữ liệu
                                revoked_tokens = tokens.filtered(lambda t: t.is_revoked)
                                if revoked_tokens:
                                    _logger.warning(
                                        f">>> [TDB PLM] CHẶN RPC: Thiết bị '{revoked_tokens[0].machine_name}' "
                                        f"của User ID {uid} ĐÃ BỊ THU HỒI. Từ chối thực thi {model}.{method_}"
                                    )
                                    raise odoo.exceptions.AccessDenied("CAD Workstation access has been REVOKED by Administrator. Please contact Admin to restore access.")

                                token = tokens[0]
                                from odoo import fields
                                now = fields.Datetime.now()

                                # 2. Với các thao tác nghiệp vụ CAD (sửa linh kiện, bản vẽ, BOM, checkout): Bắt buộc còn hạn và có session
                                if token.expires_at and token.expires_at <= now:
                                    _logger.warning(
                                        f">>> [TDB PLM] CHẶN RPC: Thiết bị '{token.machine_name}' "
                                        f"của User ID {uid} ĐÃ HẾT HẠN 180 NGÀY ({token.expires_at}). Từ chối thực thi {model}.{method_}"
                                    )
                                    raise odoo.exceptions.AccessDenied("CAD 180-day Session has EXPIRED. Please log in again from SolidWorks to renew.")
                                elif not token.session_id:
                                    _logger.warning(
                                        f">>> [TDB PLM] YÊU CẦU ĐĂNG NHẬP LẠI: Thiết bị '{token.machine_name}' "
                                        f"của User ID {uid} chưa có phiên đăng nhập hợp lệ. Từ chối thực thi {model}.{method_}"
                                    )
                                    raise odoo.exceptions.AccessDenied("Session expired. Please log in to OdooPLM again from SolidWorks.")
        except odoo.exceptions.AccessDenied:
            raise
        except Exception as e:
            _logger.error(f"[TDB PLM] Lỗi kiểm tra token trong RPC dispatch: {e}")

    return _original_dispatch_rpc(service_name, method, params)


# 1. Áp dụng bản vá vào router.dispatch_rpc
router.dispatch_rpc = _cad_dispatch_rpc

# 2. Đồng bộ bản vá vào các controller rpc nếu đã nạp trước đó trong sys.modules
for mod_path in (
    'odoo.addons.rpc.controllers.xmlrpc',
    'odoo.addons.rpc.controllers.jsonrpc',
    'addons.rpc.controllers.xmlrpc',
    'addons.rpc.controllers.jsonrpc',
):
    if mod_path in sys.modules:
        setattr(sys.modules[mod_path], 'dispatch_rpc', _cad_dispatch_rpc)

_logger.info(">>> [TDB PLM] Đã kích hoạt bản vá tương thích CAD Client XML-RPC / JSON-RPC (service: db + Access Revoke Gate) cho Odoo 20.")

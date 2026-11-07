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
        # Xác thực XML-RPC cho CAD Client:
        # 1. Chặn đứng nếu thiết bị đang bị Admin THU HỒI quyền.
        # 2. KHÔNG chặn token hết hạn tại đây để cho phép kỹ sư dùng 'Execute New Login' xác thực và gia hạn lại.
        # 3. KHÔNG tự ý gia hạn 180 ngày tại đây để ngăn 'Use Current Session' tự động reset hạn.
        db, login, password = params[:3]
        from odoo.modules.registry import Registry
        from odoo import api

        # Kiểm tra trước: Nếu tài khoản/thiết bị đang bị Admin THU HỒI -> CHẶN ĐỨNG
        with Registry(db).cursor() as cr:
            env = api.Environment(cr, api.SUPERUSER_ID, {})
            if 'plm.desktop.token' in env.registry:
                cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                row = cr.fetchone()
                if row and row[0]:
                    user = env['res.users'].search([('login', '=', login)], limit=1)
                    if user:
                        tokens = env['plm.desktop.token'].search([('user_id', '=', user.id)], order='id desc')
                        if tokens and any(t.is_revoked for t in tokens):
                            _logger.warning(
                                f">>> [TDB PLM] TỪ CHỐI XML-RPC AUTHENTICATE: Thiết bị của user '{login}' "
                                f"đang ở trạng thái BỊ THU HỒI bởi Quản trị viên."
                            )
                            raise odoo.exceptions.AccessDenied("CAD Workstation access has been REVOKED by Administrator. Please contact Admin to restore access.")

        # Cho phép Odoo xác thực tài khoản / mật khẩu
        uid = _original_dispatch_rpc(service_name, method, params)
        return uid

    elif service_name == 'object':
        try:
            db, uid, passwd, model, method_ = params[:5]
            # Bỏ qua không chặn nếu là model quản lý token hoặc hàm handshake cơ bản
            is_exempt = (method_ in HANDSHAKE_METHODS) or (model in ('plm.desktop.token', 'plm.access'))

            if not is_exempt:
                from odoo.modules.registry import Registry
                from odoo import api, fields
                with Registry(db).cursor() as cr:
                    env = api.Environment(cr, api.SUPERUSER_ID, {})
                    if 'plm.desktop.token' in env.registry:
                        cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                        row = cr.fetchone()
                        if row and row[0]:
                            tokens = env['plm.desktop.token'].search([('user_id', '=', int(uid))], order='id desc')
                            if tokens:
                                # 1. Nếu thiết bị đã bị Thu hồi: Chặn tuyệt đối mọi thao tác can thiệp dữ liệu
                                if any(t.is_revoked for t in tokens):
                                    _logger.warning(
                                        f">>> [TDB PLM] CHẶN RPC: Thiết bị của User ID {uid} "
                                        f"ĐÃ BỊ THU HỒI. Từ chối thực thi {model}.{method_}"
                                    )
                                    raise odoo.exceptions.AccessDenied("CAD Workstation access has been REVOKED by Administrator. Please contact Admin to restore access.")

                                # 2. Với các thao tác CAD: Bắt buộc còn hạn 180 ngày và có session_id hợp lệ
                                now = fields.Datetime.now()
                                active_tokens = [t for t in tokens if (not t.is_revoked) and t.expires_at and (t.expires_at > now) and t.session_id]
                                if not active_tokens:
                                    _logger.warning(
                                        f">>> [TDB PLM] CHẶN RPC: Thiết bị của User ID {uid} "
                                        f"ĐÃ HẾT HẠN hoặc CHƯA ĐĂNG NHẬP LẠI. Từ chối thực thi {model}.{method_}"
                                    )
                                    raise odoo.exceptions.AccessDenied("CAD 180-day Session has EXPIRED. Please use 'Execute New Login' from SolidWorks to renew.")
                                else:
                                    tokens[0].update_last_used()
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

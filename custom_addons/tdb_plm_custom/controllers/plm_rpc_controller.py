# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Layer 3: Tầng Controller điều phối & Middleware RPC cho OdooPLM Client (SolidWorks / Inventor)
=============================================================================================
Bối cảnh kỹ thuật:
- Trên Odoo 20, dịch vụ 'db' đã bị loại bỏ khỏi hàm dispatch_rpc (chỉ còn 'common' và 'object').
- Khi CAD Client (SolidWorks OdooPLM) kết nối, client gọi RPC service 'db', method 'list'
  để lấy danh sách Database hiển thị lên combobox đăng nhập.
- Controller này cung cấp bản vá (patch) hàm dispatch_rpc:
  1. Phục hồi service 'db' (list, list_db, db_exist) cho CAD Client.
  2. Bắt cả 2 phương thức xác thực của CAD Client: common.authenticate và common.login để
     luôn tự động mở khóa và gia hạn 180 ngày ngay lập tức khi đăng nhập từ SolidWorks.
  3. Cho phép các lệnh đọc người dùng/cấu hình và snapshot/dọn dẹp nền chạy trơn tru, loại bỏ triệt để
     các cảnh báo lặp đi lặp lại và đảm bảo New Login luôn thành công.
  4. Chặn đứng tuyệt đối (AccessDenied) mọi thao tác nghiệp vụ CAD (sửa linh kiện product.product,
     bản vẽ ir.attachment, bom mrp.bom, check-in, check-out) khi token 180 ngày đã HẾT HẠN hoặc BỊ THU HỒI.
"""
import sys
import logging
import secrets
from datetime import timedelta
import odoo
from odoo import api, fields
from odoo.http import router
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

# Lưu lại hàm dispatch_rpc nguyên bản của Odoo
_original_dispatch_rpc = getattr(router, '_tdb_original_dispatch_rpc', None)
if not _original_dispatch_rpc:
    _original_dispatch_rpc = router.dispatch_rpc
    router._tdb_original_dispatch_rpc = _original_dispatch_rpc

# Các model hệ thống phục vụ hiển thị UI, nạp thông tin người dùng và tiến trình đăng nhập
# Tuyệt đối không chặn các model này để New Login luôn thành công và không bị crash COM client
SYSTEM_SAFE_MODELS = (
    'res.users',
    'res.company',
    'res.partner',
    'plm.access',
    'plm.desktop.token',
    'ir.model.data',
    'ir.config_parameter',
)

# Các phương thức handshake, dọn dẹp phiên, đồng bộ trạng thái ngầm và đọc thông số môi trường
# Cho phép chạy ngầm để SolidWorks không liên tục bật cảnh báo lặp đi lặp lại và hoàn tất complete_login_session
SYSTEM_SAFE_METHODS = (
    'getServerTime',
    'getUserSign',
    'getMacros',
    'getCustomProcedure',
    'get_checkout_snapshot',
    'koo_context_get',
    'context_get',
    'checkUnlinkCadOpen',
    'cleanZipArchives',
    'CleanUp',
    'cleanUp',
)


def _cad_dispatch_rpc(service_name, method, params):
    """Điều phối RPC tùy biến (Middleware XML-RPC & JSON-RPC):
    1. Phục hồi service 'db' cho các ứng dụng CAD Client (SolidWorks/Inventor).
    2. Quản lý vòng đời Access Token 180 ngày:
       - Khi 'Execute New Login' thành công (qua authenticate hoặc login): Mở khóa và gia hạn 180 ngày ngay lập tức.
       - Khi 'Thu hồi quyền' (Revoked): Chặn đứng mọi thao tác và từ chối đăng nhập mới.
       - Khi 'Hết hạn' (Expired): Chặn đứng các thao tác CAD (product.product, ir.attachment, mrp.bom, plm.client)
         bằng AccessDenied để ngăn chặn mở form CAD Editing hoặc Check-in/Check-out.
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

    elif service_name == 'common' and method in ('authenticate', 'login'):
        # Xác thực XML-RPC cho CAD Client (hỗ trợ cả authenticate và login):
        # 1. Chặn đứng nếu thiết bị đang bị Admin THU HỒI quyền (kể cả có mật khẩu đúng).
        # 2. Khi kỹ sư bấm Login từ hộp thoại CAD (New Login) với mật khẩu đúng:
        #    Tự động mở khóa và gia hạn 180 ngày cho token của thiết bị.
        db, login, password = params[:3]
        from odoo.modules.registry import Registry

        # Kiểm tra trước: Nếu tài khoản/thiết bị đang bị Admin THU HỒI -> CHẶN ĐỨNG
        try:
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
                                    f">>> [TDB PLM] TỪ CHỐI XML-RPC {method.upper()}: Thiết bị của user '{login}' "
                                    f"đang ở trạng thái BỊ THU HỒI bởi Quản trị viên."
                                )
                                raise AccessDenied("Thiết bị CAD đã bị Quản trị viên thu hồi quyền truy cập. Vui lòng liên hệ Quản trị viên.")
        except AccessDenied:
            raise
        except Exception as e:
            _logger.debug(f"[TDB PLM] Kiểm tra revoke trước {method}: {e}")

        # Cho phép Odoo xác thực tài khoản / mật khẩu
        uid = _original_dispatch_rpc(service_name, method, params)

        # Khi đăng nhập thành công qua hộp thoại CAD (Execute New Login):
        # Mở khóa và gia hạn 180 ngày cho thiết bị
        if uid:
            try:
                with Registry(db).cursor() as cr:
                    env = api.Environment(cr, api.SUPERUSER_ID, {})
                    if 'plm.desktop.token' in env.registry:
                        cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                        row = cr.fetchone()
                        if row and row[0]:
                            tokens = env['plm.desktop.token'].search([('user_id', '=', int(uid))], order='id desc')
                            now = fields.Datetime.now()
                            new_session = f"cad_{now.strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(8)}"
                            if tokens:
                                tokens.write({
                                    'expires_at': now + timedelta(days=180),
                                    'is_revoked': False,
                                    'session_id': new_session,
                                    'last_used_date': now,
                                })
                                if len(tokens) > 1:
                                    (tokens - tokens[0]).unlink()
                            else:
                                env['plm.desktop.token'].create({
                                    'name': secrets.token_urlsafe(32),
                                    'user_id': int(uid),
                                    'machine_name': f"CAD WS ({login})",
                                    'machine_uuid': f"WS_{login}",
                                    'expires_at': now + timedelta(days=180),
                                    'is_revoked': False,
                                    'session_id': new_session,
                                    'last_used_date': now,
                                    'issued_at': now,
                                })
                            cr.commit()
                            _logger.info(
                                f">>> [TDB PLM] Kỹ sư '{login}' (UID {uid}) đã đăng nhập thành công từ hộp thoại CAD (qua {method}): "
                                f"Đã mở khóa và gia hạn 180 ngày cho thiết bị."
                            )
            except Exception as e:
                _logger.error(f"[TDB PLM] Lỗi gia hạn token trong common.{method}: {e}")

        return uid

    elif service_name == 'object':
        try:
            db, uid, passwd, model, method_ = params[:5]

            # Bỏ qua không chặn nếu là model hệ thống, tiến trình đăng nhập hoặc hàm đọc nền
            is_system_call = (model in SYSTEM_SAFE_MODELS) or (method_ in SYSTEM_SAFE_METHODS)

            # Chặn đứng các thao tác nghiệp vụ CAD thực tế nếu token hết hạn hoặc bị thu hồi
            if not is_system_call:
                from odoo.modules.registry import Registry
                with Registry(db).cursor() as cr:
                    env = api.Environment(cr, api.SUPERUSER_ID, {})
                    if 'plm.desktop.token' in env.registry:
                        cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                        row = cr.fetchone()
                        if row and row[0]:
                            tokens = env['plm.desktop.token'].search([('user_id', '=', int(uid))], order='id desc')
                            if tokens:
                                # 1. Nếu thiết bị đã bị Thu hồi: Chặn tuyệt đối
                                if any(t.is_revoked for t in tokens):
                                    _logger.warning(
                                        f">>> [TDB PLM] CHẶN RPC: Thiết bị của User ID {uid} "
                                        f"ĐÃ BỊ THU HỒI. Từ chối thực thi {model}.{method_}"
                                    )
                                    raise AccessDenied("Thiết bị CAD đã bị Quản trị viên thu hồi quyền truy cập. Vui lòng liên hệ Quản trị viên.")

                                # 2. Với các thao tác CAD: Bắt buộc token còn trong thời hạn 180 ngày
                                now = fields.Datetime.now()
                                active_tokens = [t for t in tokens if (not t.is_revoked) and t.expires_at and (t.expires_at > now)]
                                if not active_tokens:
                                    _logger.warning(
                                        f">>> [TDB PLM] CHẶN RPC: Thiết bị của User ID {uid} "
                                        f"ĐÃ HẾT HẠN 180 NGÀY. Từ chối thực thi {model}.{method_}"
                                    )
                                    raise AccessDenied("Phiên làm việc CAD 180 ngày đã hết hạn. Vui lòng bấm 'Execute New Login' từ SolidWorks để tiếp tục.")
                                else:
                                    tokens[0].update_last_used()
                            else:
                                _logger.warning(
                                    f">>> [TDB PLM] CHẶN RPC: User ID {uid} chưa có token thiết bị CAD. Từ chối thực thi {model}.{method_}"
                                )
                                raise AccessDenied("Thiết bị CAD chưa được xác thực hoặc phiên đã hết hạn. Vui lòng bấm 'Execute New Login' từ SolidWorks.")
        except AccessDenied:
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

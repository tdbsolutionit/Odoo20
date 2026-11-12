# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Layer 3: Tầng Controller điều phối & Middleware RPC cho OdooPLM Client (SolidWorks / Inventor)
=============================================================================================
Kiến trúc Chốt chặn Triple-Gate dứt điểm triệt để:
1. Phục hồi service 'db' (list, list_db, db_exist) cho CAD Client (do Odoo 20 đã loại bỏ khỏi dispatch_rpc).
2. Monkeypatch trực tiếp tầng odoo.service.model.dispatch:
   Bắt MỌI cuộc gọi XML-RPC, JSON-RPC thực thi model (product.product, ir.attachment, mrp.bom, plm.client, v.v.).
   Chặn đứng toàn bộ thao tác sửa/lưu (createFromProps, SaveOrUpdate, write, create, check-in, check-out)
   khi token 180 ngày hết hạn hoặc bị thu hồi.
3. Monkeypatch trực tiếp tầng odoo.service.common.dispatch:
   - Chặn tuyệt đối nếu máy trạm CAD đang bị Admin Thu hồi (Revoked).
   - Tự động mở khóa và gia hạn 180 ngày khi kỹ sư bấm New Login và nhập đúng mật khẩu.
"""
import sys
import logging
import secrets
from datetime import timedelta
import odoo
import odoo.service.model
import odoo.service.common
from odoo import api, fields
from odoo.http import router
from odoo.exceptions import UserError, AccessDenied

_logger = logging.getLogger(__name__)

# Lưu lại các hàm dispatch nguyên bản
_original_dispatch_rpc = getattr(router, '_tdb_original_dispatch_rpc', None)
if not _original_dispatch_rpc:
    _original_dispatch_rpc = router.dispatch_rpc
    router._tdb_original_dispatch_rpc = _original_dispatch_rpc

_original_model_dispatch = getattr(odoo.service.model, '_tdb_original_dispatch', None)
if not _original_model_dispatch:
    _original_model_dispatch = odoo.service.model.dispatch
    odoo.service.model._tdb_original_dispatch = _original_model_dispatch

_original_common_dispatch = getattr(odoo.service.common, '_tdb_original_dispatch', None)
if not _original_common_dispatch:
    _original_common_dispatch = odoo.service.common.dispatch
    odoo.service.common._tdb_original_dispatch = _original_common_dispatch

# Các model hệ thống phục vụ hiển thị UI, nạp thông tin người dùng và tiến trình đăng nhập
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


# ==============================================================================
# 1. GATE MODEL: Chặn đứng mọi RPC object tại tầng odoo.service.model.dispatch
# ==============================================================================
def _cad_model_dispatch(method, params):
    """Chốt chặn tầng thấp nhất của Odoo RPC Object:
    Bắt mọi yêu cầu execute/execute_kw gửi tới bất kỳ model nào.
    """
    try:
        db, uid, passwd, model, method_, *args = params
        uid = int(uid)

        is_safe = (model in SYSTEM_SAFE_MODELS) or (method_ in SYSTEM_SAFE_METHODS)

        if not is_safe:
            from odoo.modules.registry import Registry
            with Registry(db).cursor() as cr:
                env = api.Environment(cr, api.SUPERUSER_ID, {})
                if 'plm.desktop.token' in env.registry:
                    cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                    row = cr.fetchone()
                    if row and row[0]:
                        tokens = env['plm.desktop.token'].search([('user_id', '=', uid)], order='id desc')
                        if tokens:
                            if any(t.is_revoked for t in tokens):
                                _logger.warning(
                                    f">>> [TDB PLM] CHẶN model.dispatch: Thiết bị của User ID {uid} "
                                    f"ĐÃ BỊ THU HỒI. Từ chối {model}.{method_}"
                                )
                                raise UserError("Thiết bị CAD đã bị Quản trị viên thu hồi quyền truy cập. Vui lòng liên hệ Quản trị viên.")

                            now = fields.Datetime.now()
                            active_tokens = [t for t in tokens if (not t.is_revoked) and t.expires_at and (t.expires_at > now)]
                            if not active_tokens:
                                _logger.warning(
                                    f">>> [TDB PLM] CHẶN model.dispatch: Thiết bị của User ID {uid} "
                                    f"ĐÃ HẾT HẠN 180 NGÀY. Từ chối {model}.{method_}"
                                )
                                raise UserError("Phiên làm việc CAD 180 ngày đã HẾT HẠN. Vui lòng bấm 'Execute New Login' từ SolidWorks để tiếp tục.")
                            else:
                                tokens[0].update_last_used()
                        else:
                            _logger.warning(
                                f">>> [TDB PLM] CHẶN model.dispatch: User ID {uid} chưa có token thiết bị CAD. Từ chối {model}.{method_}"
                            )
                            raise UserError("Thiết bị CAD chưa được xác thực hoặc phiên đã hết hạn. Vui lòng bấm 'Execute New Login' từ SolidWorks.")
    except (UserError, AccessDenied):
        raise
    except Exception as e:
        _logger.debug(f"[TDB PLM] Lỗi kiểm tra token trong model.dispatch: {e}")

    return _original_model_dispatch(method, params)

odoo.service.model.dispatch = _cad_model_dispatch


# ==============================================================================
# 2. GATE AUTHENTICATION: Xử lý Đăng nhập & Gia hạn tại odoo.service.common.dispatch
# ==============================================================================
def _cad_common_dispatch(method, params):
    """Chốt chặn tầng thấp nhất của Odoo RPC Common:
    Bắt login / authenticate để kiểm tra thu hồi và gia hạn 180 ngày khi đăng nhập hợp lệ.
    """
    if method in ('authenticate', 'login'):
        db, login, password = params[:3]
        from odoo.modules.registry import Registry

        # 1. Kiểm tra nếu thiết bị đang bị Thu hồi: CHẶN ĐỨNG
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
                                    f">>> [TDB PLM] TỪ CHỐI common.dispatch {method.upper()}: Thiết bị của user '{login}' "
                                    f"đang ở trạng thái BỊ THU HỒI bởi Quản trị viên."
                                )
                                raise UserError("Thiết bị CAD đã bị Quản trị viên thu hồi quyền truy cập. Vui lòng liên hệ Quản trị viên.")
        except (UserError, AccessDenied):
            raise
        except Exception as e:
            _logger.debug(f"[TDB PLM] Kiểm tra revoke trước common.dispatch {method}: {e}")

        # 2. Thực hiện xác thực nguyên bản của Odoo
        uid = _original_common_dispatch(method, params)

        # 3. Khi kỹ sư đăng nhập thành công với mật khẩu đúng: Mở khóa và gia hạn 180 ngày ngay lập tức
        if uid and isinstance(uid, int):
            try:
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

                            machine_name = f"CAD WS ({client_ip})" if client_ip else f"CAD WS ({login})"
                            machine_uuid = f"WS_{machine_name}"
                            now = fields.Datetime.now()
                            new_session = f"cad_{now.strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(8)}"

                            env['plm.desktop.token'].register_session_token(
                                user_id=uid,
                                session_id=new_session,
                                machine_uuid=machine_uuid,
                                machine_name=machine_name,
                                client_ip=client_ip,
                                cad_version='SolidWorks 2022'
                            )
                            cr.commit()
                            _logger.info(
                                f">>> [TDB PLM] Kỹ sư '{login}' (UID {uid}) đã đăng nhập thành công qua CAD {method}: "
                                f"Đã mở khóa và gia hạn 180 ngày cho thiết bị."
                            )
            except Exception as e:
                _logger.error(f"[TDB PLM] Lỗi gia hạn token trong common.dispatch {method}: {e}")

        return uid

    return _original_common_dispatch(method, params)

odoo.service.common.dispatch = _cad_common_dispatch


# ==============================================================================
# 3. ROUTER DISPATCH RPC: Phục hồi service 'db' cho CAD Client
# ==============================================================================
def _cad_dispatch_rpc(service_name, method, params):
    """Bổ sung phục hồi service 'db' cho SolidWorks / Inventor Add-in."""
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

    return _original_dispatch_rpc(service_name, method, params)

router.dispatch_rpc = _cad_dispatch_rpc

# Đồng bộ vào các controller rpc nếu đã nạp trong sys.modules
for mod_path in (
    'odoo.addons.rpc.controllers.xmlrpc',
    'odoo.addons.rpc.controllers.jsonrpc',
    'addons.rpc.controllers.xmlrpc',
    'addons.rpc.controllers.jsonrpc',
):
    if mod_path in sys.modules:
        setattr(sys.modules[mod_path], 'dispatch_rpc', _cad_dispatch_rpc)

_logger.info(">>> [TDB PLM] Đã kích hoạt bản vá toàn diện Triple-Gate (model.dispatch, common.dispatch, router.dispatch_rpc).")

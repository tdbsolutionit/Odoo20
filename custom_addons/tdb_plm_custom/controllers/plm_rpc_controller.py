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

    elif service_name == 'object':
        try:
            db, uid, passwd, model, method_ = params[:5]
            # Chặn trên mọi model liên quan đến CAD/PLM (bao gồm cả linh kiện kỹ thuật product.product)
            if str(model).startswith('plm.') or model in CAD_OPERATIONAL_MODELS:
                from odoo.modules.registry import Registry
                from odoo import api
                with Registry(db).cursor() as cr:
                    env = api.Environment(cr, api.SUPERUSER_ID, {})
                    if 'plm.desktop.token' in env.registry:
                        cr.execute("SELECT to_regclass('public.plm_desktop_token');")
                        row = cr.fetchone()
                        if row and row[0]:
                            req = odoo.http.request_var.get(None)
                            client_ip = None
                            if req and hasattr(req, 'httprequest'):
                                client_ip = req.httprequest.headers.get('X-Forwarded-For') or req.httprequest.remote_addr
                                if client_ip and ',' in client_ip:
                                    client_ip = client_ip.split(',')[0].strip()

                            token = False
                            if client_ip:
                                token = env['plm.desktop.token'].search([
                                    ('user_id', '=', int(uid)),
                                    ('client_ip', '=', client_ip),
                                ], order='id desc', limit=1)
                            if not token:
                                token = env['plm.desktop.token'].search([('user_id', '=', int(uid))], order='id desc', limit=1)

                            if token:
                                from odoo import fields
                                now = fields.Datetime.now()
                                if token.is_revoked:
                                    _logger.warning(
                                        f">>> [TDB PLM] CHẶN RPC: Thiết bị '{token.machine_name}' "
                                        f"của User ID {uid} ĐÃ BỊ THU HỒI. Từ chối thực thi {model}.{method_}"
                                    )
                                    raise odoo.exceptions.AccessDenied("CAD Workstation access has been REVOKED by Administrator.")
                                elif token.expires_at and token.expires_at <= now:
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

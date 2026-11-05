# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Layer 3: Tầng Controller điều phối & Khắc phục tương thích RPC cho OdooPLM Client (SolidWorks / Inventor)
======================================================================================================
Bối cảnh kỹ thuật:
- Trên Odoo 20, dịch vụ 'db' đã bị loại bỏ khỏi hàm dispatch_rpc (chỉ còn 'common' và 'object').
- Khi CAD Client (SolidWorks OdooPLM) kết nối, client thực hiện gọi RPC service 'db', method 'list'
  để lấy danh sách Database hiển thị lên combobox đăng nhập.
- Khi Odoo 20 ném ngoại lệ ValueError("Invalid service name: db"), CAD Client hiểu nhầm là mất kết nối
  và hiển thị "Could not connect to server !".
- Controller này cung cấp bản vá (patch) hàm dispatch_rpc nhằm phục hồi khả năng phản hồi danh mục database cho CAD Client.
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


def _cad_dispatch_rpc(service_name, method, params):
    """Điều phối RPC tùy biến, hỗ trợ thêm service 'db' cho các ứng dụng CAD Client (SolidWorks/Inventor)."""
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
                return [d.strip() for d in str(cfg_db).split(',') if d.strip()]
            return ['odoo20']
        elif method == 'db_exist':
            target_db = params[0] if params else ''
            cfg_db = odoo.tools.config.get('db_name') or 'odoo20'
            return target_db in (cfg_db, 'odoo20')
        elif method == 'server_version':
            return odoo.release.version
        elif method == 'server_environment':
            return 'production'
    return _original_dispatch_rpc(service_name, method, params)


# 1. Áp dụng bản vá vào router.dispatch_rpc
router.dispatch_rpc = _cad_dispatch_rpc

# 2. Đồng bộ bản vá vào các controller rpc nếu đã nạp trước đó trong sys.modules
for mod_path in ('odoo.addons.rpc.controllers.xmlrpc', 'odoo.addons.rpc.controllers.jsonrpc'):
    if mod_path in sys.modules:
        setattr(sys.modules[mod_path], 'dispatch_rpc', _cad_dispatch_rpc)

_logger.info(">>> [TDB PLM] Đã kích hoạt bản vá tương thích CAD Client XML-RPC / JSON-RPC (service: db) cho Odoo 20.")

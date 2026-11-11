# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import logging
from odoo.http import Controller, route, request
from odoo.http.session import logout

_logger = logging.getLogger(__name__)


class TdbWebSession(Controller):

    @route('/web/session/logout', type='http', auth='none', methods=['GET', 'POST'], readonly=True, csrf=False)
    def logout(self, redirect='/web/login'):
        """Cho phép đăng xuất an toàn bằng cả phương thức GET và POST, tránh hoàn toàn lỗi 405 Method Not Allowed."""
        try:
            logout(request.session, keep_db=True)
        except Exception as e:
            _logger.debug(f"[TDB PLM] Lỗi khi logout: {e}")
            if hasattr(request, 'session') and request.session:
                request.session.clear()
        return request.redirect(redirect or '/web/login', 303)

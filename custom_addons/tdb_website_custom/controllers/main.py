# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
from odoo import http
from odoo.http import request


class TdbRootController(http.Controller):

    @http.route(['/', '/home'], type='http', auth='public', website=False, sitemap=False, readonly=False)
    def index(self, **kw):
        """
        Khi truy cập trang chủ (/ hoặc /home),
        tự động chuyển hướng về trang đăng nhập (/web/login).
        """
        from werkzeug.utils import redirect as werkzeug_redirect
        return werkzeug_redirect('/web/login', code=303)

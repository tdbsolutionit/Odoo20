# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
from odoo import http
from odoo.http import request

try:
    from odoo.addons.website.controllers.main import Website
except ImportError:
    Website = http.Controller


class TdbRootController(Website):

    @http.route(['/', '/home'], type='http', auth='public', website=True, sitemap=False)
    def index(self, **kw):
        """
        Khi truy cập địa chỉ IP hoặc domain trang chủ (/),
        tự động chuyển hướng URL trình duyệt sang thẳng trang đăng nhập (/web/login).
        """
        return request.redirect('/web/login', 303)

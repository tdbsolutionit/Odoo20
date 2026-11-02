# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
from odoo import http
from odoo.http import request

try:
    from odoo.addons.website.controllers.main import Website
except ImportError:
    Website = http.Controller


class BaceRootController(Website):

    @http.route('/', type='http', auth='public', website=True, sitemap=False)
    def index(self, **kw):
        """
        Điều hướng trang chủ theo phong cách B-ACE SME:
        - Nếu chưa đăng nhập: chuyển hướng ngay đến trang đăng nhập (/web/login).
        - Nếu đã đăng nhập: chuyển hướng vào thẳng hệ thống Backend Dashboard (/web).
        """
        if not request.session.uid or request.env.user._is_public():
            return request.redirect('/web/login')
        return request.redirect('/web')

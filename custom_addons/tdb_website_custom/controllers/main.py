# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import hashlib
from odoo import http
from odoo.http import request

try:
    from odoo.addons.website.controllers.main import Website
except ImportError:
    Website = http.Controller

try:
    from odoo.addons.web.controllers.home import Home
except ImportError:
    Home = http.Controller

SECURITY_KEY = 'TDB_SOLUTION_2026_SECURITY_SALT'


def decrypt_tdb_password(token: str, key: str = SECURITY_KEY) -> str:
    """
    Giải mã token mật khẩu gửi từ frontend (định dạng TDB_ENC:<salt>:<xor_hex>).
    Sử dụng giải thuật SHA-256 CTR stream cipher đồng bộ chính xác với Frontend.
    """
    if not token or not isinstance(token, str) or not token.startswith('TDB_ENC:'):
        return token
    try:
        parts = token.split(':')
        if len(parts) != 3:
            return token
        salt, xor_hex = parts[1], parts[2]
        xor_bytes = bytes.fromhex(xor_hex)
        out = bytearray()
        counter = 0
        while len(out) < len(xor_bytes):
            block = hashlib.sha256(f'{key}:{salt}:{counter}'.encode('utf-8')).digest()
            out.extend(block)
            counter += 1
        plain_bytes = bytes([b ^ out[i] for i, b in enumerate(xor_bytes)])
        return plain_bytes.decode('utf-8')
    except Exception:
        return token


class TdbLoginSecurityController(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        """
        Kế thừa route /web/login:
        Giải mã mật khẩu nếu frontend gửi dạng mã hóa TDB_ENC:
        trước khi Odoo thực hiện authenticate().
        """
        if request.httprequest.method == 'POST':
            raw_pwd = kw.get('password')
            if not raw_pwd and hasattr(request, 'params'):
                raw_pwd = request.params.get('password')

            if raw_pwd and isinstance(raw_pwd, str) and raw_pwd.startswith('TDB_ENC:'):
                decrypted = decrypt_tdb_password(raw_pwd)
                kw['password'] = decrypted
                if hasattr(request, 'params'):
                    request.params['password'] = decrypted

        return super().web_login(redirect=redirect, **kw)


class TdbRootController(Website):

    @http.route(['/', '/home'], type='http', auth='public', website=True, sitemap=False)
    def index(self, **kw):
        """
        Khi truy cập địa chỉ IP hoặc domain trang chủ (/),
        tự động chuyển hướng URL trình duyệt sang thẳng trang đăng nhập (/web/login).
        """
        return request.redirect('/web/login', 303)

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

# Hash SHA-256 định danh cho các mật khẩu hệ thống
SHA256_MATKHAUMOI = hashlib.sha256(b'MatKhauMoi').hexdigest().lower()
SHA256_ADMIN = hashlib.sha256(b'admin').hexdigest().lower()


def resolve_tdb_password(token: str) -> str:
    """
    Xử lý mật khẩu gửi từ client:
    1. Giải mã token mã hóa bảo vệ vận chuyển: SHA256:<hash>:<cipher>
       - Giải mã cipher bằng keystream XOR 0x5A
       - Kiểm tra hash SHA-256 của chuỗi sau giải mã có khớp với <hash> không
       - Nếu khớp chính xác, trả về mật khẩu gốc ban đầu để Odoo xác thực
    2. Fallback cho client cũ chỉ gửi SHA256:<hash>:
       - Khớp với SHA256('MatKhauMoi') -> trả về 'MatKhauMoi'
       - Khớp với SHA256('admin') -> trả về 'admin'
    3. Nếu không có định dạng mã hóa, trả về nguyên bản để Odoo xác thực
       (người dùng gõ chuỗi mã hóa vào ô mật khẩu sẽ bị coi là mật khẩu sai).
    """
    if not token or not isinstance(token, str):
        return token

    token_clean = token.strip()

    # Xử lý định dạng SHA256:
    if token_clean.startswith('SHA256:'):
        parts = token_clean.split(':')

        # 1. Ưu tiên giải mã cipher kèm theo (SHA256:<hash>:<cipher>)
        if len(parts) >= 3 and parts[2]:
            try:
                cipher_hex = parts[2].strip()
                cipher_bytes = bytes.fromhex(cipher_hex)
                plain = bytes([b ^ 0x5A for b in cipher_bytes]).decode('utf-8')
                if hashlib.sha256(plain.encode('utf-8')).hexdigest().lower() == parts[1].strip().lower():
                    return plain
            except Exception:
                pass

        # 2. Fallback nếu chỉ gửi mã băm SHA256:<hash>
        hash_val = parts[1].strip().lower()
        if hash_val == SHA256_MATKHAUMOI:
            return 'MatKhauMoi'
        elif hash_val == SHA256_ADMIN:
            return 'admin'

        return token_clean

    return token


LoginBaseClass = Website if (Website != http.Controller and issubclass(Website, Home)) else Home


class TdbLoginSecurityController(LoginBaseClass):

    @http.route('/web/login', type='http', auth="none", readonly=False)
    def web_login(self, redirect=None, **kw):
        """
        Kế thừa route /web/login:
        Giải mã mật khẩu nếu frontend gửi payload mã hóa bảo vệ vận chuyển
        trước khi Odoo thực hiện authenticate().
        """
        if request.httprequest.method == 'POST':
            raw_pwd = kw.get('password')
            if not raw_pwd and hasattr(request, 'params'):
                raw_pwd = request.params.get('password')

            if raw_pwd and isinstance(raw_pwd, str):
                resolved = resolve_tdb_password(raw_pwd)
                kw['password'] = resolved
                if hasattr(request, 'params'):
                    request.params['password'] = resolved

        return super().web_login(redirect=redirect, **kw)


class TdbRootController(Website):

    @http.route(['/', '/home'], type='http', auth='public', website=True, sitemap=False)
    def index(self, **kw):
        """
        Khi truy cập địa chỉ IP hoặc domain trang chủ (/),
        tự động chuyển hướng URL trình duyệt sang thẳng trang đăng nhập (/web/login).
        """
        return request.redirect('/web/login', 303)

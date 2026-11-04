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
    1. Nếu là chuỗi hash SHA-256 (bắt đầu bằng SHA256: hoặc là chuỗi hex 64 ký tự):
       - Khớp với SHA256('MatKhauMoi') -> trả về 'MatKhauMoi'
       - Khớp với SHA256('admin') -> trả về 'admin'
       - Nếu có token cipher phụ trợ (SHA256:<hash>:<cipher>) -> giải mã cipher
    2. Nếu là định dạng TDB_ENC:... -> giải mã stream cipher
    3. Trả về mật khẩu gốc để Odoo authenticate bình thường.
    """
    if not token or not isinstance(token, str):
        return token

    token = token.strip()

    # Xử lý định dạng SHA256:
    if token.startswith('SHA256:'):
        parts = token.split(':')
        hash_val = parts[1].strip().lower()
        if hash_val == SHA256_MATKHAUMOI:
            return 'MatKhauMoi'
        elif hash_val == SHA256_ADMIN:
            return 'admin'

        # Nếu có token cipher phụ trợ (SHA256:<hash>:<cipher>)
        if len(parts) >= 3 and parts[2]:
            try:
                cipher_hex = parts[2].strip()
                cipher_bytes = bytes.fromhex(cipher_hex)
                plain = bytes([b ^ 0x5A for b in cipher_bytes]).decode('utf-8')
                if hashlib.sha256(plain.encode('utf-8')).hexdigest().lower() == hash_val:
                    return plain
            except Exception:
                pass
        return token

    # Nếu gửi trực tiếp 64 ký tự hex SHA-256
    token_lower = token.lower()
    if len(token_lower) == 64 and all(c in '0123456789abcdef' for c in token_lower):
        if token_lower == SHA256_MATKHAUMOI:
            return 'MatKhauMoi'
        elif token_lower == SHA256_ADMIN:
            return 'admin'

    # Hỗ trợ định dạng cũ TDB_ENC: nếu có
    if token.startswith('TDB_ENC:'):
        return decrypt_tdb_password(token)

    return token


SECURITY_KEY = 'TDB_SOLUTION_2026_SECURITY_SALT'


def decrypt_tdb_password(token: str, key: str = SECURITY_KEY) -> str:
    """
    Giải mã token mật khẩu gửi từ frontend (định dạng TDB_ENC:<salt>:<xor_hex>).
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


LoginBaseClass = Website if (Website != http.Controller and issubclass(Website, Home)) else Home


class TdbLoginSecurityController(LoginBaseClass):

    @http.route('/web/login', type='http', auth="none", readonly=False)
    def web_login(self, redirect=None, **kw):
        """
        Kế thừa route /web/login:
        Giải mã mật khẩu nếu frontend gửi dạng SHA256: hoặc TDB_ENC:
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

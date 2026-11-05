# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import hashlib
from odoo import http
from odoo.http import request

try:
    from odoo.addons.web.controllers.home import Home
except ImportError:
    Home = http.Controller

# Nạp controller Website (nếu module website được cài trên server).
# Website kế thừa Home và gắn website=True vào /web/login,
# gây ra redirect tự động sang /en/web/login.
# Để triệt tiêu lỗi redirect loop, ta PHẢI kế thừa từ Website
# và ghi đè website=False.
try:
    from odoo.addons.website.controllers.main import Website as WebsiteHome
except ImportError:
    WebsiteHome = None

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
    3. Nếu token là chuỗi thô 'SHA256:MatKhauMoi' hoặc 'SHA256:admin' -> trả về mật khẩu tương ứng
    4. Nếu không có định dạng mã hóa, trả về nguyên bản để Odoo xác thực.
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

        # 2. Fallback nếu chỉ gửi mã băm hoặc chuỗi thô SHA256:...
        if len(parts) >= 2:
            sec = parts[1].strip()
            if sec == 'MatKhauMoi' or sec.lower() == SHA256_MATKHAUMOI:
                return 'MatKhauMoi'
            elif sec == 'admin' or sec.lower() == SHA256_ADMIN:
                return 'admin'

        return token_clean

    return token


def _resolve_password_in_request(kw):
    """Helper: giải mã mật khẩu SHA256 trong request params & form data."""
    raw_pwd = kw.get('password')
    if not raw_pwd and hasattr(request, 'params'):
        raw_pwd = request.params.get('password')

    if raw_pwd and isinstance(raw_pwd, str):
        resolved = resolve_tdb_password(raw_pwd)
        kw['password'] = resolved
        if hasattr(request, 'params'):
            request.params['password'] = resolved
        try:
            if hasattr(request.httprequest, 'form') and 'password' in request.httprequest.form:
                form_dict = request.httprequest.form.to_dict()
                form_dict['password'] = resolved
                from werkzeug.datastructures import ImmutableMultiDict
                request.httprequest.form = ImmutableMultiDict(form_dict)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# Monkey-patch Home.web_login — lớp bảo vệ nền tảng
# Đảm bảo giải mã mật khẩu SHA256 bất kể route nào gọi Home.web_login
# ─────────────────────────────────────────────────────────────
_orig_home_web_login = getattr(Home, 'web_login', None)


def _tdb_safe_web_login(self, redirect=None, **kw):
    if request.httprequest.method == 'POST':
        _resolve_password_in_request(kw)
    if _orig_home_web_login:
        return _orig_home_web_login(self, redirect=redirect, **kw)
    return super(Home, self).web_login(redirect=redirect, **kw)


if _orig_home_web_login:
    Home.web_login = _tdb_safe_web_login


# ─────────────────────────────────────────────────────────────
# Controller chính: kế thừa route /web/login
# ─────────────────────────────────────────────────────────────
# Chọn lớp cha cao nhất trong chuỗi kế thừa:
#   Nếu website module đã cài → kế thừa WebsiteHome (Website → Home)
#   Nếu chưa cài → kế thừa Home
# Điều này ĐẢM BẢO route /web/login của ta ghi đè route của
# website module (nếu có), triệt tiêu website=True → không còn
# redirect vô hạn /web/login ↔ /en/web/login.
LoginBaseClass = WebsiteHome if WebsiteHome is not None else Home


class TdbLoginSecurityController(LoginBaseClass):

    @http.route('/web/login', type='http', auth="none", readonly=False, website=False, sitemap=False)
    def web_login(self, redirect=None, **kw):
        """
        Kế thừa route /web/login:
        - Giải mã mật khẩu SHA256 nếu frontend gửi payload mã hóa.
        - Ghi đè website=False để CHẶN TRIỆT ĐỂ redirect sang /en/web/login.
        - auth="none" giống hệt Odoo core, không phải auth="public".
        """
        if request.httprequest.method == 'POST':
            _resolve_password_in_request(kw)

        try:
            return super().web_login(redirect=redirect, **kw)
        except Exception as e:
            from werkzeug.exceptions import BadRequest
            if isinstance(e, BadRequest) or 'CSRF' in str(e):
                values = dict(request.params)
                values['error'] = 'Phiên làm việc đã được làm mới. Vui lòng đăng nhập lại.'
                return request.render('web.login', values)
            raise


# ─────────────────────────────────────────────────────────────
# Controller gốc: chuyển hướng / và /home về /web/login
# ─────────────────────────────────────────────────────────────
class TdbRootController(LoginBaseClass):

    @http.route(['/', '/home'], type='http', auth='public', website=False, sitemap=False, readonly=False)
    def index(self, **kw):
        """
        Khi truy cập địa chỉ IP hoặc domain trang chủ (/ hoặc /home),
        chuyển hướng trực tiếp sang /web/login bằng werkzeug redirect chuẩn.
        website=False ngăn Odoo thêm tiền tố ngôn ngữ (/en/, /vi/).
        """
        from werkzeug.utils import redirect as werkzeug_redirect
        return werkzeug_redirect('/web/login', code=303)

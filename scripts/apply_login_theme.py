# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import os
import sys

def main():
    print('=' * 80)
    print('>>> KHOI PHUC GIAO DIEN DANG NHAP TDB SOLUTION (CORPORATE GOLD THEME) <<<')
    print('=' * 80)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    odoo_dir = os.path.abspath(os.path.join(current_dir, '..')) if os.path.basename(current_dir) in ('scripts', 'custom_addons') else current_dir
    os.chdir(odoo_dir)
    if odoo_dir not in sys.path:
        sys.path.insert(0, odoo_dir)

    import odoo
    from odoo.tools import config
    try:
        from odoo.modules.registry import Registry
    except ImportError:
        from odoo.orm.registry import Registry

    config_path = os.path.join(odoo_dir, 'odoo.conf')
    if not os.path.exists(config_path):
        config_path = 'odoo.conf'

    try:
        config.parse_config(['-c', config_path, '-d', 'odoo20'], setup_logging=False)
    except TypeError:
        config.parse_config(['-c', config_path, '-d', 'odoo20'])

    registry = Registry('odoo20')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
# Bước 6: Khôi phục giao diện đăng nhập TDB Solution nguyên bản (không mã hóa) & Đồng bộ tài khoản admin
        print("\n[6/7] Khôi phục giao diện Đăng nhập TDB Solution (chuẩn Hình 1 & Logo Hình 2, không mã hóa)...")
        try:
            View = env['ir.ui.view']

            # 1. Gỡ bỏ / vô hiệu hóa các view con xung đột kế thừa web.login_layout hoặc web.login
            layout_target = env.ref('web.login_layout', raise_if_not_found=False)
            login_target = env.ref('web.login', raise_if_not_found=False)

            if layout_target:
                for cv in View.search([('inherit_id', '=', layout_target.id), ('id', '!=', layout_target.id), ('active', '=', True)]):
                    try:
                        cv.write({'active': False})
                    except Exception:
                        pass

            if login_target:
                for cv in View.search([('inherit_id', '=', login_target.id), ('id', '!=', login_target.id), ('active', '=', True)]):
                    try:
                        cv.write({'active': False})
                    except Exception:
                        pass

            # 2. Xóa các COW view của web.login_layout hoặc web.login (nếu có trên website cụ thể)
            cow_views = View.search([
                ('key', 'in', ['web.login_layout', 'web.login']),
                ('website_id', '!=', False)
            ])
            for cv in cow_views:
                try:
                    cv.unlink()
                except Exception:
                    pass

            # 3. Cập nhật trực tiếp web.login_layout với đầy đủ CSS inline và bộ chuyển đổi ngôn ngữ
            tdb_layout_arch = """<t t-name="web.login_layout">
    <t t-call="web.layout">
        <t t-set="html_data" t-value="{'style': 'height: 100%;'}"/>
        <t t-set="body_classname" t-value="'tdb-login-body'"/>
        <style>
<![CDATA[
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    min-height: 100% !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background: #FAF6EE !important;
    color: #1E293B !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
    text-rendering: optimizeLegibility !important;
    overflow-x: hidden !important;
}

*, *::before, *::after {
    box-sizing: border-box !important;
}

img, svg {
    max-width: 100%;
    height: auto;
}

#top, #bottom, header, footer, .o_header_standard, .o_footer, .o_footer_copyright, .oe_website_login_container > .container, #oe_main_menu_navbar {
    display: none !important;
}

.login-wrapper {
    position: relative !important;
    width: 100% !important;
    min-height: 100vh !important;
    min-height: 100dvh !important;
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    flex-direction: row !important;
    background-color: #FAF6EE !important;
    background-image: url('/tdb_website_custom/static/src/img/login_bg.webp?v=20261102_clean_v4') !important;
    background-repeat: no-repeat !important;
    background-position: center center !important;
    background-size: cover !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* ---------------- Cột trái: Trình bày Giá Trị Cốt Lõi ---------------- */
.presentation-side {
    flex: 1.2 !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    padding: 44px 60px 40px !important;
    position: relative !important;
    z-index: 2 !important;
    box-sizing: border-box !important;
}

.top-brand-logo {
    display: inline-block !important;
    text-align: left !important;
}

.top-brand-logo img {
    height: 56px !important;
    width: auto !important;
    display: block !important;
    object-fit: contain !important;
}

.core-content-center {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    text-align: center !important;
    margin: auto 0 !important;
    padding: 28px 0 !important;
    max-width: 1040px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.core-heading-wrap {
    margin-bottom: 36px !important;
    text-align: center !important;
}

.core-title {
    font-size: 58px !important;
    font-weight: 800 !important;
    letter-spacing: -0.015em !important;
    line-height: 1.18 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 16px !important;
}

.word-navy {
    color: #1E293B !important;
}

.word-gold {
    color: #EAA015 !important;
    position: relative !important;
}

.title-gold-line {
    width: 120px !important;
    height: 5px !important;
    background: #EAA015 !important;
    border-radius: 3px !important;
    margin: 14px auto 0 !important;
}

.core-subtitle {
    font-size: 19px !important;
    font-weight: 500 !important;
    color: #475569 !important;
    line-height: 1.65 !important;
    margin: 20px 0 0 0 !important;
    max-width: 780px !important;
}

.values-row {
    display: flex !important;
    justify-content: center !important;
    gap: 26px !important;
    width: 100% !important;
    margin-top: 24px !important;
}

.value-card {
    flex: 1 1 280px !important;
    max-width: 330px !important;
    background: #FFFFFF !important;
    border: 1.5px solid rgba(240, 230, 210, 0.95) !important;
    border-radius: 22px !important;
    padding: 30px 28px 28px !important;
    box-shadow: 0 14px 34px rgba(220, 180, 100, 0.14), 0 3px 10px rgba(0, 0, 0, 0.03) !important;
    text-align: left !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
    box-sizing: border-box !important;
}

.value-card:hover {
    transform: translateY(-5px) !important;
    box-shadow: 0 20px 42px rgba(220, 180, 100, 0.22) !important;
    border-color: #EAA015 !important;
}

.value-card-header {
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    margin-bottom: 14px !important;
}

.value-icon-box {
    width: 54px !important;
    height: 54px !important;
    border-radius: 14px !important;
    background: #FFFBEB !important;
    border: 1.5px solid #FDE68A !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    color: #EAA015 !important;
    box-shadow: 0 3px 8px rgba(234, 160, 21, 0.12) !important;
}

.value-icon-box svg {
    width: 28px !important;
    height: 28px !important;
    stroke: #EAA015 !important;
    stroke-width: 2.3 !important;
}

/* Vạch màu vàng ở giữa icon và chữ theo đúng yêu cầu */
.value-divider {
    width: 3.5px !important;
    height: 32px !important;
    background: #EAA015 !important;
    border-radius: 2px !important;
    flex-shrink: 0 !important;
}

.value-title {
    font-size: 22px !important;
    font-weight: 800 !important;
    color: #1E293B !important;
    margin: 0 !important;
    white-space: nowrap !important;
}

.value-desc {
    font-size: 15px !important;
    color: #64748B !important;
    line-height: 1.6 !important;
    margin: 0 !important;
    font-weight: 500 !important;
}

.page-footer-left {
    text-align: left !important;
    font-size: 14px !important;
    color: #64748B !important;
    font-weight: 500 !important;
    margin-top: 24px !important;
}

/* ---------------- Cột phải: Login Card nổi ---------------- */
.login-card-side {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 30px 60px 30px 20px !important;
    z-index: 5 !important;
    box-sizing: border-box !important;
}

.login-card {
    width: 420px !important;
    max-width: 100% !important;
    background: #FFFFFF !important;
    border-radius: 26px !important;
    padding: 40px 36px 32px !important;
    box-shadow: 0 20px 50px rgba(210, 160, 50, 0.15), 0 4px 16px rgba(0, 0, 0, 0.04) !important;
    border: 1.5px solid rgba(240, 230, 210, 0.7) !important;
    box-sizing: border-box !important;
    text-align: left !important;
}

.card-logo-wrap {
    text-align: center !important;
    margin-bottom: 16px !important;
}

.card-logo-wrap img {
    height: 42px !important;
    width: auto !important;
    max-width: 100% !important;
    object-fit: contain !important;
    display: inline-block !important;
}

.card-title {
    font-size: 26px !important;
    font-weight: 800 !important;
    color: #1E293B !important;
    text-align: center !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: -0.01em !important;
}

.card-subtitle {
    font-size: 13.5px !important;
    color: #64748B !important;
    text-align: center !important;
    line-height: 1.5 !important;
    margin: 0 0 22px 0 !important;
}

.form-error {
    display: flex !important;
    align-items: flex-start !important;
    gap: 8px !important;
    padding: 10px 14px !important;
    background: #FEF2F2 !important;
    border: 1px solid #FECACA !important;
    border-radius: 10px !important;
    color: #991B1B !important;
    font-size: 12.5px !important;
    line-height: 1.4 !important;
    margin-bottom: 14px !important;
}

.form-group {
    margin-bottom: 16px !important;
    text-align: left !important;
}

.form-label {
    display: block !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: #1E293B !important;
    margin-bottom: 6px !important;
}

.input-wrap {
    position: relative !important;
    width: 100% !important;
}

.input-icon {
    position: absolute !important;
    left: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: #EAA015 !important;
    pointer-events: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 2 !important;
}

.input-icon svg {
    width: 17px !important;
    height: 17px !important;
    stroke: #EAA015 !important;
    stroke-width: 2 !important;
}

.input-wrap input {
    width: 100% !important;
    height: 48px !important;
    padding: 0 16px 0 44px !important;
    font-family: inherit !important;
    font-size: 14px !important;
    color: #1E293B !important;
    background: #FFFFFF !important;
    border: 1.5px solid #F1E7D5 !important;
    border-radius: 12px !important;
    outline: none !important;
    transition: all 0.15s ease !important;
    box-sizing: border-box !important;
}

.input-wrap input:hover {
    border-color: #E2D4BC !important;
}

.input-wrap input:focus {
    border-color: #EAA015 !important;
    box-shadow: 0 0 0 3px rgba(234, 160, 21, 0.16) !important;
    background: #FFFFFF !important;
}

.input-wrap input::placeholder {
    color: #9CA3AF !important;
}

.pwd-toggle {
    position: absolute !important;
    right: 12px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    background: transparent !important;
    border: none !important;
    padding: 6px !important;
    cursor: pointer !important;
    color: #9CA3AF !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 6px !important;
    transition: color 0.15s ease !important;
    z-index: 3 !important;
}

.pwd-toggle:hover {
    color: #EAA015 !important;
}

.pwd-toggle svg {
    width: 17px !important;
    height: 17px !important;
    stroke: currentColor !important;
    stroke-width: 2 !important;
}

.form-options {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin: 14px 0 20px 0 !important;
    font-size: 13px !important;
}

.cbx {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    cursor: pointer !important;
    user-select: none !important;
    font-size: 13px !important;
    color: #1E293B !important;
}

.cbx input {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

.cbx .box {
    width: 18px !important;
    height: 18px !important;
    border: 1.5px solid #F1E7D5 !important;
    border-radius: 5px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    background: #FFFFFF !important;
    box-sizing: border-box !important;
    transition: all 0.15s ease !important;
}

.cbx input:checked + .box {
    background: #EAA015 !important;
    border-color: #EAA015 !important;
}

.cbx .box svg {
    width: 12px !important;
    height: 12px !important;
    stroke: #FFFFFF !important;
    stroke-width: 3 !important;
    fill: none !important;
    opacity: 0 !important;
    transition: opacity 0.15s ease !important;
}

.cbx input:checked + .box svg {
    opacity: 1 !important;
}

.cbx-label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #1E293B !important;
}

.form-forgot {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #EAA015 !important;
    text-decoration: none !important;
    transition: color 0.15s ease !important;
    white-space: nowrap !important;
}

.form-forgot:hover {
    color: #D97706 !important;
    text-decoration: underline !important;
}

/* Ẩn hoàn toàn các nút thừa */
.field-password a,
.field-password .small,
a[href*="reset_password"],
a[href*="signup"],
button[value*="become"],
.btn-link[value*="become"],
.o_login_auth {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    pointer-events: none !important;
    overflow: hidden !important;
}

.form-submit-wrap {
    margin-top: 6px !important;
}

.btn-submit {
    width: 100% !important;
    height: 50px !important;
    background: #EAA015 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 25px !important;
    font-family: inherit !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(234, 160, 21, 0.32) !important;
    padding: 0 !important;
}

.btn-submit:hover {
    background: #D97706 !important;
    box-shadow: 0 6px 18px rgba(217, 119, 6, 0.42) !important;
    transform: translateY(-1px) !important;
}

.btn-submit:active {
    transform: translateY(0) !important;
}

.btn-submit svg {
    width: 17px !important;
    height: 17px !important;
    stroke: #FFFFFF !important;
    fill: none !important;
    stroke-width: 2 !important;
}

.divider-or {
    display: flex !important;
    align-items: center !important;
    text-align: center !important;
    margin: 16px 0 14px 0 !important;
    color: #9CA3AF !important;
    font-size: 12.5px !important;
}

.divider-or::before, .divider-or::after {
    content: '' !important;
    flex: 1 !important;
    border-bottom: 1px solid #E5E7EB !important;
}

.divider-or span {
    padding: 0 12px !important;
}

.demo-btn-wrap {
    width: 100% !important;
}

.btn-demo {
    width: 100% !important;
    height: 42px !important;
    border: 1.5px solid #FDE68A !important;
    background: #FFFDF9 !important;
    border-radius: 24px !important;
    font-family: inherit !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    color: #EAA015 !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    transition: all 0.15s ease !important;
    padding: 0 !important;
}

.btn-demo:hover {
    background: #FFFBEB !important;
    border-color: #EAA015 !important;
}

.btn-demo svg {
    width: 16px !important;
    height: 16px !important;
    stroke: #EAA015 !important;
    fill: none !important;
    stroke-width: 2 !important;
}

.card-footer {
    text-align: center !important;
    font-size: 12px !important;
    color: #9CA3AF !important;
    margin-top: 20px !important;
}

/* ==================== RESPONSIVE ENGINE (MỌI MÀN HÌNH) ==================== */

/* 1. Ultra-wide & 4K Displays (> 1600px) */
@media (min-width: 1600px) {
    .presentation-side {
        padding: 56px 80px 48px !important;
    }
    .core-content-center {
        max-width: 1140px !important;
    }
    .value-card {
        max-width: 350px !important;
        padding: 34px 30px 30px !important;
    }
    .login-card {
        max-width: 450px !important;
        padding: 46px 40px 36px !important;
    }
}

/* 2. Laptop nhỏ & Tablet ngang (992px - 1199px) */
@media (max-width: 1199px) and (min-width: 992px) {
    .presentation-side {
        padding: 32px 36px 28px !important;
    }
    .top-brand-logo img,
    .brand-logo-img {
        height: 48px !important;
    }
    .core-title {
        font-size: 44px !important;
    }
    .core-subtitle {
        font-size: 15.5px !important;
        max-width: 640px !important;
    }
    .values-row {
        gap: 16px !important;
    }
    .value-card {
        flex: 1 1 200px !important;
        max-width: 280px !important;
        padding: 22px 18px 20px !important;
    }
    .value-icon-box {
        width: 44px !important;
        height: 44px !important;
    }
    .value-icon-box svg {
        width: 22px !important;
        height: 22px !important;
    }
    .value-title {
        font-size: 18px !important;
    }
    .value-desc {
        font-size: 13px !important;
    }
    .login-card-side {
        padding: 24px 36px 24px 20px !important;
        max-width: 460px !important;
    }
    .login-card {
        max-width: 390px !important;
        padding: 34px 28px 26px !important;
    }
}

/* 3. Tablet & Màn hình trung bình (768px - 991px): Chuyển bố cục dọc, BA DÒNG XUẤT HIỆN ĐẦY ĐỦ */
@media (max-width: 991px) {
    .login-wrapper {
        flex-direction: column !important;
        height: auto !important;
        min-height: 100vh !important;
        overflow-y: auto !important;
        padding-bottom: 40px !important;
        background-position: center top !important;
    }

    .presentation-side {
        flex: none !important;
        width: 100% !important;
        padding: 32px 32px 16px !important;
        align-items: center !important;
        text-align: center !important;
    }

    .top-brand-logo {
        align-self: flex-start !important;
        margin-bottom: 24px !important;
    }

    .top-brand-logo img,
    .brand-logo-img {
        height: 48px !important;
    }

    .core-content-center {
        margin: 0 auto !important;
        padding: 10px 0 20px !important;
        max-width: 640px !important;
    }

    .core-heading-wrap {
        margin-bottom: 24px !important;
    }

    .core-title {
        font-size: 38px !important;
        gap: 12px !important;
    }

    .title-gold-line {
        width: 90px !important;
        height: 4px !important;
        margin: 10px auto 0 !important;
    }

    .core-subtitle {
        font-size: 16px !important;
        max-width: 580px !important;
        margin-top: 14px !important;
    }

    /* YÊU CẦU BẮT BUỘC MỤC 4: Ba dòng nội dung xuất hiện đầy đủ theo bố cục dọc */
    .values-row {
        flex-direction: column !important;
        align-items: center !important;
        gap: 14px !important;
        width: 100% !important;
        max-width: 540px !important;
        margin: 22px auto 0 !important;
    }

    .value-card {
        width: 100% !important;
        max-width: 100% !important;
        flex: none !important;
        padding: 18px 22px !important;
        border-radius: 18px !important;
        box-shadow: 0 6px 20px rgba(220, 180, 100, 0.12) !important;
        transform: none !important;
    }

    .value-card:hover {
        transform: translateY(-2px) !important;
    }

    .value-card-header {
        margin-bottom: 6px !important;
        gap: 12px !important;
    }

    .value-icon-box {
        width: 44px !important;
        height: 44px !important;
        border-radius: 12px !important;
    }

    .value-icon-box svg {
        width: 22px !important;
        height: 22px !important;
    }

    .value-divider {
        width: 3px !important;
        height: 26px !important;
    }

    .value-title {
        font-size: 18px !important;
    }

    .value-desc {
        font-size: 14px !important;
        line-height: 1.5 !important;
    }

    .page-footer-left {
        display: none !important;
    }

    .login-card-side {
        width: 100% !important;
        max-width: 100% !important;
        padding: 16px 24px 32px !important;
    }

    .login-card {
        width: 100% !important;
        max-width: 480px !important;
        margin: 0 auto !important;
        padding: 36px 32px 28px !important;
    }
}

/* 4. Mobile & Cửa sổ nhỏ (< 768px): BA DÒNG NỘI DUNG GỌN GÀNG, ĐẦY ĐỦ */
@media (max-width: 767px) {
    .presentation-side {
        padding: 24px 18px 12px !important;
    }

    .top-brand-logo {
        margin-bottom: 16px !important;
    }

    .top-brand-logo img,
    .brand-logo-img {
        height: 42px !important;
    }

    .core-title {
        font-size: 28px !important;
        gap: 8px !important;
    }

    .title-gold-line {
        width: 75px !important;
        height: 3.5px !important;
        margin: 8px auto 0 !important;
    }

    .core-subtitle {
        font-size: 14.5px !important;
        line-height: 1.55 !important;
        margin-top: 12px !important;
        padding: 0 4px !important;
    }

    /* BA DÒNG NỘI DUNG HIỂN THỊ ĐẦY ĐỦ TRÊN MOBILE (Tận Tâm, Đồng Hành, Bền Vững) */
    .values-row {
        flex-direction: column !important;
        align-items: stretch !important;
        gap: 11px !important;
        width: 100% !important;
        max-width: 440px !important;
        margin: 18px auto 0 !important;
    }

    .value-card {
        width: 100% !important;
        max-width: 100% !important;
        padding: 14px 16px !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 14px rgba(220, 180, 100, 0.1) !important;
    }

    .value-card-header {
        margin-bottom: 5px !important;
        gap: 10px !important;
    }

    .value-icon-box {
        width: 38px !important;
        height: 38px !important;
        border-radius: 10px !important;
    }

    .value-icon-box svg {
        width: 19px !important;
        height: 19px !important;
    }

    .value-divider {
        width: 2.5px !important;
        height: 22px !important;
    }

    .value-title {
        font-size: 16.5px !important;
    }

    .value-desc {
        font-size: 13.5px !important;
        line-height: 1.45 !important;
    }

    .login-card-side {
        padding: 12px 16px 28px !important;
    }

    .login-card {
        width: 100% !important;
        max-width: 420px !important;
        padding: 28px 20px 24px !important;
        border-radius: 20px !important;
    }

    .card-title {
        font-size: 24px !important;
    }

    .card-subtitle {
        font-size: 13px !important;
        margin-bottom: 18px !important;
    }

    .input-wrap input {
        height: 48px !important;
        font-size: 14px !important;
        padding-left: 44px !important;
    }

    .btn-submit {
        height: 48px !important;
        font-size: 15px !important;
    }

    .btn-demo {
        height: 40px !important;
        font-size: 13px !important;
    }
}

/* 5. Mobile Siêu Nhỏ (320px - 374px) */
@media (max-width: 374px) {
    .presentation-side {
        padding: 18px 12px 10px !important;
    }

    .top-brand-logo img,
    .brand-logo-img {
        height: 36px !important;
    }

    .core-title {
        font-size: 24px !important;
        gap: 6px !important;
    }

    .core-subtitle {
        font-size: 13px !important;
    }

    .values-row {
        gap: 8px !important;
    }

    .value-card {
        padding: 11px 12px !important;
        border-radius: 12px !important;
    }

    .value-icon-box {
        width: 32px !important;
        height: 32px !important;
    }

    .value-icon-box svg {
        width: 16px !important;
        height: 16px !important;
    }

    .value-divider {
        height: 18px !important;
        width: 2px !important;
    }

    .value-title {
        font-size: 15px !important;
    }

    .value-desc {
        font-size: 12px !important;
        line-height: 1.4 !important;
    }

    .login-card-side {
        padding: 8px 12px 24px !important;
    }

    .login-card {
        padding: 22px 14px 18px !important;
        border-radius: 16px !important;
    }

    .card-title {
        font-size: 21px !important;
    }

    .card-subtitle {
        font-size: 12px !important;
        margin-bottom: 14px !important;
    }

    .input-wrap input {
        height: 44px !important;
        font-size: 13.5px !important;
        padding-left: 40px !important;
    }

    .input-icon {
        left: 10px !important;
    }

    .input-icon svg {
        width: 16px !important;
        height: 16px !important;
    }

    .btn-submit {
        height: 44px !important;
        font-size: 14px !important;
    }

    .btn-demo {
        height: 38px !important;
        font-size: 12.5px !important;
    }
}

/* 6. HiDPI & Retina Displays (2x, 3x pixel density) */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
    .login-wrapper {
        image-rendering: -webkit-optimize-contrast;
    }
    .brand-logo-img,
    .card-logo {
        image-rendering: -webkit-optimize-contrast;
    }
}

.lang-switcher-login {
    position: absolute !important;
    top: 18px !important;
    right: 18px !important;
    z-index: 10 !important;
}
.lang-switcher-login .lang-pill-group {
    display: inline-flex !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 20px !important;
    padding: 3px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    gap: 2px !important;
}
.lang-btn {
    display: inline-block !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    padding: 4px 10px !important;
    border-radius: 14px !important;
    text-decoration: none !important;
    color: #64748B !important;
    line-height: 1.2 !important;
    transition: all 0.2s ease !important;
}
.lang-btn.active {
    background: #EAA015 !important;
    color: #FFFFFF !important;
}
.lang-btn:hover:not(.active) {
    background: #F1F5F9 !important;
    color: #1E293B !important;
}
.login-card {
    position: relative !important;
}

]]>
        </style>
        <div class="login-wrapper">
            <!-- Khu vực bên trái: Trình bày Giá Trị Cốt Lõi -->
            <aside class="presentation-side">
                <!-- Logo TDB Solution (Hình 2) góc trên bên trái -->
                <div class="top-brand-logo">
                    <img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_logo2" alt="TDB Solution" class="brand-logo-img"/>
                </div>

                <!-- Khối nội dung chính giữa: Tiêu đề & 3 Card Giá trị cốt lõi -->
                <div class="core-content-center">
                    <div class="core-heading-wrap">
                        <h1 class="core-title">
                            <span class="word-navy">GIÁ TRỊ</span>
                            <span class="word-gold">CỐT LÕI</span>
                        </h1>
                        <div class="title-gold-line"/>
                        <p class="core-subtitle">
                            TDB Solution sáng tạo và đổi mới, mang đến khách hàng sự hài lòng<br/>
                            nhờ đồng hành và cung cấp dịch vụ chất lượng cao.
                        </p>
                    </div>

                    <!-- 3 Card Giá trị cốt lõi -->
                    <div class="values-row">
                        <!-- Card 1: Tận Tâm -->
                        <div class="value-card">
                            <div class="value-card-header">
                                <div class="value-icon-box">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-heart-handshake">
                                        <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                                        <path d="M12 5 9.04 7.96a2.17 2.17 0 0 0 0 3.08v0c.82.82 2.13.85 3 .07l2.07-1.9a2.82 2.82 0 0 1 3.79 0l2.96 2.66"/>
                                        <path d="m18 15-2-2"/>
                                        <path d="m15 18-2-2"/>
                                    </svg>
                                </div>
                                <div class="value-divider"/>
                                <h3 class="value-title">Tận Tâm</h3>
                            </div>
                            <p class="value-desc">
                                Tận tâm trong phục vụ,<br/>
                                tiên phong trong công nghệ.
                            </p>
                        </div>

                        <!-- Card 2: Đồng Hành -->
                        <div class="value-card">
                            <div class="value-card-header">
                                <div class="value-icon-box">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-users">
                                        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                                        <circle cx="9" cy="7" r="4"/>
                                        <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                                    </svg>
                                </div>
                                <div class="value-divider"/>
                                <h3 class="value-title">Đồng Hành</h3>
                            </div>
                            <p class="value-desc">
                                Đồng hành bền vững,<br/>
                                đổi mới không ngừng.
                            </p>
                        </div>

                        <!-- Card 3: Bền Vững -->
                        <div class="value-card">
                            <div class="value-card-header">
                                <div class="value-icon-box">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shield-check">
                                        <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>
                                        <path d="m9 12 2 2 4-4"/>
                                    </svg>
                                </div>
                                <div class="value-divider"/>
                                <h3 class="value-title">Bền Vững</h3>
                            </div>
                            <p class="value-desc">
                                Bền vững trong chiến lược,<br/>
                                bản lĩnh trong hành động.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Chân trang góc dưới bên trái -->
                <div class="page-footer-left">
                    © 2026 TDB-Solution · Phiên bản nội bộ
                </div>
            </aside>

            <!-- Khu vực bên phải: Login Card nổi -->
            <main class="login-card-side">
                <div class="login-card">
                    <!-- Bộ chuyển đổi ngôn ngữ EN <-> VI trên trang đăng nhập -->
                    <div class="lang-switcher-login">
                        <div class="lang-pill-group">
                            <a href="/web/session/switch_language_http?lang=vi_VN&amp;redirect=/web/login"
                               t-attf-class="lang-btn #{'active' if (request.env.context.get('lang') or 'vi_VN').startswith('vi') else ''}">
                                🇻🇳 VI
                            </a>
                            <a href="/web/session/switch_language_http?lang=en_US&amp;redirect=/web/login"
                               t-attf-class="lang-btn #{'active' if not (request.env.context.get('lang') or 'vi_VN').startswith('vi') else ''}">
                                🇬🇧 EN
                            </a>
                        </div>
                    </div>

                    <!-- Logo TDB Solution (Hình 2) trong Card -->
                    <div class="card-logo-wrap">
                        <img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_logo2" alt="TDB Solution" class="card-logo"/>
                    </div>

                    <h2 class="card-title">Đăng nhập</h2>
                    <p class="card-subtitle">Chào mừng trở lại! Vui lòng đăng nhập vào hệ thống TDB Solution.</p>

                    <!-- Form Đăng nhập cắm tại đây -->
                    <t t-out="0"/>

                    <!-- Chân Card -->
                    <div class="card-footer">
                        TDB Solution © 2026.
                    </div>
                </div>
            </main>
        </div>
    </t>
</t>"""
            if layout_target:
                layout_target.write({'arch_db': tdb_layout_arch})
                print("  [OK] Đã khôi phục web.login_layout chuẩn TDB Solution (đầy đủ CSS inline & logo & giá trị cốt lõi).")

            # 4. Cập nhật trực tiếp web.login với form chuẩn Odoo (không mã hóa, kèm nút Demo: admin)
            tdb_login_arch = """<t t-name="web.login">
    <t t-call="web.login_layout">
        <t t-set="title">Đăng nhập | TDB Solution</t>
        <form class="oe_login_form" role="form" t-attf-action="/web/login" method="post" onsubmit="sessionStorage.setItem('tdb_open_home_menu', 'true'); this.action = '/web/login' + location.hash;">
            <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>

            <div class="form-error" t-if="error" role="alert">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-alert-circle"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span><t t-out="error"/></span>
            </div>
            <div class="alert alert-success" t-if="message" role="status">
                <t t-out="message"/>
            </div>

            <!-- Tài khoản / Email -->
            <div class="form-group field-login">
                <label class="form-label" for="login">Tài khoản / Email</label>
                <div class="input-wrap">
                    <div class="input-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-mail">
                            <rect width="20" height="16" x="2" y="4" rx="2"/>
                            <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                        </svg>
                    </div>
                    <input id="login" name="login" t-att-value="login" placeholder="admin hoặc ban@tdbsolu" required="required" autofocus="autofocus" autocapitalize="off" autocomplete="username" class="form-control" type="text"/>
                </div>
            </div>

            <!-- Mật khẩu -->
            <div class="form-group field-password">
                <label class="form-label" for="password">Mật khẩu</label>
                <div class="input-wrap">
                    <div class="input-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-lock">
                            <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                        </svg>
                    </div>
                    <input id="password" name="password" placeholder="Nhập mật khẩu" required="required" autocomplete="current-password" maxlength="4096" type="password"/>
                    <button aria-label="Hiện mật khẩu" class="pwd-toggle" type="button" onclick="var p=document.getElementById('password');if(p)p.type=p.type==='password'?'text':'password';">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eye-off">
                            <path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/>
                            <path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/>
                            <path d="M17.479 17.499A10.75 10.75 0 0 1 2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.417-5.148"/>
                            <line x1="2" x2="22" y1="2" y2="22"/>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Ghi nhớ đăng nhập + Quên mật khẩu? -->
            <div class="form-options">
                <label class="cbx">
                    <input checked="checked" type="checkbox" name="remember"/>
                    <span class="box">
                        <svg viewBox="0 0 24 24">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </span>
                    <span class="cbx-label">Ghi nhớ đăng nhập</span>
                </label>
                <a class="form-forgot" href="/web/reset_password" t-if="debug">Quên mật khẩu?</a>
            </div>

            <input type="hidden" name="redirect" t-att-value="redirect"/>

            <!-- Nút Đăng nhập bo tròn -->
            <div class="form-submit-wrap">
                <button class="btn-submit" type="submit">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-log-in">
                        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                        <polyline points="10 17 15 12 10 7"/>
                        <line x1="15" x2="3" y1="12" y2="12"/>
                    </svg>
                    <span>Đăng nhập</span>
                </button>
            </div>

            <!-- Hoặc -->
            <div class="divider-or">
                <span>Hoặc</span>
            </div>

            <!-- Nút Demo: admin -->
            <div class="demo-btn-wrap">
                <button type="button" class="btn-demo" onclick="var l=document.getElementById('login'),p=document.getElementById('password');if(l)l.value='admin';if(p)p.value='MatKhauMoi';" title="Nhấp để tự động điền tài khoản demo">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-key-round">
                        <path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 1 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"/>
                        <circle cx="16.5" cy="7.5" fill="currentColor" r=".5"/>
                    </svg>
                    <span>Demo: admin</span>
                </button>
            </div>
        </form>
    </t>
</t>"""
            if login_target:
                login_target.write({'arch_db': tdb_login_arch})
                print("  [OK] Đã khôi phục web.login chuẩn Odoo (POST nguyên bản, không mã hóa, nút Demo MatKhauMoi).")

            # 5. Đảm bảo tài khoản admin luôn đăng nhập được với mật khẩu MatKhauMoi
            admin_user = env['res.users'].sudo().search([('login', '=', 'admin')], limit=1)
            if admin_user:
                admin_user.write({'password': 'MatKhauMoi'})
                print("  [OK] Đã đảm bảo mật khẩu tài khoản 'admin' là: MatKhauMoi")

            cr.commit()
        except Exception as e:
            cr.rollback()
            print(f"  [Lưu ý cấu hình đăng nhập]: {e}")


        # Xoa cache
        try:
            env.registry.clear_cache()
            cached_assets = env['ir.attachment'].search([
                '|', '|',
                ('url', '=like', '/web/assets/%'),
                ('url', '=like', '%assets_backend%'),
                ('name', '=like', '%.assets_%')
            ])
            if cached_assets:
                cached_assets.unlink()
        except Exception:
            pass
        cr.commit()

    print('\n>>> HOAN TAT KHOI PHUC GIAO DIEN DANG NHAP TDB SOLUTION!')
    print('Vui long tai lai trinh duyet (Ctrl + F5): http://192.168.103.8:8080/web/login')

if __name__ == '__main__':
    main()

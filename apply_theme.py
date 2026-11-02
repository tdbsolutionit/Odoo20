# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Kịch bản tự động hóa cấu hình giao diện B-ACE SME:
1. Bỏ toàn bộ danh mục menu (Trang chủ, Cửa hàng, Sự kiện, Khóa học, Tuyển dụng, Liên hệ) và Giỏ hàng theo Hình 1.
2. Thiết lập giao diện Đăng nhập (/web/login) chia 2 cột tỉ lệ 8:2 chuẩn theo Hình 2 (http://192.168.103.8:3000/login):
   - Cột trái (80%): Ảnh nền tập thể HD từ thư mục Picture (BG-TapThe.webp).
   - Cột phải (20%): Form đăng nhập B-ACE SME sang trọng, tối giản, bo góc chuẩn mực với nút gradient vàng đồng.
3. Xóa bỏ hoàn toàn các cấu hình cũ không còn phù hợp (Shop, Events, Jobs, ContactUs form, 3-column footer).
4. Điều hướng trang chủ (/) tự động chuyển hướng người dùng chưa đăng nhập sang /web/login.
"""
import base64
import os
import sys

def make_binary_value(raw_bytes, filename="tdb_logo.png"):
    """Tạo đối tượng nhị phân tương thích các phiên bản Odoo."""
    try:
        from odoo.tools import BinaryBytes
        return BinaryBytes(raw_bytes, filename=filename)
    except Exception:
        pass
    try:
        from odoo.orm.fields_binary import BinaryValue
        return BinaryValue(raw_bytes, filename=filename)
    except Exception:
        pass
    return base64.b64encode(raw_bytes)


# =============================================================================
# CÁC DỊCH VỤ CẤU HÌNH THEO YÊU CẦU MỚI
# =============================================================================

def setup_bace_root_redirection(env):
    """
    Yêu cầu: Nhập địa chỉ (/) thì qua thẳng trang đăng nhập (/web/login).
    - Cấu hình homepage_url = '/web/login' trên tất cả website.
    - Cập nhật view website.homepage có sẵn thẻ meta refresh và JS redirect tức thì.
    """
    print("\n>>> [1/7] Thiết lập tự động chuyển hướng trang chủ (/) sang /web/login...")
    for ws in env['website'].search([]):
        vals = {}
        if hasattr(ws, 'homepage_url'):
            vals['homepage_url'] = '/web/login'
        if vals:
            try:
                ws.write(vals)
                print(f"[OK] Đã thiết lập website '{ws.name}' homepage_url = '/web/login'")
            except Exception as e:
                print(f"Lưu ý homepage_url: {e}")

    hp_view = env.ref('website.homepage', raise_if_not_found=False)
    if hp_view:
        hp_arch = """<t t-name="website.homepage">
    <t t-call="web.layout">
        <t t-set="head">
            <meta http-equiv="refresh" content="0; url=/web/login"/>
            <script type="text/javascript">
                if (!window.location.pathname.startsWith('/web')) {
                    window.location.replace('/web/login');
                }
            </script>
        </t>
        <div style="display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;color:#64748b;">
            Đang chuyển hướng đến trang đăng nhập...
        </div>
    </t>
</t>"""
        try:
            hp_view.write({'arch_db': hp_arch})
            print("[OK] Đã cấu hình website.homepage tự động chuyển hướng sang /web/login!")
        except Exception as e:
            print(f"Lưu ý cấu hình website.homepage: {e}")


def setup_vietnamese_language(env):
    """Kích hoạt và nạp gói ngôn ngữ Tiếng Việt (vi_VN) làm mặc định."""
    print("\n>>> [2/7] Đảm bảo ngôn ngữ Tiếng Việt (vi_VN) được kích hoạt...")
    vi_lang = env['res.lang'].with_context(active_test=False).search([('code', '=', 'vi_VN')], limit=1)
    if vi_lang:
        if not vi_lang.active:
            vi_lang.write({'active': True})
        print(f"[OK] Ngôn ngữ Tiếng Việt sẵn sàng (id={vi_lang.id})")
    else:
        try:
            env['res.lang']._activate_lang('vi_VN')
            vi_lang = env['res.lang'].search([('code', '=', 'vi_VN')], limit=1)
            print("[OK] Đã kích hoạt vi_VN thành công!")
        except Exception as e:
            print(f"[Lưu ý vi_VN]: {e}")

    for ws in env['website'].search([]):
        vals = {}
        if vi_lang:
            if vi_lang.id not in ws.language_ids.ids:
                vals['language_ids'] = [(4, vi_lang.id)]
            vals['default_lang_id'] = vi_lang.id
        if vals:
            ws.write(vals)

    for ref_key in ['base.user_admin', 'base.partner_admin', 'base.public_user', 'base.public_partner']:
        rec = env.ref(ref_key, raise_if_not_found=False)
        if rec and hasattr(rec, 'lang'):
            rec.write({'lang': 'vi_VN'})


def cleanup_obsolete_views(env):
    """
    Xóa bỏ các view và cấu hình tùy biến cũ không còn phù hợp với yêu cầu mới:
    - Khôi phục website.layout về bản gốc sạch sẽ.
    - Xóa các bản COW view bị rách tag gây tràn text ở đầu trang.
    - Khôi phục các trang homepage, contactus, jobs, footer về mặc định Odoo.
    """
    print("\n>>> [2/6] Dọn dẹp các view cũ và khôi phục template hệ thống...")
    
    # 1. Làm sạch website.layout
    layout_views = env['ir.ui.view'].search([('key', '=', 'website.layout')])
    for lv in layout_views:
        if lv.website_id:
            try:
                lv.unlink()
                print(f"[OK] Đã xóa COW view website.layout (id={lv.id})")
                continue
            except Exception as e:
                print(f"Lưu ý xóa COW layout: {e}")

        parent = env.ref('portal.frontend_layout', raise_if_not_found=False) or env.ref('web.frontend_layout', raise_if_not_found=False)
        if parent and lv.inherit_id != parent:
            try:
                lv.write({'inherit_id': parent.id, 'mode': 'extension'})
            except Exception:
                pass

        if hasattr(lv, 'reset_arch'):
            try:
                lv.reset_arch(mode='hard')
                print(f"[OK] Đã khôi phục view {lv.key} (id={lv.id}) về nguyên bản sạch sẽ!")
            except Exception as e:
                print(f"Lưu ý reset_arch layout: {e}")

    # 2. Xóa các view rác bị tràn text đầu trang
    corrupted_views = env['ir.ui.view'].search([
        '|', '|', '|',
        ('arch_db', 'ilike', '%extra_items_toggle_aria_label%'),
        ('arch_db', 'ilike', '%Footer Copyright not editable%'),
        ('arch_db', 'ilike', '%header_visible%main_object%'),
        ('arch_db', 'ilike', '%footer_visible%main_object%'),
    ])
    for cv in corrupted_views:
        if cv.key == 'website.layout' and not cv.website_id:
            continue
        if cv.website_id:
            try:
                cv.unlink()
                print(f"[OK] Đã xóa COW view lỗi id={cv.id}")
            except Exception:
                pass
        elif hasattr(cv, 'reset_arch'):
            try:
                cv.reset_arch(mode='hard')
            except Exception:
                pass

    # 3. Khôi phục các view footer, contactus, jobs về mặc định
    for v_key in [
        'website.footer_custom',
        'website.template_footer_default',
        'website.contactus',
        'website_hr_recruitment.index',
        'website.homepage',
    ]:
        for v in env['ir.ui.view'].search([('key', '=', v_key)]):
            if hasattr(v, 'reset_arch'):
                try:
                    v.reset_arch(mode='hard')
                    print(f"[OK] Đã khôi phục view '{v_key}' về mặc định Odoo")
                except Exception:
                    pass

    # Xóa view 1953 nếu có
    v1953 = env['ir.ui.view'].browse(1953)
    if v1953.exists() and hasattr(v1953, 'reset_arch'):
        try:
            v1953.reset_arch(mode='hard')
        except Exception:
            pass


def remove_all_menus_and_cart(env):
    """
    Yêu cầu Hình 1: Bỏ hết các mục menu điều hướng (Trang chủ, Cửa hàng, Sự kiện,
    Khóa học, Tuyển dụng, Liên hệ) và bỏ nút Giỏ hàng 🛒.
    """
    print("\n>>> [3/6] Xóa toàn bộ danh mục Menu và nút Giỏ hàng theo yêu cầu Hình 1...")
    
    # 1. Xóa toàn bộ các menu con trên thanh điều hướng website
    menu_model = env['website.menu']
    for ws in env['website'].search([]):
        if not ws.menu_id:
            continue
        child_menus = menu_model.search([('parent_id', '=', ws.menu_id.id)])
        for m in child_menus:
            print(f"[XÓA MENU] Đã xóa menu: '{m.name}' ({m.url})")
            m.unlink()

    # Xóa cả các menu rác độc lập theo tên
    for old_m in menu_model.search([
        ('name', 'in', [
            'Trang chủ', 'Cửa hàng', 'Sự kiện', 'Khóa học', 'Tuyển dụng', 'Liên hệ',
            'Home', 'Shop', 'Events', 'Courses', 'Jobs', 'Contact Us'
        ])
    ]):
        try:
            print(f"[XÓA MENU CŨ] Đã xóa menu: '{old_m.name}'")
            old_m.unlink()
        except Exception:
            pass

    # 2. Vô hiệu hóa nút Giỏ hàng và các view liên quan đến giỏ hàng
    for cv in env['ir.ui.view'].search([
        '|', '|',
        ('key', '=', 'website_sale.header_cart_link'),
        ('key', '=', 'website_sale.template_header_default'),
        ('key', 'ilike', '%header_cart%'),
    ]):
        if cv.active:
            cv.write({'active': False})
            print(f"[OK] Đã vô hiệu hóa nút Giỏ hàng: {cv.key or cv.id}")

    # Gỡ bỏ li.o_wsale_my_cart khỏi tất cả các header view nếu có
    for hv in env['ir.ui.view'].search([('key', 'in', ['website.template_header_default', 'website.default_header'])]):
        h_arch = hv.arch_db or ''
        if 'o_wsale_my_cart' in h_arch:
            import re
            h_clean = re.sub(r'<li[^>]*class=\"[^\"]*o_wsale_my_cart[^\"]*\"[^>]*>.*?</li>', '', h_arch, flags=re.DOTALL)
            try:
                hv.write({'arch_db': h_clean})
                print(f"[OK] Đã loại bỏ hoàn toàn thẻ giỏ hàng khỏi {hv.key}")
            except Exception as e:
                print(f"Lưu ý làm sạch header: {e}")


def setup_picture_attachments(env, odoo_dir, current_dir):
    """
    Nạp ảnh tập thể trong thư mục Picture (BG-TapThe.webp) vào Odoo Attachment
    để hiển thị sắc nét ở cột trái (80%) trên trang Đăng nhập.
    """
    print("\n>>> [4/6] Nạp ảnh tập thể từ thư mục Picture vào hệ thống...")
    search_dirs = [
        os.path.join(odoo_dir, 'Picture'),
        os.path.join(current_dir, '..', '..', 'Picture'),
        os.path.join(current_dir, 'Picture'),
        os.path.join(odoo_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img'),
        r'C:\odoo20\odoo\Picture',
    ]

    for bg_filename in ['BG-TapThe.webp', 'BG-TapThe.jpg']:
        found_path = None
        for s_dir in search_dirs:
            candidate = os.path.join(s_dir, bg_filename)
            if os.path.exists(candidate):
                found_path = candidate
                break

        if found_path and os.path.exists(found_path):
            with open(found_path, 'rb') as f:
                raw_bytes = f.read()

            b64_data = base64.b64encode(raw_bytes).decode('ascii')
            mimetype = 'image/webp' if bg_filename.endswith('.webp') else 'image/jpeg'

            att_model = env['ir.attachment']
            att = att_model.search([('url', '=', f'/tdb_website_custom/static/src/img/{bg_filename}')], limit=1)
            vals = {
                'name': bg_filename,
                'type': 'binary',
                'datas': b64_data,
                'mimetype': mimetype,
                'public': True,
                'url': f'/tdb_website_custom/static/src/img/{bg_filename}',
            }
            if att:
                att.write(vals)
            else:
                att_model.create(vals)
            print(f"[OK] Đã nạp thành công '{bg_filename}' vào ir.attachment!")


def apply_bace_login_interface(env, current_dir):
    """
    Yêu cầu Hình 2: Áp dụng giao diện Đăng nhập B-ACE SME chia 2 cột tỉ lệ 8:2
    chuẩn theo http://192.168.103.8:3000/login
    Cập nhật trực tiếp web.login_layout và web.login mà không dùng xpath kế thừa
    để tránh hoàn toàn lỗi 'cannot be located in parent view' khi website được cài đặt.
    """
    print("\n>>> [5/6] Áp dụng giao diện Đăng nhập B-ACE SME tỉ lệ 8:2...")

    View = env['ir.ui.view']

    # 1. Gỡ bỏ các view kế thừa cũ đã tạo trước đó để tránh xung đột xpath
    for xml_key in ['tdb_website_custom.bace_login_layout', 'tdb_website_custom.bace_login_form']:
        for v in View.search([('key', '=', xml_key)]):
            try:
                v.unlink()
                print(f"[OK] Đã gỡ bỏ view kế thừa cũ '{xml_key}' (id={v.id})")
            except Exception:
                try:
                    v.write({'active': False})
                except Exception:
                    pass

    # Xóa bản ghi trong ir.model.data nếu có
    imd_records = env['ir.model.data'].search([
        ('module', '=', 'tdb_website_custom'),
        ('name', 'in', ['bace_login_layout', 'bace_login_form'])
    ])
    if imd_records:
        imd_records.unlink()

    # 2. Xóa các COW view của web.login_layout hoặc web.login (nếu có)
    cow_views = View.search([
        ('key', 'in', ['web.login_layout', 'web.login']),
        ('website_id', '!=', False)
    ])
    for cv in cow_views:
        try:
            cv.unlink()
            print(f"[OK] Đã xóa COW view '{cv.key}' (id={cv.id})")
        except Exception:
            pass

    # 3. Vô hiệu hóa website.login_layout và tất cả các view con kế thừa web.login_layout
    layout_target = env.ref('web.login_layout', raise_if_not_found=False)
    if layout_target:
        child_views = View.search([
            ('inherit_id', '=', layout_target.id),
            ('id', '!=', layout_target.id),
            ('active', '=', True)
        ])
        for cv in child_views:
            try:
                cv.write({'active': False})
                print(f"[OK] Đã vô hiệu hóa view con kế thừa web.login_layout: {cv.key or cv.id} ({cv.name})")
            except Exception as e:
                print(f"Lưu ý vô hiệu hóa view con {cv.id}: {e}")

        # Cập nhật trực tiếp arch_db của web.login_layout theo tỉ lệ 8:2 chuẩn xác
        # Sử dụng web.layout (thay vì web.frontend_layout) để ngăn hoàn toàn website.layout chèn header/footer
        # Nhúng kèm khối style CSS trực tiếp qua CDATA để giao diện ăn ngay lập tức không phụ thuộc asset bundle
        bace_layout_arch = """<t t-name="web.login_layout">
    <t t-call="web.layout">
        <t t-set="html_data" t-value="{'style': 'height: 100%;'}"/>
        <t t-set="body_classname" t-value="'bace-login-body'"/>
        <t t-set="head">
            <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
            <style>
<![CDATA[
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background: #ffffff !important;
    overflow-x: hidden !important;
}
#top, #bottom, header, footer, .o_header_standard, .o_footer_copyright, .oe_website_login_container > .container {
    display: none !important;
}
.login-grid {
    display: grid !important;
    grid-template-columns: 8fr 2fr !important;
    min-height: 100vh !important;
    width: 100vw !important;
    margin: 0 !important;
    padding: 0 !important;
    background: #ffffff !important;
}
.login-grid .hero-side {
    background-color: #0F1117 !important;
    background-image: url('/tdb_website_custom/static/src/img/BG-TapThe.webp') !important;
    background-size: cover !important;
    background-position: center center !important;
    background-repeat: no-repeat !important;
    position: relative !important;
    overflow: hidden !important;
    min-height: 100vh !important;
}
.login-grid .hero-side::before {
    content: "" !important;
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(180deg, rgba(15, 17, 23, 0.05) 0%, rgba(15, 17, 23, 0.25) 100%) !important;
    pointer-events: none !important;
}
.login-grid .form-side {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    padding: 40px 28px !important;
    background: #ffffff !important;
    position: relative !important;
    box-sizing: border-box !important;
    box-shadow: -10px 0 30px rgba(0, 0, 0, 0.04) !important;
    min-height: 100vh !important;
}
.form-inner {
    width: 100% !important;
    max-width: 360px !important;
    margin: 0 auto !important;
}
.mobile-logo {
    display: none;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
}
.mobile-logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 11px;
    background: linear-gradient(135deg, #C9A961, #A8894A);
    box-shadow: 0 8px 20px rgba(201, 169, 97, 0.3);
}
.mobile-logo-name {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.02em;
}
.form-header {
    margin-bottom: 28px !important;
    text-align: left !important;
}
.form-title {
    font-size: 28px !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: #0a0e1a !important;
    margin: 0 0 8px !important;
    line-height: 1.15 !important;
}
.form-subtitle {
    font-size: 13.5px !important;
    color: #64748b !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}
.form-error {
    display: flex !important;
    align-items: flex-start !important;
    gap: 10px !important;
    padding: 10px 14px !important;
    background: #fef2f2 !important;
    border: 1px solid #fecaca !important;
    border-radius: 10px !important;
    color: #991b1b !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
    margin-bottom: 18px !important;
}
.form-group {
    margin-bottom: 18px !important;
    text-align: left !important;
}
.form-label {
    display: block !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #0f172a !important;
    margin-bottom: 7px !important;
    letter-spacing: -0.005em !important;
}
.input-wrap {
    position: relative !important;
    width: 100% !important;
}
.input-wrap .icon {
    position: absolute !important;
    left: 15px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: #94a3b8 !important;
    pointer-events: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 2 !important;
}
.input-wrap .icon svg {
    width: 16px !important;
    height: 16px !important;
    stroke: #94a3b8 !important;
    fill: none !important;
}
.input-wrap input {
    width: 100% !important;
    height: 48px !important;
    padding: 0 16px 0 44px !important;
    font-family: inherit !important;
    font-size: 14px !important;
    color: #0f172a !important;
    background: #ffffff !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    outline: none !important;
    transition: all 0.15s ease !important;
    box-sizing: border-box !important;
}
.input-wrap input:hover {
    border-color: #cbd5e1 !important;
}
.input-wrap input:focus {
    border-color: #C9A961 !important;
    box-shadow: 0 0 0 4px rgba(201, 169, 97, 0.15) !important;
}
.pwd-toggle {
    position: absolute !important;
    right: 10px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 32px !important;
    height: 32px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 7px !important;
    color: #94a3b8 !important;
    background: transparent !important;
    border: none !important;
    cursor: pointer !important;
    padding: 0 !important;
    z-index: 2 !important;
}
.pwd-toggle:hover {
    color: #0f172a !important;
    background: #f1f5f9 !important;
}
.pwd-toggle svg {
    width: 16px !important;
    height: 16px !important;
    stroke: currentColor !important;
    fill: none !important;
}
.form-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    gap: 12px !important;
    margin-bottom: 22px !important;
}
.cbx {
    position: relative !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    cursor: pointer !important;
    user-select: none !important;
    font-size: 13px !important;
    color: #0f172a !important;
}
.cbx input {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
.cbx .box {
    width: 18px !important;
    height: 18px !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 5px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    background: #ffffff !important;
    box-sizing: border-box !important;
}
.cbx input:checked + .box {
    background: #C9A961 !important;
    border-color: #C9A961 !important;
}
.cbx .box svg {
    width: 12px !important;
    height: 12px !important;
    stroke: #ffffff !important;
    stroke-width: 3 !important;
    fill: none !important;
    opacity: 0 !important;
}
.cbx input:checked + .box svg {
    opacity: 1 !important;
}
.form-forgot {
    font-size: 12.5px !important;
    font-weight: 500 !important;
    color: #C9A961 !important;
    text-decoration: none !important;
    white-space: nowrap !important;
}
.form-forgot:hover {
    color: #A8894A !important;
    text-decoration: underline !important;
}
.btn-submit {
    width: 100% !important;
    height: 48px !important;
    background: linear-gradient(135deg, #C9A961, #A8894A) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: inherit !important;
    font-size: 14.5px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    box-shadow: 0 4px 12px rgba(201, 169, 97, 0.3) !important;
    padding: 0 !important;
}
.btn-submit:hover {
    box-shadow: 0 8px 24px rgba(201, 169, 97, 0.45) !important;
    transform: translateY(-1px) !important;
}
.btn-submit svg {
    width: 16px !important;
    height: 16px !important;
    stroke: #ffffff !important;
    fill: none !important;
    stroke-width: 2 !important;
}
.demo-box {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    margin-top: 24px !important;
    padding: 10px 14px !important;
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    font-size: 12.5px !important;
    color: #475569 !important;
    line-height: 1.5 !important;
}
.demo-box-icon {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 32px !important;
    height: 32px !important;
    border-radius: 8px !important;
    background: #FAF5E6 !important;
    color: #A8894A !important;
    flex-shrink: 0 !important;
}
.demo-box-icon svg {
    width: 16px !important;
    height: 16px !important;
    stroke: currentColor !important;
    fill: none !important;
}
.demo-box-text strong {
    color: #0f172a !important;
    font-weight: 600 !important;
}
.demo-box code {
    background: #ffffff !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-family: ui-monospace, SF Mono, monospace !important;
    font-size: 11.5px !important;
    color: #A8894A !important;
    border: 1px solid #e2e8f0 !important;
}
.form-footer {
    text-align: center !important;
    font-size: 12px !important;
    color: #94a3b8 !important;
    margin-top: 24px !important;
}
@media (max-width: 1024px) {
    .login-grid {
        grid-template-columns: 1fr !important;
    }
    .login-grid .hero-side {
        display: none !important;
    }
    .login-grid .form-side {
        padding: 48px 24px !important;
    }
    .mobile-logo {
        display: flex !important;
    }
}
]]>
            </style>
        </t>
        <div class="login-grid">
            <!-- Cột trái (80%): Ảnh nền tập thể HD từ thư mục Picture -->
            <aside class="hero-side">
                <div class="hero-image-overlay"/>
            </aside>

            <!-- Cột phải (20%): Form đăng nhập B-ACE SME -->
            <main class="form-side">
                <div class="form-inner">
                    <div class="mobile-logo">
                        <div class="mobile-logo-icon">
                            <svg aria-hidden="true" class="lucide lucide-layers" fill="none" height="20" stroke="#fff" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="20" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"/>
                                <path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/>
                                <path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/>
                            </svg>
                        </div>
                        <span class="mobile-logo-name">B-ACE</span>
                    </div>

                    <div class="form-header">
                        <h2 class="form-title">Đăng nhập</h2>
                        <p class="form-subtitle">Chào mừng trở lại! Vui lòng đăng nhập để tiếp tục.</p>
                    </div>

                    <!-- Vị trí cắm form đăng nhập -->
                    <t t-out="0"/>

                    <div class="demo-box">
                        <div class="demo-box-icon">
                            <svg aria-hidden="true" class="lucide lucide-key-round" fill="none" height="16" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg">
                                <path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 1 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"/>
                                <circle cx="16.5" cy="7.5" fill="currentColor" r=".5"/>
                            </svg>
                        </div>
                        <div class="demo-box-text">
                            <strong>Demo:</strong>
                            <code onclick="var l=document.getElementById('login'),p=document.getElementById('password');if(l)l.value='admin@b-ace.vn';if(p)p.value='password';" style="cursor:pointer;" title="Nhấp để điền">admin@b-ace.vn</code>
                            <span style="margin:0 4px;color:#cbd5e1">&#183;</span>
                            <code onclick="var l=document.getElementById('login'),p=document.getElementById('password');if(l)l.value='admin@b-ace.vn';if(p)p.value='password';" style="cursor:pointer;" title="Nhấp để điền">password</code>
                        </div>
                    </div>

                    <p class="form-footer">
                        B-ACE © 2026 · Phiên bản nội bộ
                    </p>
                </div>
            </main>
        </div>
    </t>
</t>"""
        try:
            layout_target.write({'arch_db': bace_layout_arch})
            print("[OK] Đã cập nhật trực tiếp web.login_layout chuẩn B-ACE SME (tỉ lệ 8:2)!")
        except Exception as e:
            print(f"[CẢNH BÁO web.login_layout]: {e}")

    # 4. Cập nhật trực tiếp web.login
    login_target = env.ref('web.login', raise_if_not_found=False)
    if login_target:
        bace_login_arch = """<t t-name="web.login">
    <t t-call="web.login_layout">
        <t t-set="title">Đăng nhập | B-ACE SME</t>
        <form class="oe_login_form" role="form" t-attf-action="/web/login" method="post" onsubmit="this.action = '/web/login' + location.hash">
            <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>

            <div class="form-error" t-if="error" role="alert">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-alert-circle"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span><t t-out="error"/></span>
            </div>
            <div class="alert alert-success" t-if="message" role="status">
                <t t-out="message"/>
            </div>

            <div class="form-group field-login">
                <label class="form-label" for="login">Email</label>
                <div class="input-wrap">
                    <svg aria-hidden="true" class="lucide lucide-mail icon" fill="none" height="16" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg">
                        <path d="m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7"/>
                        <rect height="16" rx="2" width="20" x="2" y="4"/>
                    </svg>
                    <input id="login" name="login" t-att-value="login" placeholder="ban@congty.com" required="required" autofocus="autofocus" autocapitalize="off" autocomplete="username" class="form-control" type="text"/>
                </div>
            </div>

            <div class="form-group field-password">
                <label class="form-label" for="password">Mật khẩu</label>
                <div class="input-wrap">
                    <svg aria-hidden="true" class="lucide lucide-lock icon" fill="none" height="16" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg">
                        <rect height="11" rx="2" ry="2" width="18" x="3" y="11"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    <input id="password" name="password" placeholder="••••••••" required="required" autocomplete="current-password" maxlength="4096" style="padding-right:44px" type="password"/>
                    <button aria-label="Hiện mật khẩu" class="pwd-toggle" type="button" onclick="var p=document.getElementById('password');if(p)p.type=p.type==='password'?'text':'password';">
                        <svg aria-hidden="true" class="lucide lucide-eye" fill="none" height="16" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg">
                            <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </button>
                </div>
            </div>

            <div class="form-row">
                <label class="cbx">
                    <input checked="checked" type="checkbox" name="remember"/>
                    <span class="box">
                        <svg viewBox="0 0 24 24">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </span>
                    <span>Ghi nhớ đăng nhập</span>
                </label>
                <a href="/web/reset_password" class="form-forgot">Quên mật khẩu?</a>
            </div>

            <input type="hidden" name="redirect" t-att-value="redirect"/>

            <div class="oe_login_buttons">
                <button class="btn-submit" type="submit">
                    <svg aria-hidden="true" class="lucide lucide-log-in" fill="none" height="16" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg">
                        <path d="m10 17 5-5-5-5"/>
                        <path d="M15 12H3"/>
                        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                    </svg>
                    Đăng nhập
                </button>
                <t t-if="debug">
                    <div class="text-center mt-3">
                        <button type="submit" name="redirect" value="/web/become" class="btn btn-link btn-sm text-muted">Đăng nhập tài khoản Siêu Quản Trị (Superuser)</button>
                    </div>
                </t>
                <div class="o_login_auth"/>
            </div>
        </form>
    </t>
</t>"""
        try:
            login_target.write({'arch_db': bace_login_arch})
            print("[OK] Đã cập nhật trực tiếp web.login chuẩn B-ACE SME!")
        except Exception as e:
            print(f"[CẢNH BÁO web.login]: {e}")


def main():
    """Điểm khởi chạy chính kết nối ORM Odoo và điều phối các dịch vụ thiết lập giao diện."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == 'tdb_website_custom':
        odoo_dir = os.path.dirname(os.path.dirname(current_dir))
    else:
        odoo_dir = current_dir
        
    os.chdir(odoo_dir)
    sys.path.insert(0, odoo_dir)

    try:
        import odoo
        from odoo.tools import config
        try:
            from odoo.modules.registry import Registry
        except ImportError:
            from odoo.orm.registry import Registry
    except ImportError as e:
        print(f"Error importing odoo: {e}. Vui lòng chạy trong môi trường ảo của Odoo.")
        return

    config_path = os.path.join(odoo_dir, 'odoo.conf')
    if not os.path.exists(config_path):
        config_path = 'odoo.conf'

    print(">>> Đang kết nối database odoo20...")
    try:
        config.parse_config(['-c', config_path, '-d', 'odoo20'], setup_logging=False)
    except TypeError:
        config.parse_config(['-c', config_path, '-d', 'odoo20'])
    
    registry = Registry('odoo20')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'no_vat_validation': True})

        # Thực thi tuần tự các phân hệ
        setup_bace_root_redirection(env)
        setup_vietnamese_language(env)
        cleanup_obsolete_views(env)
        remove_all_menus_and_cart(env)
        setup_picture_attachments(env, odoo_dir, current_dir)
        apply_bace_login_interface(env, current_dir)

        # Xóa cache QWeb và commit thay đổi vào PostgreSQL
        try:
            env.registry.clear_cache()
            print("\n[OK] Đã xóa cache QWeb template và View cache")
        except Exception:
            pass

        # Xóa các asset cache compiled trong ir.attachment để CSS mới ăn ngay
        try:
            cached_assets = env['ir.attachment'].search([
                ('name', 'ilike', '%.assets_%'),
                ('url', 'ilike', '/web/assets/%')
            ])
            if cached_assets:
                cached_assets.unlink()
                print(f"[OK] Đã làm mới {len(cached_assets)} bundle asset cache!")
        except Exception:
            pass

        cr.commit()
        print("\n" + "="*70)
        print(">>> HOÀN TẤT THÀNH CÔNG! GIAO DIỆN ĐĂNG NHẬP B-ACE SME TỈ LỆ 8:2 ĐÃ ÁP DỤNG! <<<")
        print("="*70)

if __name__ == '__main__':
    main()

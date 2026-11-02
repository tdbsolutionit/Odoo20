# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Kịch bản tự động hóa cấu hình giao diện TDB Solution:
Concept: Together We Grow – Natural Corporate Gold Theme
1. Tự động chuyển hướng trang chủ (/) sang thẳng trang đăng nhập (/web/login).
2. Bỏ toàn bộ danh mục menu (Trang chủ, Cửa hàng, Sự kiện, Khóa học, Tuyển dụng, Liên hệ) và Giỏ hàng.
3. Thiết lập giao diện Đăng nhập (/web/login) chia 2 cột tỉ lệ 73:27 chuẩn nhận diện Corporate Gold của TDB Solution:
   - Cột trái (73%): Ảnh tập thể TDB từ thư mục Picture (BG-TapThe.webp), kèm Card Logo & Slogan 'TOGETHER WE GROW' và thanh 3 Giá trị cốt lõi (Innovation, Collaboration, Development).
   - Cột phải (27%): Form đăng nhập TDB Solution sang trọng, tối giản, bo góc chuẩn mực với nút màu vàng nhận diện (#D9A441).
4. Xóa bỏ hoàn toàn các cấu hình cũ không còn phù hợp.
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
# CÁC DỊCH VỤ CẤU HÌNH THEO YÊU CẦU
# =============================================================================

def setup_tdb_root_redirection(env):
    """
    Yêu cầu: Nhập địa chỉ IP / domain (/) thì qua thẳng trang đăng nhập (/web/login).
    Xử lý đa tầng triệt để:
    1. Cấu hình website.rewrite: Chuyển hướng HTTP 302 từ '/' sang '/web/login' cho mọi website.
    2. Cấu hình website.page: Tắt header/footer trên tất cả trang chủ và nạp mã redirect.
    3. Ghi đè view website.homepage: Xóa COW view, ghi đè view gốc với script JS và meta refresh sang /web/login.
    4. Thêm view guard trên website.layout: Nếu trình duyệt truy cập '/' thì JS lập tức chuyển hướng sang /web/login.
    5. Đặt homepage_url trên website thành '/web/login'.
    """
    print("\n>>> [1/7] Thiết lập tự động chuyển hướng trang chủ (/) sang /web/login...")
    View = env['ir.ui.view']

    # 1. Cấu hình website.rewrite (HTTP 302 Redirect cấp HTTP Router)
    if 'website.rewrite' in env:
        Rewrite = env['website.rewrite']
        # Dọn dẹp các quy tắc rewrite cũ cho '/' để không xung đột
        old_rewrites = Rewrite.search([('url_from', '=', '/')])
        for rw in old_rewrites:
            try:
                rw.unlink()
            except Exception:
                pass

        # Tạo quy tắc toàn cục (website_id = False)
        try:
            r_global = Rewrite.create({
                'name': 'TDB Solution Redirect / to /web/login (Global)',
                'url_from': '/',
                'url_to': '/web/login',
                'redirect_type': '302',
                'active': True,
                'sequence': 1,
            })
            print(f"[OK] Đã tạo website.rewrite toàn cục (id={r_global.id}): '/' -> '/web/login' (302)")
        except Exception as e:
            print(f"[Lưu ý website.rewrite global]: {e}")

        # Tạo quy tắc cho từng website cụ thể
        for ws in env['website'].search([]):
            try:
                r_ws = Rewrite.create({
                    'name': f'TDB Solution Redirect / to /web/login ({ws.name})',
                    'url_from': '/',
                    'url_to': '/web/login',
                    'redirect_type': '302',
                    'website_id': ws.id,
                    'active': True,
                    'sequence': 1,
                })
                print(f"[OK] Đã tạo website.rewrite cho website '{ws.name}' (id={r_ws.id})")
            except Exception as e:
                print(f"[Lưu ý website.rewrite {ws.name}]: {e}")

    # 2. Định nghĩa mã chuyển hướng HTML/JS thuần túy cho Homepage View
    hp_arch = """<t name="Homepage" t-name="website.homepage">
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/web/login"/>
            <script type="text/javascript">
                window.location.replace('/web/login');
            </script>
        </head>
        <body style="margin:0;padding:0;background:#FAF8F2;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;color:#263247;">
            <script type="text/javascript">
                window.location.replace('/web/login');
            </script>
            Đang chuyển hướng sang trang đăng nhập: <a href="/web/login">/web/login</a>
        </body>
    </html>
</t>"""

    # 3. Dọn dẹp COW view và ghi đè toàn bộ view website.homepage
    hp_views = View.search(['|', ('key', '=', 'website.homepage'), ('name', '=', 'Homepage')])
    for v in hp_views:
        if v.website_id:
            try:
                v.unlink()
                print(f"[OK] Đã xóa COW view '{v.key}' (id={v.id}, website_id={v.website_id.id})")
                continue
            except Exception as e:
                print(f"[Lưu ý xóa COW view {v.id}]: {e}")
        try:
            v.write({'arch_db': hp_arch})
            print(f"[OK] Đã cập nhật mã chuyển hướng vào view '{v.key or v.name}' (id={v.id})")
        except Exception as e:
            print(f"[Lưu ý ghi đè view {v.id}]: {e}")

    # 4. Cấu hình website.page (Ẩn header/footer và nạp mã redirect)
    if 'website.page' in env:
        Page = env['website.page']
        pages = Page.search(['|', ('url', 'in', ['/', '', '/home']), ('is_homepage', '=', True)])
        for p in pages:
            try:
                p.write({
                    'header_visible': False,
                    'footer_visible': False,
                    'header_overlay': False,
                })
                print(f"[OK] Đã tắt header/footer trên website.page (id={p.id}, url='{p.url}')")
            except Exception as e:
                print(f"[Lưu ý website.page {p.id}]: {e}")

            if p.view_id:
                try:
                    p.view_id.write({'arch_db': hp_arch})
                    print(f"[OK] Đã nạp mã chuyển hướng vào page.view_id (id={p.view_id.id})")
                except Exception as e:
                    print(f"[Lưu ý page.view_id {p.view_id.id}]: {e}")

    # 5. Cấu hình website model (homepage_url)
    for ws in env['website'].search([]):
        vals = {}
        if hasattr(ws, 'homepage_url'):
            vals['homepage_url'] = '/web/login'
        if vals:
            try:
                ws.write(vals)
                print(f"[OK] Đã cấu hình website '{ws.name}' homepage_url = '/web/login'")
            except Exception as e:
                print(f"Lưu ý homepage_url: {e}")

    # 6. Thêm View Guard bảo vệ trên website.layout (Dự phòng tối cao)
    layout_view = env.ref('website.layout', raise_if_not_found=False)
    if layout_view:
        guard_arch = """<data>
            <xpath expr="//div[@id='wrapwrap']" position="before">
                <script type="text/javascript">
                    if (window.location.pathname === '/' || window.location.pathname === '') {
                        window.location.replace('/web/login');
                    }
                </script>
            </xpath>
        </data>"""
        guard_view = View.search([('key', '=', 'tdb_website_custom.tdb_root_guard')], limit=1)
        if guard_view:
            try:
                guard_view.write({'arch_db': guard_arch, 'active': True})
                print(f"[OK] Đã cập nhật view bảo vệ tdb_root_guard (id={guard_view.id})")
            except Exception as e:
                print(f"[Lưu ý cập nhật tdb_root_guard]: {e}")
        else:
            try:
                gv = View.create({
                    'name': 'TDB Root Guard',
                    'key': 'tdb_website_custom.tdb_root_guard',
                    'type': 'qweb',
                    'inherit_id': layout_view.id,
                    'arch_db': guard_arch,
                    'active': True,
                    'priority': 1,
                })
                print(f"[OK] Đã tạo mới view bảo vệ tdb_root_guard (id={gv.id}) trên website.layout!")
            except Exception as e:
                print(f"[Lưu ý tạo tdb_root_guard]: {e}")


def setup_vietnamese_language(env):
    """Kích hoạt và nạp gói ngôn ngữ Tiếng Việt (vi_VN) làm mặc định."""
    print("\n>>> [2/7] Đảm bảo ngôn ngữ Tiếng Việt (vi_VN) được kích hoạt...")

    # Dọn dẹp số VAT không hợp lệ nếu có để tránh lỗi _run_vat_checks
    try:
        invalid_partners = env['res.partner'].search([('vat', '=', '2336999')])
        for ip in invalid_partners:
            ip.with_context(no_vat_validation=True).write({'vat': False})
            print(f"[OK] Đã làm sạch số VAT kiểm tra lỗi trên partner '{ip.name}' (id={ip.id})")
    except Exception:
        pass

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
        try:
            rec = env.ref(ref_key, raise_if_not_found=False)
            if rec and hasattr(rec, 'lang'):
                rec.with_context(no_vat_validation=True).write({'lang': 'vi_VN'})
        except Exception as e:
            print(f"[Lưu ý lang {ref_key}]: {e}")


def cleanup_obsolete_views(env):
    """
    Xóa bỏ các view và cấu hình tùy biến cũ không còn phù hợp:
    - Khôi phục website.layout về bản gốc sạch sẽ.
    - Xóa các bản COW view bị rách tag gây tràn text ở đầu trang.
    """
    print("\n>>> [3/7] Dọn dẹp các view cũ và khôi phục template hệ thống...")
    
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


def remove_all_menus_and_cart(env):
    """
    Yêu cầu: Bỏ hết các mục menu điều hướng (Trang chủ, Cửa hàng, Sự kiện,
    Khóa học, Tuyển dụng, Liên hệ) và bỏ nút Giỏ hàng.
    """
    print("\n>>> [4/7] Xóa toàn bộ danh mục Menu và nút Giỏ hàng theo yêu cầu...")
    
    menu_model = env['website.menu']
    for ws in env['website'].search([]):
        if not ws.menu_id:
            continue
        child_menus = menu_model.search([('parent_id', '=', ws.menu_id.id)])
        for m in child_menus:
            print(f"[XÓA MENU] Đã xóa menu: '{m.name}' ({m.url})")
            m.unlink()

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

    for cv in env['ir.ui.view'].search([
        '|', '|',
        ('key', '=', 'website_sale.header_cart_link'),
        ('key', '=', 'website_sale.template_header_default'),
        ('key', 'ilike', '%header_cart%'),
    ]):
        if cv.active:
            cv.write({'active': False})
            print(f"[OK] Đã vô hiệu hóa nút Giỏ hàng: {cv.key or cv.id}")

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
    Nạp ảnh tập thể trong thư mục Picture (BG-TapThe.webp / BG-TapThe.jpg) và Logo TDB Vàng vào Odoo Attachment.
    """
    print("\n>>> [5/7] Nạp ảnh tập thể từ thư mục Picture và Logo TDB vào hệ thống...")
    search_dirs = [
        os.path.join(odoo_dir, 'Picture'),
        os.path.join(current_dir, '..', '..', 'Picture'),
        os.path.join(current_dir, 'Picture'),
        os.path.join(odoo_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img'),
        os.path.join(current_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img'),
        r'C:\odoo20\odoo\Picture',
        r'C:\odoo20\odoo\custom_addons\tdb_website_custom\static\src\img',
    ]

    for bg_filename in ['BG-TapThe.webp', 'BG-TapThe.jpg', 'tdb_logo.png']:
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
            if bg_filename.endswith('.webp'):
                mimetype = 'image/webp'
            elif bg_filename.endswith('.png'):
                mimetype = 'image/png'
            else:
                mimetype = 'image/jpeg'

            att_model = env['ir.attachment']
            for att_url in [f'/tdb_website_custom/static/src/img/{bg_filename}', f'/web/image/{bg_filename}']:
                att = att_model.search([('url', '=', att_url)], limit=1)
                vals = {
                    'name': bg_filename,
                    'type': 'binary',
                    'datas': b64_data,
                    'mimetype': mimetype,
                    'public': True,
                    'url': att_url,
                }
                if att:
                    att.write(vals)
                else:
                    att_model.create(vals)
            print(f"[OK] Đã nạp thành công '{bg_filename}' vào ir.attachment!")


def apply_tdb_login_interface(env, current_dir):
    """
    Thiết lập giao diện Đăng nhập TDB Solution theo concept 'Together We Grow':
    - Phong cách: Natural Corporate Gold Theme.
    - Cột trái (73%): Ảnh tập thể nguyên bản (BG-TapThe.webp), Card Logo & Slogan 'TOGETHER WE GROW' và thanh 3 Giá trị cốt lõi.
    - Cột phải (27%): Form đăng nhập TDB Solution màu vàng nhận diện (#D9A441), sang trọng, tối giản.
    - Nhúng khối CSS trực tiếp vào template body đảm bảo 100% ăn style ngay, không phụ thuộc cache asset.
    """
    print("\n>>> [6/7] Áp dụng giao diện Đăng nhập TDB Solution (Together We Grow - Corporate Gold)...")

    View = env['ir.ui.view']

    # 1. Gỡ bỏ các view kế thừa cũ để tránh xung đột xpath
    for xml_key in ['tdb_website_custom.bace_login_layout', 'tdb_website_custom.bace_login_form',
                    'tdb_website_custom.tdb_login_layout', 'tdb_website_custom.tdb_login_form']:
        for v in View.search([('key', '=', xml_key)]):
            try:
                v.unlink()
                print(f"[OK] Đã gỡ bỏ view kế thừa cũ '{xml_key}' (id={v.id})")
            except Exception:
                try:
                    v.write({'active': False})
                except Exception:
                    pass

    imd_records = env['ir.model.data'].search([
        ('module', '=', 'tdb_website_custom'),
        ('name', 'in', ['bace_login_layout', 'bace_login_form', 'tdb_login_layout', 'tdb_login_form'])
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

        logo_b64 = ""
        for s_dir in [
            os.path.join(current_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img'),
            os.path.join(current_dir, 'static', 'src', 'img'),
            r'C:\odoo20\odoo\custom_addons\tdb_website_custom\static\src\img',
        ]:
            logo_candidate = os.path.join(s_dir, 'tdb_logo.png')
            if os.path.exists(logo_candidate):
                try:
                    with open(logo_candidate, 'rb') as lf:
                        logo_b64 = base64.b64encode(lf.read()).decode('ascii')
                    break
                except Exception:
                    pass

        if logo_b64:
            logo_img_tag = f'<img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_gold" onerror="this.onerror=null;this.src=\'data:image/png;base64,{logo_b64}\';" alt="TDB Solution" class="form-logo"/>'
            hero_logo_img_tag = f'<img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_gold" onerror="this.onerror=null;this.src=\'data:image/png;base64,{logo_b64}\';" alt="TDB Solution" class="hero-logo"/>'
        else:
            logo_img_tag = '<img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_gold" alt="TDB Solution" class="form-logo"/>'
            hero_logo_img_tag = '<img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_gold" alt="TDB Solution" class="hero-logo"/>'

        # Cập nhật trực tiếp arch_db của web.login_layout (Together We Grow - Corporate Gold Theme)
        tdb_layout_arch = """<t t-name="web.login_layout">
    <t t-call="web.layout">
        <t t-set="html_data" t-value="{'style': 'height: 100%;'}"/>
        <t t-set="body_classname" t-value="'tdb-login-body'"/>
        <style>
<![CDATA[
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500;1,700&display=swap');

html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background: #FAF8F2 !important;
    color: #263247 !important;
    -webkit-font-smoothing: antialiased !important;
    overflow-x: hidden !important;
}

#top, #bottom, header, footer, .o_header_standard, .o_footer, .o_footer_copyright, .oe_website_login_container > .container, #oe_main_menu_navbar {
    display: none !important;
}

.login-grid {
    display: grid !important;
    grid-template-columns: 73% 27% !important;
    height: 100vh !important;
    max-height: 100vh !important;
    width: 100vw !important;
    margin: 0 !important;
    padding: 0 !important;
    background: #FAF8F2 !important;
    position: relative !important;
    overflow: hidden !important;
}

/* ---------------- Cột trái (73%): Ảnh tập thể TDB ---------------- */
.hero-side {
    position: relative !important;
    height: 100vh !important;
    overflow: hidden !important;
    background-color: #263247 !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    padding: 36px 44px !important;
    box-sizing: border-box !important;
}

.hero-bg-img {
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
    object-position: center 30% !important;
    z-index: 1 !important;
    transition: transform 6s cubic-bezier(0.25, 1, 0.5, 1) !important;
}

.hero-side:hover .hero-bg-img {
    transform: scale(1.02) !important;
}

.hero-overlay {
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(
        180deg,
        rgba(38, 50, 71, 0.18) 0%,
        rgba(250, 248, 242, 0.04) 40%,
        rgba(38, 50, 71, 0.45) 100%
    ) !important;
    z-index: 2 !important;
    pointer-events: none !important;
}

/* Góc trên bên trái: Logo & Slogan Card */
.hero-top-card {
    position: relative !important;
    z-index: 5 !important;
    background: rgba(255, 255, 255, 0.92) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(233, 227, 214, 0.9) !important;
    border-radius: 18px !important;
    padding: 22px 28px !important;
    max-width: 440px !important;
    box-shadow: 0 12px 32px rgba(38, 50, 71, 0.08) !important;
    animation: fadeInDown 0.6s ease-out !important;
}

.hero-logo-row {
    margin-bottom: 14px !important;
}

.hero-logo {
    height: 34px !important;
    width: auto !important;
    display: block !important;
    object-fit: contain !important;
}

.hero-main-slogan {
    font-size: 26px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    letter-spacing: -0.02em !important;
}

.word-together {
    color: #263247 !important;
    margin-right: 6px !important;
}

.word-we-grow {
    color: #D9A441 !important;
}

.hero-slogan-sub {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #687386 !important;
    margin-top: 6px !important;
    line-height: 1.4 !important;
}

.hero-slogan-line {
    height: 2.5px !important;
    width: 44px !important;
    background: linear-gradient(90deg, #D9A441, #B98524) !important;
    border-radius: 2px !important;
    margin: 12px 0 !important;
}

.hero-team-tag {
    font-size: 13px !important;
}

.tag-title {
    display: block !important;
    font-weight: 700 !important;
    font-style: italic !important;
    color: #B98524 !important;
    letter-spacing: 0.04em !important;
    margin-bottom: 2px !important;
}

.tag-desc {
    display: block !important;
    color: #687386 !important;
    font-size: 12.5px !important;
}

/* Phía dưới ảnh: 3 Giá trị cốt lõi */
.hero-bottom-bar {
    position: relative !important;
    z-index: 5 !important;
    background: rgba(255, 255, 255, 0.94) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(233, 227, 214, 0.9) !important;
    border-radius: 16px !important;
    padding: 12px 24px !important;
    max-width: 620px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 16px !important;
    box-shadow: 0 12px 32px rgba(38, 50, 71, 0.08) !important;
    animation: fadeInUp 0.6s ease-out !important;
}

.core-value-item {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    flex: 1 !important;
}

.core-value-icon {
    width: 38px !important;
    height: 38px !important;
    border-radius: 10px !important;
    background: #FBF6EA !important;
    color: #D9A441 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    transition: transform 0.2s ease, background-color 0.2s ease !important;
}

.core-value-item:hover .core-value-icon {
    transform: scale(1.08) !important;
    background: #F5E7C5 !important;
}

.core-value-icon svg {
    width: 20px !important;
    height: 20px !important;
    stroke: #D9A441 !important;
    stroke-width: 2 !important;
}

.core-value-info {
    display: flex !important;
    flex-direction: column !important;
}

.core-title {
    font-size: 13.5px !important;
    font-weight: 700 !important;
    color: #263247 !important;
    line-height: 1.2 !important;
}

.core-sub {
    font-size: 11.5px !important;
    color: #687386 !important;
    margin-top: 2px !important;
}

.core-divider {
    width: 1px !important;
    height: 28px !important;
    background: #E9E3D6 !important;
}

/* ---------------- Cột phải (27%): Form đăng nhập ---------------- */
.form-side {
    background: #FFFFFF !important;
    border-left: 1px solid #E9E3D6 !important;
    height: 100vh !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    padding: 40px 32px !important;
    box-shadow: -8px 0 32px rgba(38, 50, 71, 0.04) !important;
    z-index: 10 !important;
    position: relative !important;
    overflow-y: auto !important;
}

.form-inner {
    width: 100% !important;
    max-width: 350px !important;
    margin: 0 auto !important;
}

.form-logo-wrap {
    margin-bottom: 22px !important;
    text-align: left !important;
}

.form-logo {
    height: 36px !important;
    width: auto !important;
    max-width: 100% !important;
    object-fit: contain !important;
    display: block !important;
}

.form-header {
    margin-bottom: 24px !important;
    text-align: left !important;
}

.form-title {
    font-size: 26px !important;
    font-weight: 800 !important;
    color: #263247 !important;
    margin: 0 0 8px 0 !important;
    letter-spacing: -0.02em !important;
    line-height: 1.15 !important;
}

.form-subtitle {
    font-size: 13.5px !important;
    color: #687386 !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}

.form-error {
    display: flex !important;
    align-items: flex-start !important;
    gap: 10px !important;
    padding: 10px 14px !important;
    background: #FEF2F2 !important;
    border: 1px solid #FECACA !important;
    border-radius: 10px !important;
    color: #991B1B !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
    margin-bottom: 16px !important;
}

.form-group {
    margin-bottom: 18px !important;
    text-align: left !important;
}

.form-label {
    display: block !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #263247 !important;
    margin-bottom: 7px !important;
    letter-spacing: -0.005em !important;
}

.input-wrap {
    position: relative !important;
    width: 100% !important;
}

.input-wrap .icon {
    position: absolute !important;
    left: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    color: #D9A441 !important;
    pointer-events: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 2 !important;
}

.input-wrap .icon svg {
    width: 16px !important;
    height: 16px !important;
    stroke: #D9A441 !important;
    stroke-width: 2 !important;
}

.input-wrap input {
    width: 100% !important;
    height: 48px !important;
    padding: 0 16px 0 42px !important;
    font-family: inherit !important;
    font-size: 14px !important;
    color: #263247 !important;
    background: #FFFFFF !important;
    border: 1.5px solid #E9E3D6 !important;
    border-radius: 10px !important;
    outline: none !important;
    transition: all 0.15s ease !important;
    box-sizing: border-box !important;
}

.input-wrap input:focus {
    border-color: #D9A441 !important;
    box-shadow: 0 0 0 3px rgba(217, 164, 65, 0.18) !important;
    background: #FFFFFF !important;
}

.input-wrap input::placeholder {
    color: #A0AEC0 !important;
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
    color: #687386 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 6px !important;
    transition: color 0.15s ease !important;
    z-index: 3 !important;
}

.pwd-toggle:hover {
    color: #D9A441 !important;
}

.pwd-toggle svg {
    width: 16px !important;
    height: 16px !important;
    stroke: currentColor !important;
    stroke-width: 2 !important;
}

.form-row {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin-bottom: 22px !important;
    font-size: 13px !important;
}

.cbx {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    cursor: pointer !important;
    user-select: none !important;
    font-size: 13px !important;
    color: #263247 !important;
}

.cbx input {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

.cbx .box {
    width: 18px !important;
    height: 18px !important;
    border: 1.5px solid #E9E3D6 !important;
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
    background: #D9A441 !important;
    border-color: #D9A441 !important;
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

.form-forgot {
    font-size: 12.5px !important;
    font-weight: 500 !important;
    color: #D9A441 !important;
    text-decoration: none !important;
    transition: color 0.15s ease !important;
    white-space: nowrap !important;
}

.form-forgot:hover {
    color: #B98524 !important;
    text-decoration: underline !important;
}

/* Ẩn hoàn toàn các nút thừa như Đặt lại mật khẩu, Siêu quản trị */
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

.btn-submit {
    width: 100% !important;
    height: 50px !important;
    background: #D9A441 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: inherit !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: -0.005em !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(217, 164, 65, 0.32) !important;
    padding: 0 !important;
}

.btn-submit:hover {
    background: #B98524 !important;
    box-shadow: 0 6px 20px rgba(185, 133, 36, 0.42) !important;
    transform: translateY(-1px) !important;
}

.btn-submit:active {
    transform: translateY(0) !important;
}

.btn-submit svg {
    width: 16px !important;
    height: 16px !important;
    stroke: #FFFFFF !important;
    fill: none !important;
    stroke-width: 2 !important;
}

.demo-box {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    margin-top: 22px !important;
    padding: 10px 14px !important;
    background: #FAF8F2 !important;
    border: 1px solid #E9E3D6 !important;
    border-radius: 10px !important;
    font-size: 12.5px !important;
    color: #687386 !important;
    line-height: 1.5 !important;
}

.demo-box-icon {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 30px !important;
    height: 30px !important;
    border-radius: 8px !important;
    background: #FBF6EA !important;
    color: #D9A441 !important;
    flex-shrink: 0 !important;
}

.demo-box-icon svg {
    width: 16px !important;
    height: 16px !important;
    stroke: #D9A441 !important;
    fill: none !important;
    stroke-width: 2 !important;
}

.demo-box-text strong {
    color: #263247 !important;
    font-weight: 600 !important;
}

.demo-box code {
    background: #FFFFFF !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-family: ui-monospace, SF Mono, monospace !important;
    font-size: 11.5px !important;
    color: #B98524 !important;
    border: 1px solid #E9E3D6 !important;
    transition: all 0.15s ease !important;
}

.demo-box code:hover {
    background: #FBF6EA !important;
    border-color: #D9A441 !important;
}

.form-footer {
    text-align: center !important;
    font-size: 12px !important;
    color: #687386 !important;
    margin-top: 24px !important;
    line-height: 1.5 !important;
}

.form-footer .footer-copy {
    display: block !important;
    font-weight: 600 !important;
    color: #263247 !important;
}

.form-footer .footer-tagline {
    display: block !important;
    color: #687386 !important;
    margin-top: 2px !important;
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-16px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(16px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 1024px) {
    .login-grid {
        grid-template-columns: 1fr !important;
        height: auto !important;
        min-height: 100vh !important;
        overflow-y: auto !important;
    }
    .hero-side {
        height: 340px !important;
        min-height: 340px !important;
        padding: 24px !important;
    }
    .hero-bottom-bar {
        display: none !important;
    }
    .hero-top-card {
        top: auto !important;
        left: auto !important;
        position: relative !important;
        max-width: 100% !important;
        padding: 16px 20px !important;
    }
    .hero-main-slogan {
        font-size: 20px !important;
    }
    .form-side {
        padding: 36px 24px !important;
        min-height: auto !important;
        box-shadow: none !important;
        border-left: none !important;
    }
}
]]>
        </style>
        <div class="login-grid">
            <!-- Cột trái (73%): Ảnh tập thể TDB & Slogan Together We Grow -->
            <aside class="hero-side">
                <img src="/tdb_website_custom/static/src/img/BG-TapThe.webp?v=20261102" onerror="this.onerror=null;this.src='/tdb_website_custom/static/src/img/BG-TapThe.jpg?v=20261102';" alt="TDB Solution Team" class="hero-bg-img"/>
                <div class="hero-overlay"/>

                <!-- Góc trên bên trái: Logo & Slogan Card -->
                <div class="hero-top-card">
                    <div class="hero-logo-row">
                        """ + hero_logo_img_tag + """
                    </div>
                    <div class="hero-slogan-wrap">
                        <div class="hero-main-slogan">
                            <span class="word-together">TOGETHER</span>
                            <span class="word-we-grow">WE GROW</span>
                        </div>
                        <div class="hero-slogan-sub">Phát triển cùng nhau – Vững bước tương lai.</div>
                        <div class="hero-slogan-line"/>
                        <div class="hero-team-tag">
                            <span class="tag-title">ONE TEAM – ONE DREAM</span>
                            <span class="tag-desc">Cùng sáng tạo, cùng hợp tác, cùng phát triển.</span>
                        </div>
                    </div>
                </div>

                <!-- Phía dưới ảnh: 3 Giá trị cốt lõi -->
                <div class="hero-bottom-bar">
                    <div class="core-value-item">
                        <div class="core-value-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-lightbulb"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>
                        </div>
                        <div class="core-value-info">
                            <span class="core-title">Innovation</span>
                            <span class="core-sub">Sáng tạo</span>
                        </div>
                    </div>
                    <div class="core-divider"/>
                    <div class="core-value-item">
                        <div class="core-value-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-users"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                        </div>
                        <div class="core-value-info">
                            <span class="core-title">Collaboration</span>
                            <span class="core-sub">Hợp tác</span>
                        </div>
                    </div>
                    <div class="core-divider"/>
                    <div class="core-value-item">
                        <div class="core-value-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trending-up"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
                        </div>
                        <div class="core-value-info">
                            <span class="core-title">Development</span>
                            <span class="core-sub">Phát triển</span>
                        </div>
                    </div>
                </div>
            </aside>

            <!-- Cột phải (27%): Form đăng nhập TDB Solution -->
            <main class="form-side">
                <div class="form-inner">
                    <div class="form-logo-wrap">
                        """ + logo_img_tag + """
                    </div>

                    <div class="form-header">
                        <h1 class="form-title">Đăng nhập</h1>
                        <p class="form-subtitle">Chào mừng trở lại! Vui lòng đăng nhập vào hệ thống TDB Solution.</p>
                    </div>

                    <!-- Vị trí cắm form đăng nhập -->
                    <t t-out="0"/>

                    <div class="demo-box">
                        <div class="demo-box-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-key-round"><path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 1 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"/><circle cx="16.5" cy="7.5" fill="currentColor" r=".5"/></svg>
                        </div>
                        <div class="demo-box-text">
                            <strong>Demo:</strong>
                            <code onclick="var l=document.getElementById('login'),p=document.getElementById('password');if(l)l.value='admin';if(p)p.value='admin';" style="cursor:pointer;" title="Nhấp để điền">admin</code>
                            <span style="margin:0 4px;color:#cbd5e1">&#183;</span>
                            <code onclick="var l=document.getElementById('login'),p=document.getElementById('password');if(l)l.value='admin';if(p)p.value='admin';" style="cursor:pointer;" title="Nhấp để điền">admin</code>
                        </div>
                    </div>

                    <div class="form-footer">
                        <span class="footer-copy">TDB Solution © 2026.</span>
                        <span class="footer-tagline">Phát triển bền vững cùng nhau.</span>
                    </div>
                </div>
            </main>
        </div>
    </t>
</t>"""
        try:
            layout_target.write({'arch_db': tdb_layout_arch})
            print("[OK] Đã cập nhật trực tiếp web.login_layout chuẩn TDB Solution (Together We Grow - Corporate Gold)!")
        except Exception as e:
            print(f"[CẢNH BÁO web.login_layout]: {e}")

    # 4. Cập nhật trực tiếp web.login
    login_target = env.ref('web.login', raise_if_not_found=False)
    if login_target:
        child_login_views = View.search([
            ('inherit_id', '=', login_target.id),
            ('id', '!=', login_target.id),
            ('active', '=', True)
        ])
        for clv in child_login_views:
            try:
                clv.write({'active': False})
                print(f"[OK] Đã vô hiệu hóa view con kế thừa web.login: {clv.key or clv.id} ({clv.name})")
            except Exception as e:
                print(f"Lưu ý vô hiệu hóa view con web.login {clv.id}: {e}")

        for extra_key in ['auth_signup.login', 'auth_signup.reset_password', 'auth_oauth.login_buttons']:
            for ev in View.search([('key', '=', extra_key), ('active', '=', True)]):
                try:
                    ev.write({'active': False})
                    print(f"[OK] Đã tắt view phụ '{extra_key}' (id={ev.id})")
                except Exception:
                    pass

        tdb_login_arch = """<t t-name="web.login">
    <t t-call="web.login_layout">
        <t t-set="title">Đăng nhập | TDB Solution</t>
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
                <label class="form-label" for="login">Tài khoản / Email</label>
                <div class="input-wrap">
                    <svg aria-hidden="true" class="lucide lucide-mail icon" fill="none" height="16" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg">
                        <path d="m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7"/>
                        <rect height="16" rx="2" width="20" x="2" y="4"/>
                    </svg>
                    <input id="login" name="login" t-att-value="login" placeholder="admin hoặc ban@tdbsolution.com.vn" required="required" autofocus="autofocus" autocapitalize="off" autocomplete="username" class="form-control" type="text"/>
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
                <a class="form-forgot" href="/web/reset_password" t-if="debug">Quên mật khẩu?</a>
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
            </div>
        </form>
    </t>
</t>"""
        try:
            login_target.write({'arch_db': tdb_login_arch})
            print("[OK] Đã cập nhật trực tiếp web.login chuẩn TDB Solution!")
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
        setup_tdb_root_redirection(env)
        setup_vietnamese_language(env)
        cleanup_obsolete_views(env)
        remove_all_menus_and_cart(env)
        setup_picture_attachments(env, odoo_dir, current_dir)
        apply_tdb_login_interface(env, current_dir)

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
        print(">>> HOÀN TẤT THÀNH CÔNG! GIAO DIỆN TOGETHER WE GROW - CORPORATE GOLD ĐÃ ĐƯỢC ÁP DỤNG! <<<")
        print("="*70)

if __name__ == '__main__':
    main()

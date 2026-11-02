# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Kịch bản tự động hóa cấu hình giao diện TDB Solution:
Concept: TDB Solution - Giá Trị Cốt Lõi (Corporate Gold Theme theo Hình 1 & Logo Hình 2)
1. Tự động chuyển hướng trang chủ (/) sang thẳng trang đăng nhập (/web/login).
2. Bỏ toàn bộ danh mục menu (Trang chủ, Cửa hàng, Sự kiện, Khóa học, Tuyển dụng, Liên hệ) và Giỏ hàng.
3. Thiết lập giao diện Đăng nhập (/web/login) chuẩn mực 100% theo Hình 1:
   - Cột trái: Logo TDB Solution (Hình 2), Tiêu đề 'GIÁ TRỊ CỐT LÕI' + gạch chân vàng, lời dẫn và 3 Card: Tận Tâm, Đồng Hành, Bền Vững.
   - Nền: Bầu trời kem ấm, sóng vàng nghệ thuật và phối cảnh skyline tòa nhà hiện đại.
   - Cột phải: Card đăng nhập bo tròn nổi (24px), Logo TDB Solution (Hình 2), Tiêu đề, input viền kem focus vàng, nút Đăng nhập bo tròn vàng, vạch 'Hoặc', nút 'Demo: admin'.
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
        <body style="margin:0;padding:0;background:#FAF6EE;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;color:#1E293B;">
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
        try:
            Page = env['website.page']
            pages = Page.search([('url', 'in', ['/', '', '/home'])])
            try:
                for ap in Page.search([]):
                    if getattr(ap, 'is_homepage', False) and ap not in pages:
                        pages |= ap
            except Exception:
                pass

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
        except Exception as e:
            print(f"[Lưu ý cấu hình website.page]: {e}")

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
    Nạp ảnh nền (login_bg.webp, login_bg.jpg), Logo TDB Vàng (Hình 2) và ảnh tập thể vào Odoo Attachment.
    """
    print("\n>>> [5/7] Nạp tài nguyên hình ảnh (login_bg.webp, tdb_logo.png) vào hệ thống...")
    search_dirs = [
        os.path.join(odoo_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img'),
        os.path.join(current_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img'),
        os.path.join(odoo_dir, 'Picture'),
        os.path.join(current_dir, '..', '..', 'Picture'),
        os.path.join(current_dir, 'Picture'),
        r'C:\odoo20\odoo\custom_addons\tdb_website_custom\static\src\img',
        r'C:\odoo20\odoo\Picture',
    ]

    for bg_filename in ['login_bg.webp', 'login_bg.jpg', 'tdb_logo.png', 'BG-TapThe.webp', 'BG-TapThe.jpg']:
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
    Thiết lập giao diện Đăng nhập TDB Solution chuẩn 100% theo Hình 1 với Logo Hình 2:
    - Khu vực trái: Logo TDB Solution (Hình 2), 'GIÁ TRỊ CỐT LÕI' + gạch chân vàng, lời dẫn và 3 Card: Tận Tâm, Đồng Hành, Bền Vững.
    - Khu vực phải: Login Card nổi bo tròn 24px, Logo TDB Solution (Hình 2), inputs viền kem, nút Đăng nhập vàng bo tròn, vạch 'Hoặc', nút 'Demo: admin'.
    - Nhúng CSS trực tiếp đảm bảo 100% ăn giao diện ngay lập tức mà không phụ thuộc cache asset bundle.
    """
    print("\n>>> [6/7] Áp dụng giao diện Đăng nhập TDB Solution (Giá Trị Cốt Lõi - Hình 1 & Logo Hình 2)...")

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
            logo_img_tag = f'<img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_logo2" onerror="this.onerror=null;this.src=\'data:image/png;base64,{logo_b64}\';" alt="TDB Solution" class="card-logo"/>'
            hero_logo_img_tag = f'<img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_logo2" onerror="this.onerror=null;this.src=\'data:image/png;base64,{logo_b64}\';" alt="TDB Solution" class="brand-logo-img"/>'
        else:
            logo_img_tag = '<img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_logo2" alt="TDB Solution" class="card-logo"/>'
            hero_logo_img_tag = '<img src="/tdb_website_custom/static/src/img/tdb_logo.png?v=20261102_logo2" alt="TDB Solution" class="brand-logo-img"/>'

        # Cập nhật trực tiếp arch_db của web.login_layout (Thiết kế chuẩn Hình 1 & Logo Hình 2)
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
    height: 100% !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background: #FAF6EE !important;
    color: #1E293B !important;
    -webkit-font-smoothing: antialiased !important;
    overflow-x: hidden !important;
}

#top, #bottom, header, footer, .o_header_standard, .o_footer, .o_footer_copyright, .oe_website_login_container > .container, #oe_main_menu_navbar {
    display: none !important;
}

.login-wrapper {
    position: relative !important;
    width: 100vw !important;
    min-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    display: flex !important;
    background-color: #FAF6EE !important;
    background-image: url('/tdb_website_custom/static/src/img/login_bg.webp?v=20261102_1') !important;
    background-repeat: no-repeat !important;
    background-position: center center !important;
    background-size: cover !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

/* ---------------- Cột trái: Trình bày Giá Trị Cốt Lõi ---------------- */
.presentation-side {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    padding: 36px 48px !important;
    position: relative !important;
    z-index: 2 !important;
    box-sizing: border-box !important;
}

.top-brand-logo {
    display: inline-block !important;
    text-align: left !important;
}

.top-brand-logo img {
    height: 42px !important;
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
    padding: 20px 0 !important;
    max-width: 720px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.core-heading-wrap {
    margin-bottom: 28px !important;
    text-align: center !important;
}

.core-title {
    font-size: 38px !important;
    font-weight: 800 !important;
    letter-spacing: -0.01em !important;
    line-height: 1.2 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 10px !important;
}

.word-navy {
    color: #1E293B !important;
}

.word-gold {
    color: #EAA015 !important;
    position: relative !important;
}

.title-gold-line {
    width: 78px !important;
    height: 3.5px !important;
    background: #EAA015 !important;
    border-radius: 2px !important;
    margin: 8px auto 0 !important;
}

.core-subtitle {
    font-size: 14.5px !important;
    color: #475569 !important;
    line-height: 1.6 !important;
    margin: 14px 0 0 0 !important;
    max-width: 580px !important;
}

.values-row {
    display: flex !important;
    justify-content: center !important;
    gap: 16px !important;
    width: 100% !important;
    margin-top: 10px !important;
}

.value-card {
    flex: 1 !important;
    max-width: 216px !important;
    background: #FFFFFF !important;
    border: 1px solid rgba(240, 230, 210, 0.9) !important;
    border-radius: 16px !important;
    padding: 16px 18px !important;
    box-shadow: 0 8px 24px rgba(220, 180, 100, 0.08), 0 2px 6px rgba(0, 0, 0, 0.02) !important;
    text-align: left !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    box-sizing: border-box !important;
}

.value-card:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 28px rgba(220, 180, 100, 0.14) !important;
}

.value-card-header {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    margin-bottom: 10px !important;
}

.value-icon-box {
    width: 36px !important;
    height: 36px !important;
    border-radius: 10px !important;
    background: #FFFBEB !important;
    border: 1px solid #FDE68A !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    color: #EAA015 !important;
}

.value-icon-box svg {
    width: 18px !important;
    height: 18px !important;
    stroke: #EAA015 !important;
    stroke-width: 2 !important;
}

.value-divider {
    width: 1px !important;
    height: 20px !important;
    background: #E5E7EB !important;
}

.value-title {
    font-size: 15.5px !important;
    font-weight: 700 !important;
    color: #1E293B !important;
    margin: 0 !important;
    white-space: nowrap !important;
}

.value-desc {
    font-size: 12px !important;
    color: #64748B !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}

.page-footer-left {
    text-align: left !important;
    font-size: 12.5px !important;
    color: #64748B !important;
    font-weight: 500 !important;
    margin-top: 20px !important;
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
    width: 380px !important;
    max-width: 100% !important;
    background: #FFFFFF !important;
    border-radius: 24px !important;
    padding: 34px 30px 28px !important;
    box-shadow: 0 20px 48px rgba(210, 160, 50, 0.14), 0 4px 16px rgba(0, 0, 0, 0.04) !important;
    border: 1px solid rgba(240, 230, 210, 0.6) !important;
    box-sizing: border-box !important;
    text-align: left !important;
}

.card-logo-wrap {
    text-align: center !important;
    margin-bottom: 14px !important;
}

.card-logo-wrap img {
    height: 38px !important;
    width: auto !important;
    max-width: 100% !important;
    object-fit: contain !important;
    display: inline-block !important;
}

.card-title {
    font-size: 24px !important;
    font-weight: 800 !important;
    color: #1E293B !important;
    text-align: center !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: -0.01em !important;
}

.card-subtitle {
    font-size: 13px !important;
    color: #64748B !important;
    text-align: center !important;
    line-height: 1.5 !important;
    margin: 0 0 20px 0 !important;
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
    margin-bottom: 15px !important;
    text-align: left !important;
}

.form-label {
    display: block !important;
    font-size: 13px !important;
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
    width: 16px !important;
    height: 16px !important;
    stroke: #EAA015 !important;
    stroke-width: 2 !important;
}

.input-wrap input {
    width: 100% !important;
    height: 46px !important;
    padding: 0 16px 0 42px !important;
    font-family: inherit !important;
    font-size: 13.5px !important;
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
    width: 16px !important;
    height: 16px !important;
    stroke: currentColor !important;
    stroke-width: 2 !important;
}

.form-options {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin: 12px 0 18px 0 !important;
    font-size: 12.5px !important;
}

.cbx {
    display: inline-flex !important;
    align-items: center !important;
    gap: 7px !important;
    cursor: pointer !important;
    user-select: none !important;
    font-size: 12.5px !important;
    color: #1E293B !important;
}

.cbx input {
    position: absolute !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

.cbx .box {
    width: 17px !important;
    height: 17px !important;
    border: 1.5px solid #F1E7D5 !important;
    border-radius: 4px !important;
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
    width: 11px !important;
    height: 11px !important;
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
    font-size: 12.5px !important;
    font-weight: 500 !important;
    color: #1E293B !important;
}

.form-forgot {
    font-size: 12.5px !important;
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
    height: 48px !important;
    background: #EAA015 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 24px !important;
    font-family: inherit !important;
    font-size: 14.5px !important;
    font-weight: 600 !important;
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
    width: 16px !important;
    height: 16px !important;
    stroke: #FFFFFF !important;
    fill: none !important;
    stroke-width: 2 !important;
}

.divider-or {
    display: flex !important;
    align-items: center !important;
    text-align: center !important;
    margin: 14px 0 12px 0 !important;
    color: #9CA3AF !important;
    font-size: 12px !important;
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
    height: 40px !important;
    border: 1.5px solid #FDE68A !important;
    background: #FFFDF9 !important;
    border-radius: 24px !important;
    font-family: inherit !important;
    font-size: 13px !important;
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
    width: 15px !important;
    height: 15px !important;
    stroke: #EAA015 !important;
    fill: none !important;
    stroke-width: 2 !important;
}

.card-footer {
    text-align: center !important;
    font-size: 11.5px !important;
    color: #9CA3AF !important;
    margin-top: 18px !important;
}

@media (max-width: 1100px) {
    .login-wrapper {
        flex-direction: column !important;
        height: auto !important;
        overflow-y: auto !important;
        padding-bottom: 40px !important;
    }
    .presentation-side {
        padding: 30px 24px !important;
        align-items: center !important;
    }
    .top-brand-logo {
        align-self: flex-start !important;
        margin-bottom: 20px !important;
    }
    .core-title {
        font-size: 30px !important;
    }
    .values-row {
        flex-wrap: wrap !important;
    }
    .value-card {
        max-width: 280px !important;
        flex: 1 1 200px !important;
    }
    .login-card-side {
        padding: 20px 24px !important;
        width: 100% !important;
    }
    .page-footer-left {
        display: none !important;
    }
}
]]>
        </style>
        <div class="login-wrapper">
            <!-- Khu vực bên trái: Trình bày Giá Trị Cốt Lõi -->
            <aside class="presentation-side">
                <!-- Logo TDB Solution (Hình 2) góc trên bên trái -->
                <div class="top-brand-logo">
                    """ + hero_logo_img_tag + """
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
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-heart-handshake">
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
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-users">
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
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shield-check">
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
                    <!-- Logo TDB Solution (Hình 2) trong Card -->
                    <div class="card-logo-wrap">
                        """ + logo_img_tag + """
                    </div>

                    <h2 class="card-title">Đăng nhập</h2>
                    <p class="card-subtitle">Chào mừng trở lại! Vui lòng đăng nhập vào hệ thống TDB Solution.</p>

                    <!-- Form Đăng nhập cắm tại đây -->
                    <t t-out="0"/>

                    <!-- Chân Card -->
                    <div class="card-footer">
                        TDB Solution © 2026. Phát triển bền vững cùng nhau.
                    </div>
                </div>
            </main>
        </div>
    </t>
</t>"""
        try:
            layout_target.write({'arch_db': tdb_layout_arch})
            print("[OK] Đã cập nhật trực tiếp web.login_layout chuẩn TDB Solution theo Hình 1 & Logo Hình 2!")
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
                <button type="button" class="btn-demo" onclick="var l=document.getElementById('login'),p=document.getElementById('password');if(l)l.value='admin';if(p)p.value='admin';" title="Nhấp để tự động điền tài khoản demo">
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
        try:
            login_target.write({'arch_db': tdb_login_arch})
            print("[OK] Đã cập nhật trực tiếp web.login chuẩn TDB Solution theo Hình 1!")
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
        print(">>> HOÀN TẤT THÀNH CÔNG! GIAO DIỆN HÌNH 1 & LOGO HÌNH 2 ĐÃ ĐƯỢC ÁP DỤNG! <<<")
        print("="*70)

if __name__ == '__main__':
    main()

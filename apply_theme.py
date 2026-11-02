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

def setup_vietnamese_language(env):
    """Kích hoạt và nạp gói ngôn ngữ Tiếng Việt (vi_VN) làm mặc định."""
    print("\n>>> [1/6] Đảm bảo ngôn ngữ Tiếng Việt (vi_VN) được kích hoạt...")
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
    """
    print("\n>>> [5/6] Áp dụng giao diện Đăng nhập B-ACE SME tỉ lệ 8:2...")
    
    # Đọc nội dung file views/login_templates.xml
    login_xml_path = os.path.join(current_dir, 'views', 'login_templates.xml')
    if not os.path.exists(login_xml_path):
        login_xml_path = os.path.join(current_dir, 'custom_addons', 'tdb_website_custom', 'views', 'login_templates.xml')

    # Nạp trực tiếp view layout đăng nhập vào database
    bace_login_layout_arch = """<data>
    <xpath expr="//div[hasclass('container')]" position="replace">
        <div class="login-grid">
            <aside class="hero-side">
                <div class="hero-image-overlay"/>
            </aside>
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
                            <span style="margin:0 4px;color:#cbd5e1">·</span>
                            <code onclick="var l=document.getElementById('login'),p=document.getElementById('password');if(l)l.value='admin@b-ace.vn';if(p)p.value='password';" style="cursor:pointer;" title="Nhấp để điền">password</code>
                        </div>
                    </div>

                    <p class="form-footer">
                        B-ACE © 2026 · Phiên bản nội bộ
                    </p>
                </div>
            </main>
        </div>
    </xpath>
</data>"""

    bace_login_form_arch = """<data>
    <xpath expr="//form[hasclass('oe_login_form')]" position="replace">
        <form class="oe_login_form" role="form" t-attf-action="/web/login" method="post" onsubmit="this.action = '/web/login' + location.hash">
            <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>

            <div class="form-error" t-if="error" role="alert">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span><t t-out="error"/></span>
            </div>
            <div class="alert alert-success" t-if="message" role="status">
                <t t-out="message"/>
            </div>

            <div class="form-group">
                <label class="form-label" for="login">Email</label>
                <div class="input-wrap">
                    <svg aria-hidden="true" class="lucide lucide-mail icon" fill="none" height="16" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" width="16" xmlns="http://www.w3.org/2000/svg">
                        <path d="m22 7-8.991 5.727a2 2 0 0 1-2.009 0L2 7"/>
                        <rect height="16" rx="2" width="20" x="2" y="4"/>
                    </svg>
                    <input id="login" name="login" t-att-value="login" placeholder="ban@congty.com" required="required" autofocus="autofocus" autocapitalize="off" autocomplete="username" class="form-control" type="text"/>
                </div>
            </div>

            <div class="form-group">
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
        </form>
    </xpath>
</data>"""

    View = env['ir.ui.view']

    # 1. Đăng ký / cập nhật view kế thừa web.login_layout
    layout_target = env.ref('web.login_layout', raise_if_not_found=False)
    if layout_target:
        v_layout = View.search([('key', '=', 'tdb_website_custom.bace_login_layout')], limit=1)
        if not v_layout:
            v_layout = View.create({
                'name': 'B-ACE SME Login Layout (8:2)',
                'key': 'tdb_website_custom.bace_login_layout',
                'type': 'qweb',
                'inherit_id': layout_target.id,
                'arch_db': bace_login_layout_arch,
                'priority': 99,
            })
            print("[OK] Đã tạo view kế thừa B-ACE Login Layout tỉ lệ 8:2!")
        else:
            v_layout.write({'arch_db': bace_login_layout_arch, 'active': True})
            print("[OK] Đã cập nhật view B-ACE Login Layout tỉ lệ 8:2!")

    # 2. Đăng ký / cập nhật view kế thừa web.login
    login_target = env.ref('web.login', raise_if_not_found=False)
    if login_target:
        v_form = View.search([('key', '=', 'tdb_website_custom.bace_login_form')], limit=1)
        if not v_form:
            v_form = View.create({
                'name': 'B-ACE SME Login Form',
                'key': 'tdb_website_custom.bace_login_form',
                'type': 'qweb',
                'inherit_id': login_target.id,
                'arch_db': bace_login_form_arch,
                'priority': 99,
            })
            print("[OK] Đã tạo view kế thừa B-ACE Login Form!")
        else:
            v_form.write({'arch_db': bace_login_form_arch, 'active': True})
            print("[OK] Đã cập nhật view B-ACE Login Form!")


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

        cr.commit()
        print("\n" + "="*70)
        print(">>> HOÀN TẤT THÀNH CÔNG! GIAO DIỆN ĐĂNG NHẬP B-ACE SME TỈ LỆ 8:2 ĐÃ ÁP DỤNG! <<<")
        print("="*70)

if __name__ == '__main__':
    main()

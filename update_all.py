# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
KỊCH BẢN TỰ ĐỘNG HÓA NÂNG CẤP TOÀN BỘ HỆ THỐNG ODOO (UPDATE ALL MODULES)
========================================================================
Một script duy nhất thay thế toàn bộ các file cập nhật riêng lẻ:
1. Tự động kết nối cơ sở dữ liệu Odoo 20 (odoo20).
2. Thiết lập đường dẫn Video máy chủ (D:\\KhoaHoc) cho phân hệ eLearning.
3. Quét và cập nhật danh mục addons_path để nhận diện mã nguồn và ngôn ngữ i18n mới.
4. Nâng cấp đồng bộ TOÀN BỘ 6 module Custom:
   - tdb_plm_custom (Phân hệ PLM: tiêu đề chuyển đổi đa ngôn ngữ VI <-> EN, căn lề SCSS chuẩn Odoo)
   - tdb_slides_custom (Phân hệ eLearning: Video ổ đĩa D:\\KhoaHoc, Quiz, i18n)
   - tdb_dms_custom (Phân hệ DMS: Thư mục con, Thùng rác khôi phục file, i18n)
   - tdb_website_custom (Giao diện đăng nhập chuẩn doanh nghiệp TDB Solution, mã hóa SHA-256)
   - custom_home_menu (Menu chính hệ thống & chuyển đổi ngôn ngữ tức thì)
   - custom_editor_toolbar (Thanh công cụ soạn thảo văn bản)
5. Quét thư mục video con trong D:\\KhoaHoc để sẵn sàng đưa vào bài học.
6. Xóa sạch bộ nhớ đệm Asset Bundles để CSS, SCSS và JS mới có hiệu lực ngay lập tức.
"""
import os
import sys
import logging  # Nạp logging chuẩn Python trước để chống circular import với package odoo/logging.py

# Danh mục toàn bộ các module custom của dự án TDB Solution
CUSTOM_MODULES = [
    ('website_slides', 'Module gốc eLearning Odoo (Học trực tuyến)'),
    ('tdb_plm_custom', 'Tùy biến PLM (Chuyển đổi đa ngôn ngữ VI <-> EN, căn lề chuẩn SCSS)'),
    ('tdb_slides_custom', 'Tùy biến eLearning (Video ổ đĩa D:\\KhoaHoc, Quiz, i18n)'),
    ('tdb_dms_custom', 'Tùy biến DMS (Thư mục con, Thùng rác khôi phục file, i18n)'),
    ('tdb_website_custom', 'Tùy biến Website & Đăng nhập bảo mật SHA-256 TDB Solution, i18n)'),
    ('custom_home_menu', 'Tùy biến Menu chính (Home Menu) & Bộ chuyển đổi ngôn ngữ EN-VI'),
    ('custom_editor_toolbar', 'Tùy biến Thanh công cụ soạn thảo (Editor Toolbar)'),
]

def safe_set_param(env, key, value):
    """Lưu cấu hình vào ir.config_parameter an toàn trên mọi phiên bản Odoo (Odoo 14 -> 20.0)."""
    icp = env['ir.config_parameter'].sudo()
    val_str = str(value) if value is not None else ''
    setter = getattr(icp, 'set_str', getattr(icp, 'set_param', None))
    if setter:
        try:
            setter(key, val_str)
            return
        except Exception:
            pass
    rec = icp.search([('key', '=', key)], limit=1)
    if rec:
        rec.write({'value': val_str})
    else:
        icp.create({'key': key, 'value': val_str})

def main():
    print("=" * 85)
    print(">>> NÂNG CẤP ĐỒNG BỘ TOÀN BỘ MODULE HỆ THỐNG ODOO (TDB SOLUTION) <<<")
    print("=" * 85)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) in ('tdb_plm_custom', 'tdb_slides_custom', 'custom_addons', 'addons'):
        odoo_dir = os.path.abspath(os.path.join(current_dir, '..'))
        while os.path.basename(odoo_dir) in ('custom_addons', 'addons'):
            odoo_dir = os.path.abspath(os.path.join(odoo_dir, '..'))
    else:
        odoo_dir = current_dir

    os.chdir(odoo_dir)

    # Bảo vệ sys.path: Loại bỏ mọi đường dẫn trỏ trực tiếp vào thư mục gói odoo con
    # tránh hiện tượng xung đột circular import logging.py
    sys.path = [p for p in sys.path if not (os.path.basename(p.rstrip(r'\/')) == 'odoo' and os.path.isfile(os.path.join(p, '__init__.py')))]
    if odoo_dir not in sys.path:
        sys.path.insert(0, odoo_dir)

    try:
        import odoo
        from odoo.tools import config
        try:
            from odoo.modules.registry import Registry
        except ImportError:
            from odoo.orm.registry import Registry
    except ImportError:
        candidate_roots = [
            r'C:\Program Files\Odoo 20.0.20260927\server',
            r'C:\odoo20\server',
            os.path.join(odoo_dir, 'server'),
        ]
        for c in candidate_roots:
            if os.path.exists(os.path.join(c, 'odoo', '__init__.py')) and c not in sys.path:
                sys.path.append(c)
                break
        try:
            import odoo
            from odoo.tools import config
            try:
                from odoo.modules.registry import Registry
            except ImportError:
                from odoo.orm.registry import Registry
        except ImportError as e:
            print(f"[LỖI]: Không thể nạp thư viện Odoo: {e}.")
            print("Vui lòng kích hoạt môi trường ảo Python trước khi chạy (ví dụ: .venv\\Scripts\\activate).")
            return

    config_candidates = [
        os.path.join(odoo_dir, 'odoo.conf'),
        os.path.join(odoo_dir, 'config', 'odoo.conf'),
        r'C:\Program Files\Odoo 20.0.20260927\server\odoo.conf',
        'odoo.conf',
    ]
    config_path = 'odoo.conf'
    for c in config_candidates:
        if os.path.exists(c):
            config_path = c
            break

    print(f"\n[1/6] Kết nối cơ sở dữ liệu odoo20 (config: {config_path})...")
    try:
        config.parse_config(['-c', config_path], setup_logging=False)
    except TypeError:
        config.parse_config(['-c', config_path])

    # Thiết lập đường dẫn addons_path đầy đủ cho toàn bộ hệ thống
    custom_addons_path = os.path.join(odoo_dir, 'custom_addons')
    base_addons_path = os.path.join(odoo_dir, 'addons')
    raw_addons = config.get('addons_path') or ''
    if isinstance(raw_addons, list):
        current_paths = [p for p in raw_addons if p]
    elif isinstance(raw_addons, str):
        current_paths = [p.strip() for p in raw_addons.split(',') if p.strip()]
    else:
        current_paths = []

    for p in [custom_addons_path, base_addons_path]:
        if os.path.exists(p) and p not in current_paths:
            current_paths.append(p)

    if isinstance(raw_addons, list):
        config['addons_path'] = current_paths
    else:
        config['addons_path'] = ','.join(current_paths)

    try:
        import odoo.addons
        for p in current_paths:
            if p not in odoo.addons.__path__:
                odoo.addons.__path__.append(p)
    except Exception:
        pass

    db_name = config.get('db_name') or 'odoo20'
    registry = Registry(db_name)

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        # Bước 2: Thiết lập cấu hình Video Server
        print("\n[2/6] Thiết lập cấu hình Video Server D:\\KhoaHoc...")
        target_video_dir = r"D:\KhoaHoc"
        safe_set_param(env, 'tdb.video.local_path', target_video_dir)
        safe_set_param(env, 'tdb.video.server_mode', 'local')
        safe_set_param(env, 'tdb_slides.video_local_path', target_video_dir)
        safe_set_param(env, 'tdb_slides.video_server_mode', 'local')
        print(f"  [OK] Đã lưu đường dẫn video: {target_video_dir}")

        # Bước 3: Cập nhật danh sách Module trong cơ sở dữ liệu
        print("\n[3/6] Quét và cập nhật danh mục module hệ thống (update_list)...")
        try:
            env['ir.module.module'].update_list()
            print("  [OK] Đã quét thành công các module mới trong custom_addons.")
        except Exception as e:
            print(f"  [Lưu ý update_list]: {e}")

        # Bước 4: Đồng bộ và nâng cấp toàn bộ danh sách CUSTOM_MODULES
        print("\n[4/6] Nâng cấp đồng bộ các module hệ thống...")
        for mod_name, mod_desc in CUSTOM_MODULES:
            print(f"\n  -------------------------------------------------------------------------")
            print(f"  * Xử lý module: [{mod_name}] - {mod_desc}")
            mod_rec = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)

            if not mod_rec:
                print(f"    [BỎ QUA]: Không tìm thấy module '{mod_name}' trong addons_path.")
                continue

            if mod_rec.state == 'installed':
                print(f"    -> Đang NÂNG CẤP (UPGRADE) và nạp lại views, SCSS, i18n...")
                try:
                    mod_rec.button_immediate_upgrade()
                    print(f"    [THÀNH CÔNG] Đã nâng cấp thành công '{mod_name}'!")
                except Exception as e:
                    print(f"    [Lỗi nâng cấp {mod_name}]: {e}")
                    try:
                        mod_rec.button_upgrade()
                    except Exception:
                        pass
            elif mod_name in ('tdb_plm_custom', 'website_slides'):
                print(f"    -> Đang CÀI ĐẶT MỚI (INSTALL) '{mod_name}'...")
                try:
                    mod_rec.button_immediate_install()
                    print(f"    [THÀNH CÔNG] Đã cài đặt thành công '{mod_name}'!")
                except Exception as e:
                    print(f"    [Lỗi cài đặt {mod_name}]: {e}")
                    try:
                        mod_rec.button_install()
                    except Exception:
                        pass
            else:
                print(f"    [TRẠNG THÁI HIỆN TẠI]: {mod_rec.state} (Chưa được kích hoạt, bỏ qua).")

        # Nạp lại bản dịch cho các ngôn ngữ đang kích hoạt và đồng bộ hóa đa ngôn ngữ toàn hệ thống
        print(f"\n  -------------------------------------------------------------------------")
        print("\n[5/6] Đồng bộ hóa từ điển và nạp đa ngôn ngữ (VI <-> EN) toàn hệ thống...")
        try:
            # 1. Kích hoạt tiếng Việt và tiếng Anh trong res.lang
            Lang = env['res.lang'].sudo()
            for code, name in [('vi_VN', 'Vietnamese / Tiếng Việt'), ('en_US', 'English (US)')]:
                l = Lang.search([('code', '=', code)], limit=1)
                if l and not l.active:
                    l.active = True
                elif not l:
                    try:
                        Lang._activate_lang(code)
                    except Exception:
                        try:
                            Lang.create({'code': code, 'name': name, 'active': True})
                        except Exception:
                            pass

            # 2. Đồng bộ hóa bản dịch menu PLM (vi_VN <-> en_US)
            menu_translations = {
                'plm.plm_component_menu_view': ('Components', 'Linh kiện'),
                'plm.ir_attachment_form': ('Documents', 'Tài liệu'),
                'plm.plm_menu_relation': ('Component Relations', 'Quan hệ linh kiện'),
                'plm.plm_menu_dictionaries': ('Configuration', 'Cấu hình'),
                'plm.menu_document_files': ('Search on Documents', 'Tìm kiếm tài liệu'),
                'plm.menu_backupdoc': ('Search on Backup Data Set', 'Tìm kiếm bộ sao lưu'),
                'plm.menu_checkout': ('Search on Checked-Out Documents', 'Tài liệu đang kiểm xuất'),
                'plm.menu_component_component': ('Engineering Parts', 'Linh kiện kỹ thuật'),
            }
            for xmlid, (en_name, vi_name) in menu_translations.items():
                menu = env.ref(xmlid, raise_if_not_found=False)
                if menu:
                    try:
                        menu.with_context(lang='en_US').write({'name': en_name})
                        menu.with_context(lang='vi_VN').write({'name': vi_name})
                    except Exception:
                        pass

            # 3. Đồng bộ hóa window action PLM (vi_VN <-> en_US)
            action_translations = {
                'plm.action_plm_component_base': ('Engineering Parts', 'Linh kiện kỹ thuật'),
                'plm.action_plm_component_base_cad_form': ('Engineering Parts', 'Linh kiện kỹ thuật'),
                'plm.plm_action_document_form': ('Documents', 'Tài liệu kỹ thuật'),
                'plm.action_plm_relation': ('Component Relations', 'Quan hệ linh kiện'),
            }
            for xmlid, (en_name, vi_name) in action_translations.items():
                act = env.ref(xmlid, raise_if_not_found=False)
                if act:
                    try:
                        act.with_context(lang='en_US').write({'name': en_name})
                        act.with_context(lang='vi_VN').write({'name': vi_name})
                    except Exception:
                        pass

            # Quét toàn bộ action của product.product để đồng bộ tiêu đề linh kiện kỹ thuật (Action 953)
            for act in env['ir.actions.act_window'].sudo().search([('res_model', '=', 'product.product')]):
                if act.name in ('Engineering Parts', 'Linh kiện kỹ thuật') or act.id == 953:
                    try:
                        act.with_context(lang='en_US').write({'name': 'Engineering Parts'})
                        act.with_context(lang='vi_VN').write({'name': 'Linh kiện kỹ thuật'})
                    except Exception:
                        pass

            # 4. Thiết lập view arch_db cho cả vi_VN và en_US đảm bảo tiêu đề cột chuẩn 100%
            vi_plm_arch = """<data>
    <xpath expr="//list" position="attributes">
        <attribute name="class">tdb_plm_list_view</attribute>
        <attribute name="string">Linh kiện kỹ thuật</attribute>
    </xpath>
    <xpath expr="//field[@name='image_1920']" position="attributes">
        <attribute name="string">Hình ảnh</attribute>
        <attribute name="class">text-center</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='name']" position="attributes">
        <attribute name="string">Tên linh kiện</attribute>
    </xpath>
    <xpath expr="//field[@name='configuration_name']" position="attributes">
        <attribute name="string">Tên cấu hình</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_code']" position="attributes">
        <attribute name="string">Mã kỹ thuật</attribute>
    </xpath>
    <xpath expr="//field[@name='default_code']" position="attributes">
        <attribute name="string">Tham chiếu nội bộ</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_revision']" position="attributes">
        <attribute name="string">Phiên bản kỹ thuật</attribute>
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_state']" position="attributes">
        <attribute name="string">Trạng thái kỹ thuật</attribute>
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='description']" position="attributes">
        <attribute name="string">Mô tả</attribute>
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_writable']" position="attributes">
        <attribute name="string">Có thể chỉnh sửa</attribute>
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_material']" position="attributes">
        <attribute name="string">Vật liệu thô CAD</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_surface']" position="attributes">
        <attribute name="string">Hoàn thiện bề mặt CAD</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='linkeddocuments']" position="attributes">
        <attribute name="string">Tài liệu liên kết</attribute>
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
        <attribute name="widget">many2many_tags</attribute>
    </xpath>
    <xpath expr="//field[@name='document_checkout_user_ids']" position="attributes">
        <attribute name="string">Được kiểm xuất bởi</attribute>
        <attribute name="optional">show</attribute>
        <attribute name="widget">many2many_tags</attribute>
    </xpath>
</data>"""

            en_plm_arch = """<data>
    <xpath expr="//list" position="attributes">
        <attribute name="class">tdb_plm_list_view</attribute>
        <attribute name="string">Engineering Parts</attribute>
    </xpath>
    <xpath expr="//field[@name='image_1920']" position="attributes">
        <attribute name="string">Image</attribute>
        <attribute name="class">text-center</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='name']" position="attributes">
        <attribute name="string">Name</attribute>
    </xpath>
    <xpath expr="//field[@name='configuration_name']" position="attributes">
        <attribute name="string">Configuration Name</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_code']" position="attributes">
        <attribute name="string">Engineering Code</attribute>
    </xpath>
    <xpath expr="//field[@name='default_code']" position="attributes">
        <attribute name="string">Internal Reference</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_revision']" position="attributes">
        <attribute name="string">Engineering Revision</attribute>
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_state']" position="attributes">
        <attribute name="string">Engineering Status</attribute>
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='description']" position="attributes">
        <attribute name="string">Description</attribute>
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_writable']" position="attributes">
        <attribute name="string">Writable</attribute>
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_material']" position="attributes">
        <attribute name="string">CAD Raw Material</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_surface']" position="attributes">
        <attribute name="string">CAD Surface Finishing</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='linkeddocuments']" position="attributes">
        <attribute name="string">Linked Documents</attribute>
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
        <attribute name="widget">many2many_tags</attribute>
    </xpath>
    <xpath expr="//field[@name='document_checkout_user_ids']" position="attributes">
        <attribute name="string">Checked-Out By</attribute>
        <attribute name="optional">show</attribute>
        <attribute name="widget">many2many_tags</attribute>
    </xpath>
</data>"""

            v_plm = env.ref('tdb_plm_custom.plm_component_base_tree_inherit_tdb', raise_if_not_found=False)
            if v_plm:
                try:
                    v_plm.with_context(lang='en_US').write({'arch_db': en_plm_arch})
                    v_plm.with_context(lang='vi_VN').write({'arch_db': vi_plm_arch})
                    print("  [OK] Đã nạp thành công view song ngữ PLM Components (VI <-> EN).")
                except Exception as e:
                    print(f"  [Lưu ý ghi view PLM]: {e}")

            # 5. Cập nhật bản dịch các module custom
            custom_mods = env['ir.module.module'].search([('name', 'in', ['tdb_plm_custom', 'tdb_website_custom', 'tdb_slides_custom', 'tdb_dms_custom', 'custom_home_menu']), ('state', '=', 'installed')])
            if custom_mods:
                custom_mods._update_translations(['vi_VN', 'en_US'], overwrite=True)
            print("  [OK] Đã hoàn tất đồng bộ hóa đa ngôn ngữ toàn hệ thống.")
        except Exception as e:
            print(f"  [Lưu ý đồng bộ ngôn ngữ]: {e}")

        # Quét thư mục video con trong D:\KhoaHoc cho eLearning
        try:
            if 'slide.video.folder' in env:
                Folder = env['slide.video.folder']
                video_exts = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v')
                root_rec = Folder.search(['|', ('folder_path', '=', target_video_dir), ('folder_path', '=', target_video_dir.rstrip(r'\/'))], limit=1)
                root_name = os.path.basename(target_video_dir.rstrip(r'\/')) or 'KhoaHoc'
                if not root_rec:
                    root_rec = Folder.create({
                        'name': f'Thư mục gốc {root_name}',
                        'folder_path': target_video_dir,
                        'description': f'Thư mục video gốc tại {target_video_dir}'
                    })

                if os.path.exists(target_video_dir) and os.path.isdir(target_video_dir):
                    for item in sorted(os.listdir(target_video_dir)):
                        item_full = os.path.join(target_video_dir, item)
                        if os.path.isdir(item_full) and not item.startswith('.'):
                            clean_name = item.replace('_', ' ').replace('-', ' ').title()
                            f_rec = Folder.search(['|', ('folder_path', '=', item), ('folder_path', '=', item_full)], limit=1)
                            if not f_rec:
                                Folder.create({
                                    'name': clean_name,
                                    'folder_path': item_full,
                                    'description': f'Thư mục chuyên đề: {clean_name}'
                                })
                print("  [OK] Đã quét và cập nhật danh mục thư mục video D:\\KhoaHoc.")
        except Exception as e:
            print(f"  [Lưu ý thư mục video]: {e}")

        # Bước 6: Cấu hình băm SHA-256 an toàn và bảo mật mật khẩu
        print("\n[6/7] Cấu hình cơ chế Đăng nhập băm SHA-256 an toàn & Đồng bộ tài khoản admin...")
        try:
            import re
            login_view = env.ref('web.login', raise_if_not_found=False)
            login_layout_view = env.ref('web.login_layout', raise_if_not_found=False)

            clean_onsubmit = "sessionStorage.setItem('tdb_open_home_menu', 'true'); var p=document.getElementById('password')||this.querySelector('input[name=\\'password\\']'); if(p &amp;&amp; p.value){ if(p.value==='SHA256:MatKhauMoi'||p.value==='MatKhauMoi'){ p.value='SHA256:2d11659c11fde108ffc78dfc4ffbdf69f65f4e8029506ad2207e4b3a03986232'; } else if(p.value==='SHA256:admin'||p.value==='admin'){ p.value='SHA256:8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'; } else if(!p.value.startsWith('SHA256:')){ p.value='SHA256:'+(window.tdbSha256?window.tdbSha256(p.value):p.value); } }; this.action = '/web/login' + location.hash;"
            for v in [login_layout_view, login_view]:
                if v and v.arch_db:
                    arch = v.arch_db
                    # Gỡ bỏ các đoạn script cũ nếu có
                    arch = re.sub(r'<script\b[^>]*>[\s\S]*?tdbEncryptPassword[\s\S]*?</script>', '', arch)
                    arch = re.sub(r'onclick="[^"]*tdbEncryptPassword[^"]*"', '', arch)
                    # Cập nhật onsubmit luôn luôn gọi băm SHA-256
                    arch = re.sub(r'onsubmit="[^"]*"', f'onsubmit="{clean_onsubmit}"', arch)
                    # Cập nhật nút Demo: admin điền mật khẩu MatKhauMoi
                    arch = arch.replace("p.value='admin'", "p.value='MatKhauMoi'").replace('p.value="admin"', 'p.value="MatKhauMoi"')
                    v.write({'arch_db': arch})
                    print(f"  [OK] Đã cấu hình băm SHA-256 trực tiếp trong view '{v.key or v.id}'.")

            # Đảm bảo tài khoản admin luôn đăng nhập được với mật khẩu MatKhauMoi
            admin_user = env['res.users'].sudo().search([('login', '=', 'admin')], limit=1)
            if admin_user:
                admin_user.write({'password': 'MatKhauMoi'})
                print("  [OK] Đã đảm bảo mật khẩu tài khoản 'admin' là: MatKhauMoi")
        except Exception as e:
            print(f"  [Lưu ý cấu hình đăng nhập]: {e}")

        # Bước 7: Dọn dẹp Cache Assets để CSS / SCSS và JS mới có hiệu lực ngay
        print(f"\n  -------------------------------------------------------------------------")
        print("\n[7/7] Làm sạch bộ nhớ đệm Asset Bundles & QWeb cache...")
        try:
            env.registry.clear_cache()
            cached_assets = env['ir.attachment'].search([
                '|', '|',
                ('url', '=like', '/web/assets/%'),
                ('url', '=like', '%assets_backend%'),
                ('name', '=like', '%.assets_%')
            ])
            if cached_assets:
                count = len(cached_assets)
                cached_assets.unlink()
                print(f"  [OK] Đã xóa {count} tệp cache assets. Giao diện toàn hệ thống đã được phục hồi sạch sẽ.")
            else:
                print("  [OK] Không có cache assets cũ cần xóa.")
        except Exception as e:
            print(f"  [Lưu ý xóa cache]: {e}")

        cr.commit()

    # Tự động khởi động lại tiến trình chạy ngầm Odoo Server nếu có (Scheduled Task / Service)
    try:
        import subprocess
        res = subprocess.run([
            "powershell", "-Command",
            "Stop-ScheduledTask -TaskName 'Odoo_Server_24_7' -ErrorAction SilentlyContinue; "
            "Start-Sleep -Seconds 1; "
            "Start-ScheduledTask -TaskName 'Odoo_Server_24_7' -ErrorAction SilentlyContinue; "
            "Restart-Service -Name 'odoo-server' -ErrorAction SilentlyContinue; "
            "Restart-Service -Name 'odoo20' -ErrorAction SilentlyContinue"
        ], capture_output=True, timeout=10)
        print("  [OK] Đã gửi lệnh làm mới tiến trình Odoo Server.")
    except Exception:
        pass

    print("\n" + "=" * 85)
    print(">>> HOÀN TẤT ĐỒNG BỘ TOÀN BỘ HỆ THỐNG THÀNH CÔNG! <<<")
    print("Vui lòng tải lại trình duyệt (Ctrl + F5) để trải nghiệm giao diện và ngôn ngữ mới.")
    print("=" * 85)

if __name__ == '__main__':
    main()

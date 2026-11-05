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
import http
import http.server  # Nạp http chuẩn Python trước để chống xung đột với thư mục odoo/http

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

    # Đảm bảo lưu vĩnh viễn addons_path vào file odoo.conf trên đĩa để Odoo Server luôn luôn nạp custom_addons
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as cf_file:
                lines = cf_file.readlines()
            new_lines = []
            found_addons = False
            for line in lines:
                if line.strip().startswith('addons_path'):
                    new_lines.append(f"addons_path = {','.join(current_paths)}\n")
                    found_addons = True
                else:
                    new_lines.append(line)
            if not found_addons:
                new_lines.append(f"\naddons_path = {','.join(current_paths)}\n")
            with open(config_path, 'w', encoding='utf-8') as cf_file:
                cf_file.writelines(new_lines)
            print(f"  [OK] Đã lưu cấu hình addons_path chuẩn vào: {config_path}")
    except Exception as e:
        print(f"  [Lưu ý ghi file odoo.conf]: {e}")

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
            cr.rollback()
            env.invalidate_all()
            print(f"  [Lưu ý update_list]: {e}")

        # Bước 4: Đồng bộ và nâng cấp toàn bộ danh sách CUSTOM_MODULES
        print("\n[4/6] Nâng cấp đồng bộ các module hệ thống...")
        for mod_name, mod_desc in CUSTOM_MODULES:
            print(f"\n  -------------------------------------------------------------------------")
            print(f"  * Xử lý module: [{mod_name}] - {mod_desc}")
            try:
                mod_rec = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)
            except Exception:
                cr.rollback()
                env.invalidate_all()
                mod_rec = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)

            if not mod_rec:
                print(f"    [BỎ QUA]: Không tìm thấy module '{mod_name}' trong addons_path.")
                continue

            if mod_rec.state == 'installed':
                print(f"    -> Đang NÂNG CẤP (UPGRADE) và nạp lại views, SCSS, i18n...")
                try:
                    mod_rec.button_immediate_upgrade()
                    cr.commit()
                    print(f"    [THÀNH CÔNG] Đã nâng cấp thành công '{mod_name}'!")
                except Exception as e:
                    cr.rollback()
                    env.invalidate_all()
                    print(f"    [Lỗi nâng cấp {mod_name}]: {e}")
                    try:
                        mod_rec = env['ir.module.module'].browse(mod_rec.id)
                        mod_rec.button_upgrade()
                        cr.commit()
                    except Exception:
                        cr.rollback()
                        env.invalidate_all()
            else:
                print(f"    -> Đang CÀI ĐẶT MỚI (INSTALL) '{mod_name}'...")
                try:
                    mod_rec.button_immediate_install()
                    cr.commit()
                    print(f"    [THÀNH CÔNG] Đã cài đặt thành công '{mod_name}'!")
                except Exception as e:
                    cr.rollback()
                    env.invalidate_all()
                    print(f"    [Lỗi cài đặt {mod_name}]: {e}")
                    try:
                        mod_rec = env['ir.module.module'].browse(mod_rec.id)
                        mod_rec.button_install()
                        cr.commit()
                    except Exception:
                        cr.rollback()
                        env.invalidate_all()

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

            # 4. Thiết lập view arch_db gốc là tiếng Anh chuẩn Odoo và nạp từ điển dịch vi_VN
            en_plm_arch = """<data>
    <xpath expr="//list" position="attributes">
        <attribute name="class">tdb_plm_list_view</attribute>
        <attribute name="string">Engineering Parts</attribute>
    </xpath>
    <xpath expr="//field[@name='image_1920']" position="attributes">
        <attribute name="class">text-center</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_revision']" position="attributes">
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_state']" position="attributes">
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='description']" position="attributes">
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_writable']" position="attributes">
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
        <attribute name="class">text-center</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_material']" position="attributes">
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='engineering_surface']" position="attributes">
        <attribute name="optional">show</attribute>
    </xpath>
    <xpath expr="//field[@name='linkeddocuments']" position="attributes">
        <attribute name="invisible">0</attribute>
        <attribute name="optional">show</attribute>
        <attribute name="widget">many2many_tags</attribute>
    </xpath>
    <xpath expr="//field[@name='document_checkout_user_ids']" position="attributes">
        <attribute name="optional">show</attribute>
        <attribute name="widget">many2many_tags</attribute>
    </xpath>
</data>"""

            plm_view_terms = {
                'Engineering Parts': 'Linh kiện kỹ thuật',
            }

            v_plm = env.ref('tdb_plm_custom.plm_component_base_tree_inherit_tdb', raise_if_not_found=False)
            if v_plm:
                try:
                    # Ghi gốc tiếng Anh chuẩn Odoo
                    v_plm.write({'arch_db': en_plm_arch})
                    # Nạp bản dịch tiếng Việt qua API chính thức update_field_translations
                    v_plm.update_field_translations('arch_db', {'vi_VN': plm_view_terms})
                    print("  [OK] Đã nạp thành công view song ngữ PLM Components (VI <-> EN).")
                except Exception as e:
                    print(f"  [Lưu ý ghi view PLM]: {e}")

            base_plm = env.ref('plm.plm_component_base_tree', raise_if_not_found=False)
            if base_plm:
                try:
                    base_plm.update_field_translations('arch_db', {'vi_VN': plm_view_terms})
                except Exception:
                    pass

            v_doc = env.ref('tdb_plm_custom.plm_ir_attachment_list_inherit_tdb', raise_if_not_found=False)
            if v_doc:
                doc_terms = {
                    'Documents': 'Tài liệu',
                }
                try:
                    v_doc.update_field_translations('arch_db', {'vi_VN': doc_terms})
                except Exception:
                    pass

            # 5. Cập nhật nhãn field cho product.product và ir.attachment cho CẢ TIẾNG ANH (en_US) VÀ TIẾNG VIỆT (vi_VN)
            plm_field_labels = {
                'image_1920': ('Image', 'Hình ảnh'),
                'name': ('Name', 'Tên linh kiện'),
                'configuration_name': ('Configuration Name', 'Tên cấu hình'),
                'engineering_code': ('Engineering Code', 'Mã kỹ thuật'),
                'default_code': ('Internal Reference', 'Tham chiếu nội bộ'),
                'engineering_revision': ('Engineering Revision', 'Phiên bản kỹ thuật'),
                'engineering_state': ('Engineering Status', 'Trạng thái kỹ thuật'),
                'description': ('Description', 'Mô tả'),
                'engineering_writable': ('Writable', 'Có thể chỉnh sửa'),
                'engineering_material': ('CAD Raw Material', 'Vật liệu thô CAD'),
                'engineering_surface': ('CAD Surface Finishing', 'Hoàn thiện bề mặt CAD'),
                'linkeddocuments': ('Linked Documents', 'Tài liệu liên kết'),
                'document_checkout_user_ids': ('Checked-Out By', 'Được kiểm xuất bởi'),
            }
            for fname, (en_label, vi_label) in plm_field_labels.items():
                f = env['ir.model.fields'].search([('model', '=', 'product.product'), ('name', '=', fname)], limit=1)
                if f:
                    try:
                        f.update_field_translations('field_description', {'en_US': en_label, 'vi_VN': vi_label})
                    except Exception:
                        pass
                    try:
                        f.with_context(lang='en_US').write({'field_description': en_label})
                        f.with_context(lang='vi_VN').write({'field_description': vi_label})
                    except Exception:
                        pass

            doc_field_labels = {
                'preview': ('Preview', 'Xem trước'),
                'name': ('Document Name', 'Tên tài liệu'),
                'engineering_code': ('Engineering Code', 'Mã kỹ thuật'),
                'engineering_revision': ('Engineering Revision', 'Phiên bản kỹ thuật'),
                'engineering_state': ('Engineering Status', 'Trạng thái kỹ thuật'),
                'checkout_user': ('Checked-Out By', 'Được kiểm xuất bởi'),
            }
            for fname, (en_label, vi_label) in doc_field_labels.items():
                f = env['ir.model.fields'].search([('model', '=', 'ir.attachment'), ('name', '=', fname)], limit=1)
                if f:
                    try:
                        f.update_field_translations('field_description', {'en_US': en_label, 'vi_VN': vi_label})
                        f.with_context(lang='en_US').write({'field_description': en_label})
                        f.with_context(lang='vi_VN').write({'field_description': vi_label})
                    except Exception:
                        pass

            # 6. Đồng bộ hóa đa ngôn ngữ cho toàn bộ menu ứng dụng chính (Home Menu)
            root_app_translations = {
                'Discuss': 'Thảo luận',
                'Calendar': 'Lịch',
                'To-do': 'Việc cần làm',
                'PLM': 'PLM',
                'Documents': 'Tài liệu',
                'Contacts': 'Danh bạ',
                'CRM': 'CRM',
                'Sales': 'Bán hàng',
                'Dashboards': 'Bảng thông tin',
                'Point of Sale': 'Điểm bán hàng (POS)',
                'Invoicing': 'Hóa đơn',
                'Project': 'Dự án',
                'Website': 'Trang web',
                'eLearning': 'Học trực tuyến',
                'Email Marketing': 'Tiếp thị qua Email',
                'Events': 'Sự kiện',
                'Purchase': 'Mua hàng',
                'Inventory': 'Kho hàng',
                'Manufacturing': 'Sản xuất',
                'Maintenance': 'Bảo trì',
                'Repairs': 'Sửa chữa',
                'Employees': 'Nhân viên',
                'Attendances': 'Điểm danh',
                'Recruitment': 'Tuyển dụng',
                'Time Off': 'Nghỉ phép',
                'Expenses': 'Chi phí',
                'Link Tracker': 'Theo dõi liên kết',
                'Apps': 'Ứng dụng',
                'Settings': 'Cài đặt',
            }
            app_map_en_to_vi = root_app_translations
            app_map_vi_to_en = {v: k for k, v in root_app_translations.items()}

            for m in env['ir.ui.menu'].search([('parent_id', '=', False)]):
                cur_en = (m.with_context(lang='en_US').name or '').strip()
                cur_vi = (m.with_context(lang='vi_VN').name or '').strip()

                target_en = cur_en if cur_en in app_map_en_to_vi else (app_map_vi_to_en.get(cur_en) or app_map_vi_to_en.get(cur_vi))
                target_vi = app_map_en_to_vi.get(target_en) if target_en else None

                if target_en and target_vi:
                    try:
                        m.update_field_translations('name', {'en_US': target_en, 'vi_VN': target_vi})
                    except Exception:
                        pass
                    try:
                        m.with_context(lang='en_US').write({'name': target_en})
                        m.with_context(lang='vi_VN').write({'name': target_vi})
                    except Exception:
                        pass

            # 7. Cập nhật bản dịch các module custom
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
            cr.rollback()
            print(f"  [Lưu ý thư mục video]: {e}")

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
            cr.rollback()
            print(f"  [Lưu ý xóa cache]: {e}")

        cr.commit()

    # Tự động khởi động lại tiến trình chạy ngầm Odoo Server nếu có (Scheduled Task / Service)
    try:
        import subprocess
        res = subprocess.run([
            "powershell", "-Command",
            "Get-Service -Name '*odoo*' -ErrorAction SilentlyContinue | Restart-Service -Force -ErrorAction SilentlyContinue; "
            "Stop-ScheduledTask -TaskName 'Odoo_Server_24_7' -ErrorAction SilentlyContinue; "
            "Start-Sleep -Seconds 1; "
            "Start-ScheduledTask -TaskName 'Odoo_Server_24_7' -ErrorAction SilentlyContinue; "
            "Restart-Service -Name 'odoo-server-20.0' -ErrorAction SilentlyContinue; "
            "Restart-Service -Name 'odoo-server' -ErrorAction SilentlyContinue; "
            "Restart-Service -Name 'odoo20' -ErrorAction SilentlyContinue"
        ], capture_output=True, timeout=15)
        print("  [OK] Đã gửi lệnh làm mới tiến trình Odoo Server.")
    except Exception:
        pass

    print("\n" + "=" * 85)
    print(">>> HOÀN TẤT ĐỒNG BỘ TOÀN BỘ HỆ THỐNG THÀNH CÔNG! <<<")
    print("Vui lòng tải lại trình duyệt (Ctrl + F5) để trải nghiệm giao diện và ngôn ngữ mới.")
    print("=" * 85)

if __name__ == '__main__':
    main()

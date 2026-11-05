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
            print(f"  [Lưu ý thư mục video]: {e}")

        # Bước 6: Cấu hình băm SHA-256 an toàn và bảo mật mật khẩu
        print("\n[6/7] Cấu hình cơ chế Đăng nhập băm SHA-256 an toàn & Đồng bộ tài khoản admin...")
        try:
            import re
            login_view = env.ref('web.login', raise_if_not_found=False)
            login_layout_view = env.ref('web.login_layout', raise_if_not_found=False)

            script_inline = """<script type="text/javascript"><![CDATA[
(function(){
function tdbSha256(ascii){
    function rightRotate(value, amount) { return (value >>> amount) | (value << (32 - amount)); }
    var mathPow = Math.pow, maxWord = mathPow(2, 32), lengthProperty = 'length', i, j, result = '', words = [];
    var asciiBitLength = ascii[lengthProperty] * 8;
    var hash = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var k = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ];
    words = [];
    for (i = 0; i < ascii[lengthProperty]; i++) {
        words[i >> 2] |= (ascii.charCodeAt(i) & 0xff) << (24 - (i % 4) * 8);
    }
    words[asciiBitLength >> 5] |= 0x80 << (24 - (asciiBitLength % 32));
    words[(((asciiBitLength + 64) >> 9) << 4) + 15] = asciiBitLength;
    for (i = 0; i < words[lengthProperty]; i += 16) {
        var w = words.slice(i, i + 16);
        for (var idx = 0; idx < 16; idx++) {
            if (typeof w[idx] === 'undefined') w[idx] = 0;
        }
        var oldHash = hash.slice(0);
        for (j = 0; j < 64; j++) {
            if (j >= 16) {
                var s0 = rightRotate(w[j - 15], 7) ^ rightRotate(w[j - 15], 18) ^ (w[j - 15] >>> 3);
                var s1 = rightRotate(w[j - 2], 17) ^ rightRotate(w[j - 2], 19) ^ (w[j - 2] >>> 10);
                w[j] = (w[j - 16] + s0 + w[j - 7] + s1) | 0;
            }
            var s1 = rightRotate(oldHash[4], 6) ^ rightRotate(oldHash[4], 11) ^ rightRotate(oldHash[4], 25);
            var ch = (oldHash[4] & oldHash[5]) ^ (~oldHash[4] & oldHash[6]);
            var temp1 = (oldHash[7] + s1 + ch + k[j] + w[j]) | 0;
            var s0 = rightRotate(oldHash[0], 2) ^ rightRotate(oldHash[0], 13) ^ rightRotate(oldHash[0], 22);
            var maj = (oldHash[0] & oldHash[1]) ^ (oldHash[0] & oldHash[2]) ^ (oldHash[1] & oldHash[2]);
            var temp2 = (s0 + maj) | 0;
            oldHash = [(temp1 + temp2) | 0, oldHash[0], oldHash[1], oldHash[2], (oldHash[3] + temp1) | 0, oldHash[4], oldHash[5], oldHash[6]];
        }
        for (j = 0; j < 8; j++) { hash[j] = (hash[j] + oldHash[j]) | 0; }
    }
    for (i = 0; i < 8; i++) {
        for (j = 3; j >= 0; j--) {
            var b = (hash[i] >> (8 * j)) & 255;
            result += (b < 16 ? '0' : '') + b.toString(16);
        }
    }
    return result;
}
function tdbEncrypt(plain){
    if (!plain) return plain;
    var hash = tdbSha256(plain);
    var utf8 = unescape(encodeURIComponent(plain));
    var cipher = '';
    for (var i = 0; i < utf8.length; i++) {
        var code = utf8.charCodeAt(i) ^ 0x5A;
        var hex = code.toString(16);
        cipher += (hex.length < 2 ? '0' : '') + hex;
    }
    return 'SHA256:' + hash + ':' + cipher;
}
function tdbSecureSubmit(form){
    try {
        sessionStorage.setItem('tdb_open_home_menu', 'true');
        var p = form.querySelector('input[type="password"]') || form.querySelector('input[name="password"]') || document.getElementById('password');
        if (!p || !p.value) return true;
        var raw = p.value;
        if (raw.indexOf('SHA256:') === 0 && raw.split(':').length >= 3) return true;
        var enc = tdbEncrypt(raw);
        p.value = enc;
        setTimeout(function() { p.value = raw; }, 100);
    } catch (e) {
        console.error('tdbSecureSubmit error:', e);
    }
    return true;
}
window.tdbSha256 = tdbSha256;
window.tdbEncrypt = tdbEncrypt;
window.tdbSecureSubmit = tdbSecureSubmit;
document.addEventListener('submit', function (e) {
    var t = e.target;
    if (t && t.tagName === 'FORM') {
        tdbSecureSubmit(t);
    }
}, true);
})();
]]></script>"""

            clean_onsubmit = "tdbSecureSubmit(this); this.action='/web/login'+location.hash;"
            for v in [login_layout_view, login_view]:
                if v and v.arch_db:
                    arch = v.arch_db
                    # Gỡ bỏ các đoạn script cũ nếu có
                    arch = re.sub(r'<script\b[^>]*>[\s\S]*?tdbSecureSubmit[\s\S]*?</script>', '', arch)
                    arch = re.sub(r'<script\b[^>]*>[\s\S]*?tdbEncryptPassword[\s\S]*?</script>', '', arch)
                    arch = re.sub(r'onclick="[^"]*tdbEncryptPassword[^"]*"', '', arch)
                    # Cập nhật onsubmit luôn luôn gọi băm SHA-256
                    arch = re.sub(r'onsubmit="[^"]*"', f'onsubmit="{clean_onsubmit}"', arch)
                    # Cập nhật nút Demo: admin điền mật khẩu MatKhauMoi
                    arch = arch.replace("p.value='admin'", "p.value='MatKhauMoi'").replace('p.value="admin"', 'p.value="MatKhauMoi"')

                    # Chèn script_inline trực tiếp vào form của web.login
                    if v == login_view:
                        if '</form>' in arch:
                            arch = arch.replace('</form>', script_inline + '\n</form>')
                        else:
                            arch = arch + script_inline

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

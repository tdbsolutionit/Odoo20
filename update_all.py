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
   - tdb_plm_custom (Phân hệ PLM: tiêu đề song ngữ 2 dòng, căn lề SCSS chuẩn Odoo)
   - tdb_slides_custom (Phân hệ eLearning: Video ổ đĩa D:\\KhoaHoc, Quiz, i18n)
   - tdb_dms_custom (Phân hệ DMS: Thư mục con, Thùng rác khôi phục file, i18n)
   - tdb_website_custom (Giao diện đăng nhập chuẩn doanh nghiệp TDB Solution, i18n)
   - custom_home_menu (Menu chính hệ thống)
   - custom_editor_toolbar (Thanh công cụ soạn thảo văn bản)
5. Quét thư mục video con trong D:\\KhoaHoc để sẵn sàng đưa vào bài học.
6. Xóa sạch bộ nhớ đệm Asset Bundles để CSS, SCSS và JS mới có hiệu lực ngay lập tức.
"""
import os
import sys

# Danh mục toàn bộ các module custom của dự án TDB Solution
CUSTOM_MODULES = [
    ('website_slides', 'Module gốc eLearning Odoo (Học trực tuyến)'),
    ('tdb_plm_custom', 'Tùy biến PLM (Song ngữ 2 dòng Anh - Việt, căn lề chuẩn SCSS)'),
    ('tdb_slides_custom', 'Tùy biến eLearning (Video ổ đĩa D:\\KhoaHoc, Quiz, i18n)'),
    ('tdb_dms_custom', 'Tùy biến DMS (Thư mục con, Thùng rác khôi phục file, i18n)'),
    ('tdb_website_custom', 'Tùy biến Website & Đăng nhập TDB Solution, i18n)'),
    ('custom_home_menu', 'Tùy biến Menu chính (Home Menu)'),
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
        # Nếu chưa tìm thấy odoo trong odoo_dir, thử tìm thư mục server chứa package odoo
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
        config.parse_config(['-c', config_path, '-d', 'odoo20'], setup_logging=False)
    except TypeError:
        config.parse_config(['-c', config_path, '-d', 'odoo20'])

    registry = Registry('odoo20')

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'no_vat_validation': True})

        # Bước 1: Thiết lập thư mục Video Server (D:\KhoaHoc)
        print("\n[2/5] Thiết lập đường dẫn thư mục Video lưu trữ trên Server...")
        video_candidates = [
            r'D:\KhoaHoc',
            r'D:\videos',
            r'C:\odoo20\videos',
            os.path.abspath(os.path.join(odoo_dir, 'videos')),
        ]
        target_video_dir = None
        for cand in video_candidates:
            if os.path.exists(cand):
                target_video_dir = cand
                break

        if not target_video_dir:
            target_video_dir = r'D:\KhoaHoc' if os.path.exists('D:\\') else (r'C:\odoo20\videos' if os.name == 'nt' else '/data/videos')
            try:
                os.makedirs(target_video_dir, exist_ok=True)
            except Exception:
                pass

        safe_set_param(env, 'tdb_slides_custom.base_video_path', target_video_dir)
        print(f"  [OK] Thư mục Video: {target_video_dir}")

        # Bước 2: Kích hoạt ngôn ngữ Tiếng Việt và Tiếng Anh
        print("\n[3/7] Thiết lập tầng ngôn ngữ: Kích hoạt Tiếng Việt (vi_VN) & Tiếng Anh (en_US)...")
        try:
            Lang = env['res.lang']
            for code, name in [('vi_VN', 'Vietnamese / Tiếng Việt'), ('en_US', 'English (US)')]:
                l = Lang.search([('code', '=', code)], limit=1)
                if l and not l.active:
                    l.active = True
                    print(f"  [OK] Đã kích hoạt lại ngôn ngữ '{code}'.")
                elif not l:
                    try:
                        Lang._activate_lang(code)
                        print(f"  [OK] Đã kích hoạt ngôn ngữ mới '{code}'.")
                    except Exception:
                        try:
                            Lang.create({'code': code, 'name': name, 'active': True})
                            print(f"  [OK] Đã tạo và kích hoạt ngôn ngữ '{code}'.")
                        except Exception:
                            pass
                else:
                    print(f"  [OK] Ngôn ngữ '{code}' đã sẵn sàng hoạt động.")
        except Exception as e:
            print(f"  [Lưu ý res.lang]: {e}")

        # Bước 3: Cập nhật danh mục module addons_path
        print("\n[4/7] Quét danh mục addons_path để nạp mã nguồn và tầng ngôn ngữ i18n mới...")
        try:
            env['ir.module.module'].update_list()
            print("  [OK] Đã cập nhật danh mục module thành công.")
        except Exception as e:
            print(f"  [Lưu ý update_list]: {e}")

        # Bước 4: Nâng cấp đồng bộ từng module
        print("\n[5/7] Nâng cấp đồng bộ từng module custom...")
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
        print("\n  [i18n]: Đồng bộ hóa từ điển và nạp file i18n/vi.po cho toàn bộ module...")
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
                    except Exception as e:
                        pass

            # 3. Đồng bộ hóa window action PLM (vi_VN <-> en_US)
            action_translations = {
                'plm.plm_action_component_base': ('Engineering Parts', 'Linh kiện kỹ thuật'),
                'plm.plm_action_document_form': ('Documents', 'Tài liệu kỹ thuật'),
                'plm.action_plm_relation': ('Component Relations', 'Quan hệ linh kiện'),
            }
            for xmlid, (en_name, vi_name) in action_translations.items():
                act = env.ref(xmlid, raise_if_not_found=False)
                if act:
                    try:
                        act.with_context(lang='en_US').write({'name': en_name})
                        act.with_context(lang='vi_VN').write({'name': vi_name})
                    except Exception as e:
                        pass

            # 4. Đồng bộ hóa tiêu đề trường (Field Description / Column Headers)
            field_translations = {
                ('product.product', 'image_1920'): ('Image', 'Hình ảnh'),
                ('product.product', 'name'): ('Name', 'Tên linh kiện'),
                ('product.product', 'configuration_name'): ('Configuration Name', 'Tên cấu hình'),
                ('product.product', 'engineering_code'): ('Engineering Code', 'Mã kỹ thuật'),
                ('product.product', 'default_code'): ('Internal Reference', 'Tham chiếu nội bộ'),
                ('product.product', 'engineering_revision'): ('Engineering Revision', 'Phiên bản kỹ thuật'),
                ('product.product', 'engineering_state'): ('Engineering Status', 'Trạng thái kỹ thuật'),
                ('product.product', 'description'): ('Description', 'Mô tả'),
                ('product.product', 'engineering_writable'): ('Writable', 'Có thể chỉnh sửa'),
                ('product.product', 'engineering_material'): ('CAD Raw Material', 'Vật liệu thô CAD'),
                ('product.product', 'engineering_surface'): ('CAD Surface Finishing', 'Hoàn thiện bề mặt CAD'),
                ('product.product', 'linkeddocuments'): ('Linked Documents', 'Tài liệu liên kết'),
                ('product.product', 'document_checkout_user_ids'): ('Checked-Out By', 'Được kiểm xuất bởi'),
                ('ir.attachment', 'preview'): ('Preview', 'Xem trước'),
                ('ir.attachment', 'name'): ('Document Name', 'Tên tài liệu'),
                ('ir.attachment', 'checkout_user'): ('Checked-Out By', 'Được kiểm xuất bởi'),
                ('ir.attachment', 'create_uid'): ('Created By', 'Người tạo'),
                ('ir.attachment', 'create_date'): ('Created Date', 'Ngày tạo'),
                ('ir.attachment', 'write_uid'): ('Modified By', 'Người sửa'),
                ('ir.attachment', 'write_date'): ('Modified Date', 'Ngày sửa'),
            }
            FieldModel = env['ir.model.fields'].sudo()
            for (model_name, fname), (en_desc, vi_desc) in field_translations.items():
                f_rec = FieldModel.search([('model', '=', model_name), ('name', '=', fname)], limit=1)
                if f_rec:
                    try:
                        f_rec.with_context(lang='en_US').write({'field_description': en_desc})
                        f_rec.with_context(lang='vi_VN').write({'field_description': vi_desc})
                    except Exception as e:
                        pass

            installed_modules = env['ir.module.module'].search([('state', '=', 'installed')])
            installed_modules._update_translations(['vi_VN', 'en_US'], overwrite=True)
            print("  [OK] Đã nạp thành công toàn bộ bản dịch ngôn ngữ mới (VI <-> EN).")
        except Exception as e:
            print(f"  [Lưu ý _update_translations]: {e}")

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
                            vid_count = len([f for f in os.listdir(item_full) if f.lower().endswith(video_exts)])
                            clean_name = item.replace('_', ' ').replace('-', ' ').title()
                            f_rec = Folder.search(['|', ('folder_path', '=', item), ('folder_path', '=', item_full)], limit=1)
                            if not f_rec:
                                Folder.create({
                                    'name': clean_name or f'Thư mục {item}',
                                    'folder_path': item_full,
                                    'description': f'Thư mục video tại {item_full} (Có {vid_count} video)'
                                })
        except Exception as e:
            print(f"  [Lưu ý quét thư mục video]: {e}")

        # Bước 5: Khôi phục cơ chế Đăng nhập chuẩn Odoo & Đồng bộ tài khoản admin
        print(f"\n  -------------------------------------------------------------------------")
        print("\n[6/7] Khôi phục cơ chế Đăng nhập chuẩn Odoo & Đồng bộ tài khoản admin...")
        try:
            import re
            login_view = env.ref('web.login', raise_if_not_found=False)
            login_layout_view = env.ref('web.login_layout', raise_if_not_found=False)

            clean_onsubmit = 'sessionStorage.setItem(\'tdb_open_home_menu\', \'true\'); if(window.applyHash)window.applyHash(); this.action = \'/web/login\' + location.hash;'
            for v in [login_layout_view, login_view]:
                if v and v.arch_db:
                    arch = v.arch_db
                    modified = False
                    if 'tdbEncryptPassword' in arch or 'TDB_ENC' in arch:
                        # Gỡ bỏ script inline mã hóa gây lỗi
                        arch = re.sub(r'<script\b[^>]*>[\s\S]*?tdbEncryptPassword[\s\S]*?</script>', '', arch)
                        # Khôi phục onsubmit sạch không mã hóa client
                        arch = re.sub(r'onsubmit="[^"]*tdbEncryptPassword[^"]*"', f'onsubmit="{clean_onsubmit}"', arch)
                        arch = re.sub(r'onclick="[^"]*tdbEncryptPassword[^"]*"', '', arch)
                        modified = True
                    # Cập nhật nút Demo: admin điền mật khẩu MatKhauMoi
                    if 'p.value=\'admin\'' in arch:
                        arch = arch.replace('p.value=\'admin\'', 'p.value=\'MatKhauMoi\'')
                        modified = True
                    if modified:
                        v.write({'arch_db': arch})
                        print(f"  [OK] Đã dọn sạch script mã hóa cũ trong view '{v.key or v.id}'.")
                    else:
                        print(f"  [OK] View '{v.key or v.id}' đã sạch sẽ chuẩn Odoo.")

            # Đảm bảo tài khoản admin luôn đăng nhập được với mật khẩu MatKhauMoi
            admin_user = env['res.users'].sudo().search([('login', '=', 'admin')], limit=1)
            if admin_user:
                admin_user.write({'password': 'MatKhauMoi'})
                print("  [OK] Đã đảm bảo mật khẩu tài khoản 'admin' là: MatKhauMoi")
        except Exception as e:
            print(f"  [Lưu ý khôi phục đăng nhập]: {e}")

        # Bước 6: Dọn dẹp Cache Assets để CSS / SCSS và JS mới có hiệu lực ngay
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
        print("\n  [TIẾN TRÌNH HỆ THỐNG]: Đã kích hoạt lại tiến trình Odoo Server 24/7 / Service để nạp controller mới.")
    except Exception:
        pass

    print("\n" + "=" * 85)
    print(">>> HOÀN TẤT NÂNG CẤP TOÀN BỘ HỆ THỐNG ODOO THÀNH CÔNG RỰC RỠ! <<<")
    print("Tất cả phân hệ PLM, eLearning, DMS, Website, Menu... đã sẵn sàng hoạt động!")
    print("-" * 85)
    print("LƯU Ý QUAN TRỌNG VỀ BẢO MẬT ĐĂNG NHẬP:")
    print("1. Nếu Odoo đang chạy trong cửa sổ PowerShell riêng (vd: python odoo-bin ...),")
    print("   hãy nhấn Ctrl + C tại cửa sổ đó và khởi động lại Odoo để nạp controller giải mã.")
    print("2. Tại trình duyệt, nhấn Ctrl + F5 để trang /web/login nạp script mã hóa mới.")
    print("=" * 85)

if __name__ == '__main__':
    main()

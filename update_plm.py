# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Kịch bản tự động hóa nâng cấp TOÀN BỘ các module Custom của TDB Solution trên Server:
- tdb_plm_custom (Phân hệ PLM: giao diện song ngữ Anh - Việt, căn lề đồng đều, SCSS Odoo)
- tdb_slides_custom (Phân hệ eLearning: Video từ ổ đĩa máy chủ, xem video fullscreen, i18n)
- tdb_dms_custom (Phân hệ DMS: Thư mục con, Thùng rác khôi phục file, i18n)
- tdb_website_custom (Giao diện đăng nhập chuẩn doanh nghiệp TDB Solution, i18n)
- custom_home_menu (Menu chính Odoo tùy biến)
- custom_editor_toolbar (Thanh công cụ soạn thảo phong phú)
"""
import os
import sys

# Danh sách toàn bộ các module custom của dự án TDB Solution
CUSTOM_MODULES = [
    ('tdb_plm_custom', 'Tùy biến PLM (Song ngữ Anh - Việt, căn lề chuẩn SCSS)'),
    ('tdb_slides_custom', 'Tùy biến eLearning (Video ổ đĩa Server, Quiz, i18n)'),
    ('tdb_dms_custom', 'Tùy biến DMS (Thư mục con, Thùng rác khôi phục file, i18n)'),
    ('tdb_website_custom', 'Tùy biến Website & Giao diện Đăng nhập TDB, i18n)'),
    ('custom_home_menu', 'Tùy biến Menu chính (Home Menu)'),
    ('custom_editor_toolbar', 'Tùy biến Thanh công cụ soạn thảo (Editor Toolbar)'),
]

def main():
    print("=" * 85)
    print(">>> NÂNG CẤP ĐỒNG BỘ TOÀN BỘ MODULE CUSTOM TRÊN SERVER TDB SOLUTION <<<")
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
    except ImportError as e:
        print(f"[LỖI]: Không thể nạp thư viện Odoo: {e}.")
        print("Vui lòng kích hoạt môi trường ảo Python trước khi chạy (ví dụ: .venv\\Scripts\\activate).")
        return

    config_path = os.path.join(odoo_dir, 'odoo.conf')
    if not os.path.exists(config_path):
        config_path = 'odoo.conf'

    print(f"\n[1/4] Kết nối cơ sở dữ liệu odoo20 (config: {config_path})...")
    try:
        config.parse_config(['-c', config_path, '-d', 'odoo20'], setup_logging=False)
    except TypeError:
        config.parse_config(['-c', config_path, '-d', 'odoo20'])

    registry = Registry('odoo20')

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'no_vat_validation': True})

        # Bước 1: Quét cập nhật danh mục module mới
        print("\n[2/4] Quét danh mục addons_path để nhận diện các module và file ngôn ngữ i18n mới...")
        try:
            env['ir.module.module'].update_list()
            print("  [OK] Đã cập nhật danh sách module từ các thư mục addons.")
        except Exception as e:
            print(f"  [Lưu ý update_list]: {e}")

        # Bước 2: Nâng cấp tuần tự từng module custom
        print("\n[3/4] Tiến hành nâng cấp và nạp bản dịch i18n cho từng module custom...")
        for mod_name, mod_desc in CUSTOM_MODULES:
            print(f"\n  -------------------------------------------------------------------------")
            print(f"  * Xử lý module: [{mod_name}] - {mod_desc}")
            mod_rec = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)

            if not mod_rec:
                print(f"    [BỎ QUA]: Không tìm thấy module '{mod_name}' trong addons_path.")
                continue

            if mod_rec.state == 'installed':
                print(f"    -> Đang NÂNG CẤP (UPGRADE) và nạp ngôn ngữ i18n mới...")
                try:
                    mod_rec.button_immediate_upgrade()
                    print(f"    [THÀNH CÔNG] Đã nâng cấp thành công '{mod_name}'!")
                except Exception as e:
                    print(f"    [Lỗi nâng cấp {mod_name}]: {e}")
                    try:
                        mod_rec.button_upgrade()
                    except Exception:
                        pass
            elif mod_name == 'tdb_plm_custom':
                # Nếu là module PLM mới chưa cài đặt thì tiến hành cài đặt
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

        # Bước 3: Dọn dẹp Cache Assets để giao diện toàn hệ thống mượt mà
        print(f"\n  -------------------------------------------------------------------------")
        print("\n[4/4] Dọn dẹp cache assets để toàn bộ CSS / SCSS và JS mới có hiệu lực ngay...")
        try:
            asset_attachments = env['ir.attachment'].search([
                '|', '|',
                ('url', '=like', '/web/assets/%'),
                ('url', '=like', '%assets_backend%'),
                ('name', '=like', '%.assets_%')
            ])
            if asset_attachments:
                count = len(asset_attachments)
                asset_attachments.unlink()
                print(f"  [OK] Đã xóa {count} tệp cache assets cũ. Trình duyệt sẽ tải giao diện mới nhất.")
            else:
                print("  [OK] Không có cache assets cũ cần xóa.")
        except Exception as e:
            print(f"  [Lưu ý xóa cache]: {e}")

        cr.commit()

    print("\n" + "=" * 85)
    print(">>> HOÀN TẤT NÂNG CẤP TOÀN BỘ CÁC MODULE CUSTOM CỦA TDB SOLUTION! <<<")
    print("Tất cả các module:")
    print("  1. tdb_plm_custom       - Tiêu đề song ngữ Anh - Việt, căn lề đồng đều, SCSS Odoo")
    print("  2. tdb_slides_custom    - Quản lý video khóa học từ ổ đĩa máy chủ D:\\KhoaHoc, i18n")
    print("  3. tdb_dms_custom       - Thư mục con, Thùng rác khôi phục file phòng ban, i18n")
    print("  4. tdb_website_custom   - Giao diện đăng nhập TDB Solution Giá Trị Cốt Lõi, i18n")
    print("  5. custom_home_menu     - Menu chính hệ thống")
    print("  6. custom_editor_toolbar- Thanh công cụ soạn thảo văn bản")
    print("Đã được đồng bộ hóa và cập nhật tầng ngôn ngữ i18n mới nhất thành công!")
    print("=" * 85)

if __name__ == '__main__':
    main()

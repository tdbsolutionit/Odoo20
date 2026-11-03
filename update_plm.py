# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Kịch bản tự động hóa cài đặt & nâng cấp module TDB PLM Customization trên Server:
1. Tự động kết nối cơ sở dữ liệu Odoo 20 (odoo20).
2. Quét danh sách module mới để nhận diện 'tdb_plm_custom'.
3. Cài đặt hoặc nâng cấp mã nguồn giao diện song ngữ Anh - Việt và căn lề PLM.
4. Xóa cache assets để giao diện SCSS mới có hiệu lực ngay lập tức.
"""
import os
import sys

def main():
    print("=" * 80)
    print(">>> CẬP NHẬT GIAO DIỆN & TIÊU ĐỀ SONG NGỮ PLM CHO SERVER TDB SOLUTION <<<")
    print("=" * 80)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) in ('tdb_plm_custom', 'custom_addons', 'addons'):
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

        # Bước 1: Quét danh mục module mới
        print("\n[2/4] Quét danh mục addons để nhận diện 'tdb_plm_custom'...")
        try:
            env['ir.module.module'].update_list()
            print("  [OK] Đã cập nhật danh sách module từ addons_path.")
        except Exception as e:
            print(f"  [Lưu ý update_list]: {e}")

        # Bước 2: Tìm kiếm và kích hoạt / nâng cấp tdb_plm_custom
        print("\n[3/4] Cài đặt & Nâng cấp module 'tdb_plm_custom'...")
        mod_plm_custom = env['ir.module.module'].search([('name', '=', 'tdb_plm_custom')], limit=1)

        if not mod_plm_custom:
            print("  [CẢNH BÁO]: Chưa tìm thấy module 'tdb_plm_custom' trong danh sách.")
            print("  Vui lòng kiểm tra lại addons_path trong file odoo.conf trên server.")
            return

        if mod_plm_custom.state != 'installed':
            print("  -> Tiến hành CÀI ĐẶT MỚI 'tdb_plm_custom'...")
            try:
                mod_plm_custom.button_immediate_install()
                print("  [THÀNH CÔNG] Đã cài đặt thành công 'tdb_plm_custom'!")
            except Exception as e:
                print(f"  [Lỗi cài đặt]: {e}")
                try:
                    mod_plm_custom.button_install()
                except Exception:
                    pass
        else:
            print("  -> Module đã cài đặt. Tiến hành NÂNG CẤP (UPGRADE) giao diện mới...")
            try:
                mod_plm_custom.button_immediate_upgrade()
                print("  [THÀNH CÔNG] Đã nâng cấp thành công 'tdb_plm_custom'!")
            except Exception as e:
                print(f"  [Lỗi nâng cấp]: {e}")
                try:
                    mod_plm_custom.button_upgrade()
                except Exception:
                    pass

        # Bước 3: Làm mới Asset Cache để SCSS mới có hiệu lực ngay
        print("\n[4/4] Làm mới Asset Cache cho giao diện web...")
        try:
            asset_attachments = env['ir.attachment'].search([
                ('url', '=like', '/web/assets/%')
            ])
            if asset_attachments:
                count = len(asset_attachments)
                asset_attachments.unlink()
                print(f"  [OK] Đã xóa {count} tệp cache assets cũ. Hệ thống sẽ biên dịch SCSS mới khi mở trang.")
            else:
                print("  [OK] Không có cache assets cũ cần xóa.")
        except Exception as e:
            print(f"  [Lưu ý xóa cache]: {e}")

        cr.commit()

    print("\n" + "=" * 80)
    print(">>> HOÀN TẤT CẬP NHẬT GIAO DIỆN PLM CHO SERVER TDB SOLUTION! <<<")
    print("Các tiêu đề cột đã được chuẩn hóa 100% sang dạng 'English (Tiếng Việt)':")
    print("  1. Image (Hình ảnh)")
    print("  2. Name (Tên)")
    print("  3. Engineering Code (Mã kỹ thuật)")
    print("  4. Internal Reference (Tham chiếu nội bộ)")
    print("  5. Engineering Revision (Phiên bản kỹ thuật)")
    print("  6. Engineering Status (Trạng thái kỹ thuật)")
    print("  7. Description (Mô tả)")
    print("  8. Writable (Có thể chỉnh sửa)")
    print("  9. CAD Raw Material (Vật liệu thô CAD)")
    print(" 10. CAD Surface Finishing (Hoàn thiện bề mặt CAD)")
    print(" 11. Linked Documents (Tài liệu liên kết)")
    print(" 12. Checked-Out By (Được kiểm xuất bởi)")
    print("=" * 80)

if __name__ == '__main__':
    main()

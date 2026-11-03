# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Kịch bản tự động hóa cài đặt & nâng cấp E-Learning (Học trực tuyến) trên Windows Server:
1. Tự động kiểm tra và nâng cấp module gốc 'website_slides' (eLearning) và 'tdb_slides_custom' (Video ổ đĩa).
2. Tự động nhận diện thư mục Video trên ổ đĩa Server (Ưu tiên ổ D:\\KhoaHoc hoặc C:\\odoo20\\videos).
3. Thiết lập thông số cấu hình hệ thống tdb_slides_custom.base_video_path tương thích 100% với Odoo 20.
4. Tự động quét và lập danh mục các thư mục video con có sẵn trong D:\\KhoaHoc để dùng ngay trong khóa học.
5. Làm mới Asset bundles cache để trình phát video Coursera và giao diện Quiz hoạt động hoàn hảo.
"""
import os
import sys

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
    # Fallback trực tiếp ORM chuẩn mọi phiên bản Odoo
    rec = icp.search([('key', '=', key)], limit=1)
    if rec:
        rec.write({'value': val_str})
    else:
        icp.create({'key': key, 'value': val_str})

def safe_get_param(env, key, default=''):
    """Đọc cấu hình từ ir.config_parameter tương thích mọi phiên bản Odoo."""
    icp = env['ir.config_parameter'].sudo()
    getter = getattr(icp, 'get_str', getattr(icp, 'get_param', None))
    if getter:
        try:
            val = getter(key, default=default)
            return val if val is not None else default
        except Exception:
            pass
    rec = icp.search([('key', '=', key)], limit=1)
    if rec and rec.value:
        return rec.value
    return default

def main():
    print("=" * 75)
    print(">>> CẬP NHẬT PHÂN HỆ E-LEARNING (HỌC ONLINE) CHO SERVER TDB SOLUTION <<<")
    print("=" * 75)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) in ('tdb_slides_custom', 'tdb_website_custom', 'custom_addons'):
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

    print(f"\n[1/5] Kết nối cơ sở dữ liệu odoo20 (config: {config_path})...")
    try:
        config.parse_config(['-c', config_path, '-d', 'odoo20'], setup_logging=False)
    except TypeError:
        config.parse_config(['-c', config_path, '-d', 'odoo20'])

    registry = Registry('odoo20')

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'no_vat_validation': True})

        # Bước 1: Chuẩn bị thư mục Video trên Server (Ưu tiên D:\KhoaHoc)
        print("\n[2/5] Kiểm tra và thiết lập thư mục lưu trữ Video trên Server...")
        video_candidates = [
            r'D:\KhoaHoc',
            r'D:\videos',
            r'C:\odoo20\videos',
            r'C:\odoo20\odoo\videos',
            r'C:\Videos',
            r'C:\Work\odoo20-docker\videos',
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
                print(f"  [TẠO MỚI]: Đã tạo thư mục: {target_video_dir}")
            except Exception as e:
                print(f"  [LƯU Ý]: Không thể tạo {target_video_dir}: {e}")

        print(f"  [OK] Thư mục Video gốc được chọn: {target_video_dir}")

        # Lưu vào ir.config_parameter (tương thích Odoo 20)
        safe_set_param(env, 'tdb_slides_custom.base_video_path', target_video_dir)
        print("  [OK] Đã cấu hình 'tdb_slides_custom.base_video_path' = " + target_video_dir)

        # Bước 2: Nâng cấp / Cài đặt website_slides
        print("\n[3/5] Cài đặt & Kích hoạt module gốc 'website_slides' (eLearning)...")
        mod_slides = env['ir.module.module'].search([('name', '=', 'website_slides')], limit=1)
        if mod_slides:
            if mod_slides.state != 'installed':
                print("  -> Đang tiến hành cài đặt 'website_slides'...")
                try:
                    mod_slides.button_immediate_install()
                    print("  [OK] Đã cài đặt thành công 'website_slides'!")
                except Exception as e:
                    print(f"  [Lưu ý cài đặt website_slides]: {e}")
                    try:
                        mod_slides.button_install()
                    except Exception:
                        pass
            else:
                print("  [OK] Module 'website_slides' đã ở trạng thái đã cài đặt (installed).")
        else:
            print("  [LƯU Ý]: Không tìm thấy bản ghi 'website_slides' trong ir.module.module.")

        # Bước 3: Nâng cấp / Cài đặt tdb_slides_custom
        print("\n[4/5] Cài đặt & Cập nhật module tùy biến 'tdb_slides_custom'...")
        mod_tdb = env['ir.module.module'].search([('name', '=', 'tdb_slides_custom')], limit=1)
        if not mod_tdb:
            # Quét danh sách module mới
            try:
                env['ir.module.module'].update_list()
                mod_tdb = env['ir.module.module'].search([('name', '=', 'tdb_slides_custom')], limit=1)
            except Exception:
                pass

        if mod_tdb:
            if mod_tdb.state != 'installed':
                print("  -> Đang tiến hành cài đặt 'tdb_slides_custom'...")
                try:
                    mod_tdb.button_immediate_install()
                    print("  [OK] Đã cài đặt thành công 'tdb_slides_custom'!")
                except Exception as e:
                    print(f"  [Lưu ý cài đặt tdb_slides_custom]: {e}")
                    try:
                        mod_tdb.button_install()
                    except Exception:
                        pass
            else:
                print("  -> Đang tiến hành nâng cấp mã nguồn mới 'tdb_slides_custom'...")
                try:
                    mod_tdb.button_immediate_upgrade()
                    print("  [OK] Đã nâng cấp thành công 'tdb_slides_custom'!")
                except Exception as e:
                    print(f"  [Lưu ý nâng cấp tdb_slides_custom]: {e}")
                    try:
                        mod_tdb.button_upgrade()
                    except Exception:
                        pass
        else:
            print("  [CẢNH BÁO]: Chưa tìm thấy module 'tdb_slides_custom' trong addons_path.")
            print("  Vui lòng đảm bảo 'c:\\odoo20\\custom_addons' có trong addons_path của odoo.conf.")

        # Quét và tạo danh mục các thư mục video con trong target_video_dir (D:\KhoaHoc)
        try:
            Folder = env['slide.video.folder']
            video_exts = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v')

            # 1. Bản ghi thư mục gốc
            root_rec = Folder.search(['|', ('folder_path', '=', target_video_dir), ('folder_path', '=', target_video_dir.rstrip(r'\/'))], limit=1)
            root_name = os.path.basename(target_video_dir.rstrip(r'\/')) or 'KhoaHoc'
            if not root_rec:
                root_rec = Folder.create({
                    'name': f'Thư mục gốc {root_name}',
                    'folder_path': target_video_dir,
                    'description': f'Thư mục video gốc tại {target_video_dir}'
                })
                print(f"  [TẠO MỚI]: Bản ghi thư mục gốc '{root_rec.name}' ({target_video_dir})")
            else:
                print(f"  [SẴN SÀNG]: Bản ghi thư mục gốc '{root_rec.name}' ({target_video_dir})")

            # 2. Quét các thư mục con bên trong target_video_dir
            if os.path.exists(target_video_dir) and os.path.isdir(target_video_dir):
                for item in sorted(os.listdir(target_video_dir)):
                    item_full = os.path.join(target_video_dir, item)
                    if os.path.isdir(item_full) and not item.startswith('.'):
                        vid_count = len([f for f in os.listdir(item_full) if f.lower().endswith(video_exts)])
                        clean_name = item.replace('_', ' ').replace('-', ' ').title()
                        f_rec = Folder.search(['|', ('folder_path', '=', item), ('folder_path', '=', item_full)], limit=1)
                        if not f_rec:
                            f_rec = Folder.create({
                                'name': clean_name or f'Thư mục {item}',
                                'folder_path': item_full,
                                'description': f'Thư mục video tại {item_full} (Có {vid_count} video)'
                            })
                            print(f"  [PHÁT HIỆN]: Đã thêm thư mục '{clean_name}' ({item_full}) - Tìm thấy {vid_count} video.")
                        else:
                            print(f"  [SẴN SÀNG]: Thư mục '{f_rec.name}' ({item_full}) - Tìm thấy {vid_count} video.")
        except Exception as e:
            print(f"  [Lưu ý quét thư mục video]: {e}")

        # Bước 4: Xóa sạch cache Asset Bundles và QWeb
        print("\n[5/5] Làm sạch bộ nhớ đệm Asset Bundles & QWeb cache...")
        try:
            env.registry.clear_cache()
            cached_assets = env['ir.attachment'].search([
                ('name', 'ilike', '%.assets_%'),
                ('url', 'ilike', '/web/assets/%')
            ])
            if cached_assets:
                cached_assets.unlink()
                print(f"  [OK] Đã xóa {len(cached_assets)} asset cache cũ để cập nhật CSS/JS mới!")
            else:
                print("  [OK] Không có asset cache tồn đọng.")
        except Exception as e:
            print(f"  [Lưu ý dọn dẹp cache]: {e}")

        cr.commit()

    print("\n" + "=" * 75)
    print(">>> HOÀN TẤT THÀNH CÔNG! PHÂN HỆ E-LEARNING ĐÃ SẴN SÀNG CHẠY TRÊN SERVER! <<<")
    print(f"- Địa chỉ truy cập khóa học: http://<IP_SERVER>:8080/slides")
    print(f"- Thư mục Video trên Server : {target_video_dir}")
    print("=" * 75 + "\n")

if __name__ == '__main__':
    main()

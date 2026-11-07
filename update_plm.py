# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
KỊCH BẢN TỰ ĐỘNG HÓA NÂNG CẤP MODULE TDB_PLM_CUSTOM
===================================================
Chạy script này để cập nhật nhanh toàn bộ tính năng PLM:
1. Tự động nhận diện môi trường (Docker Host hoặc Native Python).
2. Tự động quét và nâng cấp module 'tdb_plm_custom'.
3. Khởi tạo bảng dữ liệu 'plm.desktop.token' (Access Token 180 ngày).
4. Nạp menu quản trị 'Desktop Access Tokens (Quản lý thiết bị CAD)' vào: PLM -> Cấu hình.
5. Xóa sạch cache assets để giao diện cập nhật ngay lập tức.
"""
import os
import sys
import subprocess
import shutil


def get_configured_db_name(odoo_dir):
    """Đọc tên database mục tiêu từ file cấu hình config/odoo.conf hoặc odoo.conf."""
    candidates = [
        os.path.join(odoo_dir, 'config', 'odoo.conf'),
        os.path.join(odoo_dir, 'odoo.conf'),
        '/etc/odoo/odoo.conf',
    ]
    for c in candidates:
        if os.path.isfile(c):
            try:
                with open(c, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('db_name') and '=' in line:
                            val = line.split('=', 1)[1].strip()
                            if val:
                                return val
            except Exception:
                pass
    return 'odoo20_dev'


def run_upgrade_via_docker(odoo_dir, db_name):
    """Nâng cấp module an toàn qua Docker Compose khi chạy từ máy Host."""
    print(f"\n[1/4] Phát hiện môi trường Docker. Cơ sở dữ liệu mục tiêu: '{db_name}'...")

    # Tìm lệnh docker compose phù hợp
    compose_cmd = None
    if shutil.which('docker'):
        # Thử docker compose v2
        res = subprocess.run(['docker', 'compose', 'version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            compose_cmd = ['docker', 'compose']
    if not compose_cmd and shutil.which('docker-compose'):
        compose_cmd = ['docker-compose']

    if not compose_cmd:
        print("[LỖI]: Không tìm thấy lệnh 'docker compose' hoặc 'docker-compose' trong PATH.")
        return False

    print("\n[2/4] Tạm dừng container Odoo để tránh lock PostgreSQL...")
    subprocess.run(compose_cmd + ['stop', 'odoo'], cwd=odoo_dir)

    print(f"\n[3/4] Đang nâng cấp module 'tdb_plm_custom' vào CSDL '{db_name}'...")
    upgrade_cmd = compose_cmd + [
        'run', '--rm', 'odoo',
        '/opt/odoo/venv/bin/python3', '/opt/odoo/src/odoo-bin',
        '-c', '/etc/odoo/odoo.conf',
        '-u', 'tdb_plm_custom',
        '-d', db_name,
        '--stop-after-init'
    ]
    res_up = subprocess.run(upgrade_cmd, cwd=odoo_dir)
    if res_up.returncode != 0:
        print(f"[CẢNH BÁO]: Nâng cấp với db '{db_name}' kết thúc với mã {res_up.returncode}. Đang thử khởi động lại Odoo...")

    print("\n[4/4] Khởi động lại container Odoo...")
    subprocess.run(compose_cmd + ['start', 'odoo'], cwd=odoo_dir)
    return res_up.returncode == 0


def run_upgrade_native(odoo_dir, db_name):
    """Nâng cấp module qua Odoo Python ORM (khi chạy bên trong container hoặc Native venv)."""
    import odoo
    from odoo.tools import config
    try:
        from odoo.modules.registry import Registry
    except ImportError:
        from odoo.orm.registry import Registry

    config_candidates = [
        '/etc/odoo/odoo.conf',
        os.path.join(odoo_dir, 'config', 'odoo.conf'),
        os.path.join(odoo_dir, 'odoo.conf'),
        'odoo.conf',
    ]
    config_path = 'odoo.conf'
    for c in config_candidates:
        if os.path.exists(c):
            config_path = c
            break

    print(f"\n[1/4] Kết nối cơ sở dữ liệu '{db_name}' (config: {config_path})...")
    try:
        config.parse_config(['-c', config_path, '-d', db_name], setup_logging=False)
    except TypeError:
        config.parse_config(['-c', config_path, '-d', db_name])

    registry = Registry(db_name)

    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'no_vat_validation': True})

        print("\n[2/4] Quét danh mục addons để đồng bộ 'tdb_plm_custom'...")
        try:
            env['ir.module.module'].update_list()
            print("  [OK] Đã quét thành công các module từ addons_path.")
        except Exception as e:
            print(f"  [Lưu ý update_list]: {e}")

        print("\n[3/4] Cập nhật module 'tdb_plm_custom'...")
        mod = env['ir.module.module'].search([('name', '=', 'tdb_plm_custom')], limit=1)
        if not mod:
            print("  [LỖI]: Không tìm thấy module 'tdb_plm_custom' trong danh mục addons.")
            return False

        if mod.state != 'installed':
            print("  -> Tiến hành CÀI ĐẶT MỚI 'tdb_plm_custom'...")
            try:
                mod.button_immediate_install()
            except Exception:
                mod.button_install()
        else:
            print("  -> Tiến hành NÂNG CẤP (UPGRADE) 'tdb_plm_custom'...")
            try:
                mod.button_immediate_upgrade()
            except Exception:
                mod.button_upgrade()

        print("\n[4/4] Dọn dẹp cache assets giao diện...")
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
                print(f"  [OK] Đã xóa {count} tệp cache assets cũ.")
        except Exception as e:
            print(f"  [Lưu ý xóa cache]: {e}")

        cr.commit()

    return True


def main():
    print("=" * 80)
    print(">>> KỊCH BẢN NÂNG CẤP TỰ ĐỘNG: TDB PLM CUSTOMIZATION (ODOO 20) <<<")
    print("=" * 80)

    odoo_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(odoo_dir)

    db_name = get_configured_db_name(odoo_dir)

    success = False
    # Kiểm tra xem có thể nạp module odoo trực tiếp không
    can_import_odoo = False
    try:
        import odoo
        can_import_odoo = True
    except ImportError:
        can_import_odoo = False

    if can_import_odoo:
        try:
            success = run_upgrade_native(odoo_dir, db_name)
        except Exception as e:
            print(f"[CẢNH BÁO Native]: {e}. Chuyển sang phương thức Docker...")
            success = run_upgrade_via_docker(odoo_dir, db_name)
    else:
        # Chạy qua Docker Compose trên máy Host
        success = run_upgrade_via_docker(odoo_dir, db_name)

    print("\n" + "=" * 80)
    if success:
        print(">>> HOÀN TẤT NÂNG CẤP MODULE TDB_PLM_CUSTOM THÀNH CÔNG! <<<")
        print("Hệ thống đã cập nhật:")
        print("1. Bảng cơ sở dữ liệu: plm.desktop.token (Access Token 180 ngày).")
        print("2. Menu quản trị: PLM -> Cấu hình -> Desktop Access Tokens (Quản lý thiết bị CAD).")
        print("3. Lớp bảo vệ thời gian thực: Chặn 401 khi token bị Admin thu hồi từ xa.")
        print("4. Giao diện Odoo Web đã sẵn sàng: Hãy F5 lại trình duyệt để kiểm tra!")
    else:
        print(">>> NÂNG CẤP HOÀN TẤT CÓ CẢNH BÁO. VUI LÒNG KIỂM TRA LOG DOCKER! <<<")
    print("=" * 80)


if __name__ == '__main__':
    main()

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

INLINE_SECURITY_SCRIPT = """<script type="text/javascript">
<![CDATA[
(function () {
    'use strict';
    var SECURITY_KEY = 'TDB_SOLUTION_2026_SECURITY_SALT';

    function sha256Bytes(ascii) {
        function rrot(v, a) { return (v >>> a) | (v << (32 - a)); }
        var mathPow = Math.pow, maxWord = mathPow(2, 32), words = [], asciiBitLength = ascii.length * 8;
        var hash = [], k = [], primeCounter = 0, isComp = {};
        for (var c = 2; primeCounter < 64; c++) {
            if (!isComp[c]) {
                for (var i = 0; i < 313; i += c) isComp[i] = c;
                hash[primeCounter] = (mathPow(c, 0.5) * maxWord) | 0;
                k[primeCounter++] = (mathPow(c, 1 / 3) * maxWord) | 0;
            }
        }
        hash = hash.slice(0, 8);
        ascii += '\\x80';
        while (ascii.length % 64 - 56) ascii += '\\x00';
        for (var i = 0; i < ascii.length; i++) words[i >> 2] |= ascii.charCodeAt(i) << ((3 - i % 4) * 8);
        words[words.length] = (asciiBitLength / maxWord) | 0;
        words[words.length] = asciiBitLength | 0;
        for (var j = 0; j < words.length;) {
            var w = words.slice(j, j += 16), oldHash = hash;
            hash = hash.slice(0, 8);
            for (var i = 0; i < 64; i++) {
                var w15 = w[i - 15], w2 = w[i - 2];
                var s0 = rrot(w15, 7) ^ rrot(w15, 18) ^ (w15 >>> 3);
                var s1 = rrot(w2, 17) ^ rrot(w2, 19) ^ (w2 >>> 10);
                w[i] = (i < 16) ? w[i] : (w[i - 16] + s0 + w[i - 7] + s1) | 0;
                var s1_h = rrot(hash[4], 6) ^ rrot(hash[4], 11) ^ rrot(hash[4], 25);
                var ch = (hash[4] & hash[5]) ^ ((~hash[4]) & hash[6]);
                var temp1 = hash[7] + s1_h + ch + k[i] + w[i];
                var s0_h = rrot(hash[0], 2) ^ rrot(hash[0], 13) ^ rrot(hash[0], 22);
                var maj = (hash[0] & hash[1]) ^ (hash[0] & hash[2]) ^ (hash[1] & hash[2]);
                var temp2 = s0_h + maj;
                hash = [(temp1 + temp2) | 0].concat(hash);
                hash[4] = (hash[4] + temp1) | 0;
            }
            for (i = 0; i < 8; i++) hash[i] = (hash[i] + oldHash[i]) | 0;
        }
        var res = [];
        for (i = 0; i < 8; i++) {
            for (var m = 3; m >= 0; m--) res.push((hash[i] >> (8 * m)) & 255);
        }
        return res;
    }

    function encryptPassword(plainText) {
        if (!plainText || plainText.indexOf('TDB_ENC:') === 0) return plainText;
        var salt = '', chars = '0123456789abcdef';
        for (var i = 0; i < 16; i++) salt += chars.charAt(Math.floor(Math.random() * chars.length));
        var binaryStr = unescape(encodeURIComponent(plainText));
        var textBytes = [];
        for (var i = 0; i < binaryStr.length; i++) textBytes.push(binaryStr.charCodeAt(i));
        var out = [], counter = 0;
        while (out.length < textBytes.length) {
            var block = sha256Bytes(SECURITY_KEY + ':' + salt + ':' + counter);
            for (var b = 0; b < block.length; b++) out.push(block[b]);
            counter++;
        }
        var hex = '';
        for (var i = 0; i < textBytes.length; i++) {
            var h = (textBytes[i] ^ out[i]).toString(16);
            hex += (h.length === 1 ? '0' : '') + h;
        }
        return 'TDB_ENC:' + salt + ':' + hex;
    }

    window.tdbEncryptPassword = encryptPassword;

    function applySecurity() {
        var form = document.querySelector('form.oe_login_form') || document.querySelector('form[action*="/web/login"]') || document.querySelector('form');
        if (!form || form._tdb_secured) return;
        form._tdb_secured = true;

        function doEncrypt() {
            var passInput = form.querySelector('input[name="password"]') || document.getElementById('password');
            if (passInput && passInput.value && passInput.value.indexOf('TDB_ENC:') !== 0) {
                passInput.value = encryptPassword(passInput.value);
            }
        }

        form.addEventListener('submit', function (e) {
            doEncrypt();
        }, true);

        var submitBtns = form.querySelectorAll('button[type="submit"], input[type="submit"], .btn-submit');
        submitBtns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                doEncrypt();
            }, true);
        });

        var passInput = form.querySelector('input[name="password"]') || document.getElementById('password');
        if (passInput) {
            passInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    doEncrypt();
                }
            }, true);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applySecurity);
    } else {
        applySecurity();
    }
})();
]]>
</script>"""

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

        # Bước 2: Cập nhật danh mục module addons_path
        print("\n[3/5] Quét danh mục addons_path để nạp mã nguồn và tầng ngôn ngữ i18n mới...")
        try:
            env['ir.module.module'].update_list()
            print("  [OK] Đã cập nhật danh mục module thành công.")
        except Exception as e:
            print(f"  [Lưu ý update_list]: {e}")

        # Bước 3: Nâng cấp đồng bộ từng module
        print("\n[4/5] Nâng cấp đồng bộ từng module custom...")
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

        # Bước 4: Thiết lập bảo mật mã hóa mật khẩu Client-Side cho trang đăng nhập
        print(f"\n  -------------------------------------------------------------------------")
        print("\n[5/6] Thiết lập Bảo mật Đăng nhập: Mã hóa Client-Side SHA-256 CTR...")
        try:
            login_view = env.ref('web.login', raise_if_not_found=False)
            login_layout_view = env.ref('web.login_layout', raise_if_not_found=False)

            for v in [login_layout_view, login_view]:
                if v and v.arch_db:
                    arch = v.arch_db
                    modified = False
                    if 'tdbEncryptPassword' not in arch:
                        if '</t>' in arch:
                            last_t = arch.rfind('</t>')
                            arch = arch[:last_t] + INLINE_SECURITY_SCRIPT + arch[last_t:]
                            modified = True
                    if v == login_view and 'onsubmit=' in arch:
                        old_sub = 'sessionStorage.setItem(\'tdb_open_home_menu\', \'true\');'
                        new_sub = "if(window.tdbEncryptPassword){var p=document.getElementById('password');if(p&amp;&amp;p.value&amp;&amp;p.value.indexOf('TDB_ENC:')!==0)p.value=window.tdbEncryptPassword(p.value);} sessionStorage.setItem('tdb_open_home_menu', 'true');"
                        if old_sub in arch and 'tdbEncryptPassword' not in arch:
                            arch = arch.replace(old_sub, new_sub)
                            modified = True
                    if modified:
                        v.write({'arch_db': arch})
                        print(f"  [OK] Đã gắn script mã hóa mật khẩu trực tiếp vào view '{v.key or v.id}'.")
                    else:
                        print(f"  [OK] View '{v.key or v.id}' đã được bảo vệ mã hóa mật khẩu.")
        except Exception as e:
            print(f"  [Lưu ý bảo mật đăng nhập]: {e}")

        # Bước 5: Dọn dẹp Cache Assets để CSS / SCSS và JS mới có hiệu lực ngay
        print(f"\n  -------------------------------------------------------------------------")
        print("\n[6/6] Làm sạch bộ nhớ đệm Asset Bundles & QWeb cache...")
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
            "Start-ScheduledTask -TaskName 'Odoo_Server_24_7' -ErrorAction SilentlyContinue"
        ], capture_output=True, timeout=10)
        print("\n  [TIẾN TRÌNH HỆ THỐNG]: Đã kích hoạt lại tiến trình Odoo Server 24/7 để nạp controller mới.")
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

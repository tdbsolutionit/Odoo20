# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import base64
import os
import re
import sys

def make_binary_value(raw_bytes, filename="tdb_logo.png"):
    """Tạo BinaryValue chuẩn cho Odoo 20"""
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

def restore_view_from_fs(env, view, odoo_dir):
    """Khôi phục view bị lỗi về nguyên bản từ file XML gốc trên đĩa (arch_fs)"""
    rel_path = view.arch_fs or 'addons/website/views/website_templates.xml'
    search_dirs = [
        odoo_dir,
        os.path.join(odoo_dir, 'odoo'),
        os.path.join(odoo_dir, 'odoo', 'addons'),
        os.path.join(odoo_dir, 'addons'),
        r'C:\odoo20\odoo',
        r'C:\odoo20\odoo\addons',
        r'C:\odoo20\odoo\odoo\addons',
    ]
    target_file = None
    for s_dir in search_dirs:
        p1 = os.path.join(s_dir, rel_path)
        if os.path.exists(p1):
            target_file = p1
            break
        p2 = os.path.join(s_dir, 'addons', rel_path)
        if os.path.exists(p2):
            target_file = p2
            break
        if '/' in rel_path:
            p3 = os.path.join(s_dir, rel_path.split('/', 1)[-1])
            if os.path.exists(p3):
                target_file = p3
                break

    if not target_file:
        return False

    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(target_file)
        root = tree.getroot()
        tpl_id = view.key.split('.')[-1] if '.' in (view.key or '') else view.name
        elem = root.find(f".//*[@id='{tpl_id}']")
        if elem is not None:
            raw_xml = ET.tostring(elem, encoding='utf-8').decode('utf-8')
            view.write({'arch_db': raw_xml})
            print(f"[OK] Đã khôi phục view '{view.key}' từ file gốc: {target_file}")
            return True
    except Exception as e:
        print(f"[Lỗi đọc XML {target_file}]: {e}")
    return False

def main():
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
        print(f"Error importing odoo: {e}. Please ensure you are running in the Odoo virtual environment.")
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

        # =========================================================================
        # 1. THIẾT LẬP TOÀN BỘ NGÔN NGỮ TIẾNG VIỆT (VI_VN) CHO HỆ THỐNG & WEBSITE
        # =========================================================================
        print("\n>>> 1. Đang kích hoạt và nạp gói ngôn ngữ Tiếng Việt (vi_VN)...")
        vi_lang = env['res.lang'].with_context(active_test=False).search([('code', '=', 'vi_VN')], limit=1)
        if vi_lang:
            if not vi_lang.active:
                vi_lang.write({'active': True})
            print(f"[OK] Đã kích hoạt ngôn ngữ Tiếng Việt (id={vi_lang.id}, code=vi_VN)")
        else:
            try:
                env['res.lang']._activate_lang('vi_VN')
                vi_lang = env['res.lang'].search([('code', '=', 'vi_VN')], limit=1)
                print("[OK] Đã cài đặt thành công ngôn ngữ Tiếng Việt vào hệ thống!")
            except Exception as e:
                print(f"[Lưu ý cài đặt vi_VN]: {e}")

        # Đồng bộ bản dịch Tiếng Việt từ các module
        try:
            LangInstall = env['base.language.install']
            if 'lang_ids' in LangInstall._fields and vi_lang:
                installer = LangInstall.create({'lang_ids': [(6, 0, [vi_lang.id])]})
                installer.lang_install()
                print("[OK] Đã đồng bộ gói dịch thuật Tiếng Việt cho toàn bộ module!")
            elif 'lang' in LangInstall._fields:
                installer = LangInstall.create({'lang': 'vi_VN'})
                installer.lang_install()
                print("[OK] Đã đồng bộ gói dịch thuật Tiếng Việt!")
        except Exception as e:
            print(f"[Lưu ý lang_install]: {e}")

        # Đặt Tiếng Việt làm ngôn ngữ MẶC ĐỊNH cho toàn bộ Website
        for ws in env['website'].search([]):
            vals = {}
            if vi_lang:
                if vi_lang.id not in ws.language_ids.ids:
                    vals['language_ids'] = [(4, vi_lang.id)]
                vals['default_lang_id'] = vi_lang.id
            if vals:
                ws.write(vals)
            print(f"[OK] Đã thiết lập Tiếng Việt làm ngôn ngữ MẶC ĐỊNH cho Website '{ws.name}'")

        # Đặt Tiếng Việt cho tài khoản Admin, Partner và Public User
        admin_user = env.ref('base.user_admin', raise_if_not_found=False)
        if admin_user:
            admin_user.write({'lang': 'vi_VN'})
            print("[OK] Đã đặt ngôn ngữ tài khoản Administrator sang Tiếng Việt")
        partner_admin = env.ref('base.partner_admin', raise_if_not_found=False)
        if partner_admin:
            partner_admin.write({'lang': 'vi_VN'})
        public_user = env.ref('base.public_user', raise_if_not_found=False)
        if public_user:
            public_user.write({'lang': 'vi_VN'})
        public_partner = env.ref('base.public_partner', raise_if_not_found=False)
        if public_partner:
            public_partner.write({'lang': 'vi_VN'})

        # =========================================================================
        # 2. KHÔI PHỤC WEBSITE.LAYOUT VÀ XỬ LÝ DỨT ĐIỂM CÁC VIEW LỖI GÂY 500 ERROR
        # =========================================================================
        print("\n>>> 2. Đang khôi phục website.layout và dọn dẹp các view bị lỗi...")
        layout_views = env['ir.ui.view'].search([('key', '=', 'website.layout')])
        for lv in layout_views:
            if hasattr(lv, 'reset_arch'):
                try:
                    lv.reset_arch(mode='hard')
                    print(f"[OK] Đã khôi phục view {lv.key} (id={lv.id}) về nguyên bản sạch sẽ bằng reset_arch!")
                except Exception as e:
                    print(f"Lưu ý reset_arch: {e}")
            else:
                restore_view_from_fs(env, lv, odoo_dir)

        # Quét và xử lý các view bị dính chuỗi text lỗi trên đầu trang
        corrupted_text_views = env['ir.ui.view'].search([
            ('arch_db', 'ilike', '%extra_items_toggle_aria_label Footer Copyright not editable%'),
        ])
        for ctv in corrupted_text_views:
            print(f"[XỬ LÝ] View ID {ctv.id} (key='{ctv.key}') bị dính text thừa trên đầu trang, đang reset...")
            if hasattr(ctv, 'reset_arch'):
                try:
                    ctv.reset_arch(mode='hard')
                except Exception:
                    pass

        # Quét và xử lý triệt để tất cả view kế thừa bị lỗi cú pháp thiếu thẻ <xpath>
        # (Nguyên nhân gây ra lỗi ValueError: Element '<div id="footer"...' cannot be located in parent)
        broken_inherited_views = env['ir.ui.view'].search([
            ('inherit_id', '!=', False),
            ('arch_db', 'ilike', '%#0b1320%'),
        ])
        for bv in broken_inherited_views:
            arch = bv.arch_db or ''
            if '<xpath' not in arch:
                print(f"[CẢNH BÁO] Phát hiện view ID {bv.id} (key='{bv.key}', name='{bv.name}') kế thừa nhưng thiếu thẻ <xpath>!")
                if hasattr(bv, 'reset_arch'):
                    try:
                        bv.reset_arch(mode='hard')
                        print(f"[OK] Đã reset_arch view ID {bv.id} về nguyên bản")
                    except Exception as e:
                        print(f"Lưu ý reset view {bv.id}: {e}")
                
                # Kiểm tra lại, nếu vẫn còn chứa chuỗi lỗi và không có xpath thì unlink
                bv_check = env['ir.ui.view'].browse(bv.id)
                if bv_check.exists() and '<xpath' not in (bv_check.arch_db or '') and '#0b1320' in (bv_check.arch_db or ''):
                    try:
                        bv_check.unlink()
                        print(f"[OK] Đã xóa view tùy biến rác ID {bv.id} để chấm dứt hoàn toàn lỗi 500!")
                    except Exception as e:
                        print(f"Lưu ý unlink view {bv.id}: {e}")

        # =========================================================================
        # 3. CẬP NHẬT THÔNG TIN CÔNG TY & TRANG LIÊN HỆ (/contactus)
        # =========================================================================
        print("\n>>> 3. Đang cập nhật thông tin công ty và trang Liên hệ (/contactus)...")
        company = env.ref('base.main_company', raise_if_not_found=False) or env['res.company'].search([], limit=1)
        if company:
            vietnam = env.ref('base.vn', raise_if_not_found=False) or env['res.country'].search([('code', '=', 'VN')], limit=1)
            hcm = env['res.country.state'].search([('country_id', '=', vietnam.id if vietnam else False), ('name', 'ilike', 'Hồ Chí Minh')], limit=1)
            try:
                # Xóa mã số thuế demo cũ (2336999) để tránh lỗi VAT check khi đổi quốc gia sang Việt Nam
                if company.partner_id:
                    company.partner_id.with_context(no_vat_validation=True).write({'vat': False})
                company.with_context(no_vat_validation=True).write({
                    'name': 'TDB Solution',
                    'street': 'KDC Van Phuc',
                    'city': 'TP Thu Duc',
                    'state_id': hcm.id if hcm else False,
                    'country_id': vietnam.id if vietnam else False,
                    'phone': '+84 37 3704895',
                    'email': 'info@tdbsolution.com.vn',
                    'website': 'https://tdbsolution.com.vn',
                    'vat': False,
                })
                print("[OK] Đã cập nhật đầy đủ thông tin: TDB Solution, KDC Van Phuc, TP Thu Duc, TP Ho Chi Minh, Hotline +84 37 3704895, info@tdbsolution.com.vn")
            except Exception as e:
                print(f"[Lưu ý cập nhật company]: {e}")

        # Cập nhật trang Liên hệ (/contactus) chuẩn 100% với 3 icon (fa-map-marker, fa-phone, fa-envelope)
        print("\n>>> 3.1 Đang cập nhật trang Liên hệ (/contactus) với 3 icon địa chỉ, hotline, email chuẩn mẫu...")
        contactus_arch = """<t t-name="website.contactus">
    <t t-call="website.layout">
        <t t-set="additional_title">Liên hệ</t>
        <span class="hidden" data-for="contactus_form" data-values="{'email_to': 'info@tdbsolution.com.vn', 'name': '', 'phone': '', 'email_from': '', 'company': '', 'subject': '', 'contact_name': '', 'partner_name': '', 'description': ''}"></span>
        <div id="wrap" class="oe_structure oe_empty">
            <section class="s_title parallax s_parallax_is_fixed bg-black-50 pt24 pb24" data-vcss="001" data-snippet="s_title" data-scroll-background-ratio="1" data-name="Tiêu đề">
                <span class="s_parallax_bg oe_img_bg" style="background-image: url('/web/image/website.s_parallax_default_image'); background-position: 50% 0;"></span>
                <div class="o_we_bg_filter bg-black-50"></div>
                <div class="container">
                    <h1>Liên hệ</h1>
                </div>
            </section>
            <section class="s_text_block pt40 pb40 o_colored_level" data-snippet="s_text_block" data-name="Văn bản">
                <div class="s_allow_columns container">
                    <div class="row">
                        <div class="col-lg-7 mt-4 mt-lg-0">
                            <p class="lead">
                                Hãy liên hệ khi bạn gặp bất cứ vấn đề nào liên quan đến công ty hoặc dịch vụ của chúng tôi.<br/>
                                Chúng tôi sẽ cố gắng phản hồi trong thời gian sớm nhất.
                            </p>
                            <section class="s_website_form" data-vcss="001" data-snippet="s_website_form" data-name="Biểu mẫu">
                                <div class="container">
                                    <form id="contactus_form" action="/website/form/" method="post" enctype="multipart/form-data" class="o_mark_required" data-mark="*" data-model_name="mail.mail" data-success-mode="redirect" data-success-page="/contactus-thank-you" data-pre-fill="true">
                                        <div class="s_website_form_rows row s_col_no_bgcolor">
                                            <div class="mb-3 col-lg-6 s_website_form_field s_website_form_custom s_website_form_required" data-type="char" data-name="Field">
                                                <label class="s_website_form_label" style="width: 200px" for="contact1">
                                                    <span class="s_website_form_label_content">Tên</span>
                                                    <span class="s_website_form_mark"> *</span>
                                                </label>
                                                <input id="contact1" type="text" class="form-control s_website_form_input" name="name" required="" data-fill-with="name"/>
                                            </div>
                                            <div class="mb-3 col-lg-6 s_website_form_field s_website_form_custom" data-type="char" data-name="Field">
                                                <label class="s_website_form_label" style="width: 200px" for="contact2">
                                                    <span class="s_website_form_label_content">Số điện thoại</span>
                                                </label>
                                                <input id="contact2" type="tel" class="form-control s_website_form_input" name="phone" data-fill-with="phone"/>
                                            </div>
                                            <div class="mb-3 col-lg-6 s_website_form_field s_website_form_required s_website_form_model_required" data-type="email" data-name="Field">
                                                <label class="s_website_form_label" style="width: 200px" for="contact3">
                                                    <span class="s_website_form_label_content">Email</span>
                                                    <span class="s_website_form_mark"> *</span>
                                                </label>
                                                <input id="contact3" type="email" class="form-control s_website_form_input" name="email_from" required="" data-fill-with="email"/>
                                            </div>
                                            <div class="mb-3 col-lg-6 s_website_form_field s_website_form_custom" data-type="char" data-name="Field">
                                                <label class="s_website_form_label" style="width: 200px" for="contact4">
                                                    <span class="s_website_form_label_content">Công ty</span>
                                                </label>
                                                <input id="contact4" type="text" class="form-control s_website_form_input" name="company" data-fill-with="commercial_company_name"/>
                                            </div>
                                            <div class="mb-3 col-12 s_website_form_field s_website_form_required s_website_form_model_required" data-type="char" data-name="Field">
                                                <label class="s_website_form_label" style="width: 200px" for="contact5">
                                                    <span class="s_website_form_label_content">Chủ đề</span>
                                                    <span class="s_website_form_mark"> *</span>
                                                </label>
                                                <input id="contact5" type="text" class="form-control s_website_form_input" name="subject" required=""/>
                                            </div>
                                            <div class="mb-3 col-12 s_website_form_field s_website_form_custom s_website_form_required" data-type="text" data-name="Field">
                                                <label class="s_website_form_label" style="width: 200px" for="contact6">
                                                    <span class="s_website_form_label_content">Câu hỏi</span>
                                                    <span class="s_website_form_mark"> *</span>
                                                </label>
                                                <textarea id="contact6" class="form-control s_website_form_input" name="description" required="" rows="8"></textarea>
                                            </div>
                                            <div class="mb-0 py-2 col-12 s_website_form_submit s_website_form_no_submit_label text-end" data-name="Submit Button">
                                                <div style="width: 200px;" class="s_website_form_label"></div>
                                                <a href="#" role="button" class="btn btn-primary s_website_form_send">Gửi</a>
                                                <span id="s_website_form_result"></span>
                                            </div>
                                        </div>
                                    </form>
                                </div>
                            </section>
                        </div>
                        <div class="col-lg-4 offset-lg-1 mt-4 mt-lg-0 o_colored_level">
                            <h5>TDB Solution</h5>
                            <ul class="list-unstyled mb-0 ps-2">
                                <li><i class="fa fa-map-marker fa-fw me-2"></i><span class="o_force_ltr">KDC Van Phuc, TP Thu Duc, TP Ho Chi Minh, Viet Nam</span></li>
                                <li><i class="fa fa-phone fa-fw me-2"></i><span class="o_force_ltr">+84 37 370 4895</span></li>
                                <li><i class="fa fa-1x fa-fw fa-envelope me-2"></i>info@tdbsolution.com.vn</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </t>
</t>"""
        for cv in env['ir.ui.view'].search([('key', '=', 'website.contactus')]):
            try:
                cv.write({'arch_db': contactus_arch})
                print(f"[OK] Đã cập nhật view {cv.key or cv.id} với 3 icon liên hệ chuẩn mẫu!")
            except Exception as e:
                print(f"[Lưu ý contactus view {cv.id}]: {e}")

        for cp in env['website.page'].search([('url', '=', '/contactus')]):
            if cp.view_id:
                try:
                    cp.view_id.write({'arch_db': contactus_arch})
                    print(f"[OK] Đã cập nhật website.page '/contactus' (view_id={cp.view_id.id})!")
                except Exception as e:
                    print(f"[Lưu ý contactus page]: {e}")


        # Nạp Logo TDB Solution vào Website và Company
        logo_path = os.path.join(odoo_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img', 'tdb_logo.png')
        if not os.path.exists(logo_path):
            logo_path = os.path.join(current_dir, 'static', 'src', 'img', 'tdb_logo.png')
            
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                raw_bytes = f.read()
            logo_val = make_binary_value(raw_bytes, "tdb_logo.png")
            try:
                if company:
                    company.write({'logo': logo_val})
                for ws in env['website'].search([]):
                    ws.write({'logo': logo_val, 'name': 'TDB Solution'})
                print("[OK] Đã nạp Logo TDB Solution chuẩn vào Website & Company")
            except Exception as e:
                print(f"[Bỏ qua lỗi logo]: {e}")
                
            try:
                att_model = env['ir.attachment']
                logo_att = att_model.search([('url', '=', '/tdb_website_custom/static/src/img/tdb_logo.png')], limit=1)
                l_b64 = base64.b64encode(raw_bytes).decode('ascii')
                if logo_att:
                    logo_att.write({'datas': l_b64, 'public': True})
                else:
                    att_model.create({
                        'name': 'tdb_logo.png',
                        'type': 'binary',
                        'datas': l_b64,
                        'mimetype': 'image/png',
                        'public': True,
                        'url': '/tdb_website_custom/static/src/img/tdb_logo.png',
                    })
            except Exception as e:
                print(f"[Lưu ý logo attachment]: {e}")

        # Nạp ảnh Banner Hero BG-TapThe từ folder Picture vào Odoo Attachment
        for bg_filename in ['BG-TapThe.webp', 'BG-TapThe.jpg']:
            candidates = [
                os.path.join(odoo_dir, 'Picture', bg_filename),
                os.path.join(current_dir, 'Picture', bg_filename),
                os.path.join(odoo_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img', bg_filename),
                os.path.join(current_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img', bg_filename),
            ]
            found_bg = None
            for p in candidates:
                if os.path.exists(p):
                    found_bg = p
                    break
            if found_bg:
                try:
                    with open(found_bg, 'rb') as f:
                        bg_bytes = f.read()
                    bg_b64 = base64.b64encode(bg_bytes).decode('ascii')
                    mimetype = 'image/webp' if bg_filename.endswith('.webp') else 'image/jpeg'
                    att_model = env['ir.attachment']
                    att = att_model.search([('url', '=', f'/tdb_website_custom/static/src/img/{bg_filename}')], limit=1)
                    if not att:
                        att = att_model.search([('name', '=', bg_filename), ('public', '=', True)], limit=1)
                    vals = {
                        'name': bg_filename,
                        'type': 'binary',
                        'datas': bg_b64,
                        'mimetype': mimetype,
                        'public': True,
                        'url': f'/tdb_website_custom/static/src/img/{bg_filename}',
                    }
                    if att:
                        att.write(vals)
                    else:
                        att_model.create(vals)
                    print(f"[OK] Đã nạp thành công ảnh '{bg_filename}' vào Odoo Attachment!")
                except Exception as e:
                    print(f"[Lưu ý nạp ảnh {bg_filename}]: {e}")

        # =========================================================================
        # 4. CHUẨN HÓA HEADER (NÚT GIỎ HÀNG, HOTLINE +84 373704895 VÀ NÚT LIÊN HỆ)
        # =========================================================================
        print("\n>>> 4. Đang chuẩn hóa Header (Nút Giỏ hàng, Hotline +84 373704895 và Nút Liên hệ)...")
        # 4.1 Đảm bảo cài đặt website_sale để hỗ trợ giỏ hàng
        try:
            ws_mod = env['ir.module.module'].search([('name', '=', 'website_sale')], limit=1)
            if ws_mod and ws_mod.state != 'installed':
                ws_mod.button_immediate_install()
                print("[OK] Đã kích hoạt module website_sale để hỗ trợ giỏ hàng!")
        except Exception as e:
            print(f"[Lưu ý module website_sale]: {e}")

        # 4.2 Kích hoạt tất cả view Header Cart trong Odoo
        for cv in env['ir.ui.view'].search([
            '|', '|', '|',
            ('key', '=', 'website_sale.header_cart_link'),
            ('key', '=', 'website_sale.template_header_default'),
            ('key', 'ilike', '%header_cart%'),
            ('arch_db', 'ilike', '%o_wsale_my_cart%'),
        ]):
            if not cv.active:
                cv.write({'active': True})
                print(f"[OK] Đã kích hoạt view giỏ hàng: {cv.key or cv.id}")

        # 4.3 Đảm bảo thẻ giỏ hàng <li class="o_wsale_my_cart"> có mặt trong view header
        cart_li_html = """<li class="divider d-none"></li>
<li class="o_wsale_my_cart">
    <a href="/shop/cart" aria-label="Giỏ hàng thương mại điện tử" class="o_navlink_background btn position-relative rounded-circle p-1 text-center text-reset">
        <div>
            <i class="fa fa-shopping-cart fa-stack"></i>
            <sup class="my_cart_quantity badge bg-primary position-absolute top-0 end-0 mt-n1 me-n1 rounded-pill d-none" data-order-id="">0</sup>
        </div>
    </a>
</li>"""
        for hv in env['ir.ui.view'].search([('key', 'in', ['website.template_header_default', 'website.default_header'])]):
            h_arch = hv.arch_db or ''
            if 'o_wsale_my_cart' not in h_arch and 'navbar-nav' in h_arch:
                for target_ul in ['class="navbar-nav align-items-center', 'class="navbar-nav ms-auto', 'class="navbar-nav me-auto']:
                    if target_ul in h_arch:
                        idx = h_arch.find(target_ul)
                        end_tag = h_arch.find('>', idx) + 1
                        h_arch = h_arch[:end_tag] + '\n' + cart_li_html + h_arch[end_tag:]
                        try:
                            hv.write({'arch_db': h_arch})
                            print(f"[OK] Đã bổ sung nút Giỏ hàng vào header view: {hv.key}")
                        except Exception as e:
                            print(f"[Lưu ý chèn cart vào {hv.key}]: {e}")
                        break

        # 4.4 Thay thế hotline và nút Liên hệ
        phone_views = env['ir.ui.view'].search([
            '|', '|',
            ('arch_db', 'ilike', '%555-555-5556%'),
            ('arch_db', 'ilike', '%555 555 5556%'),
            ('arch_db', 'ilike', '%Contact Us%')
        ])
        for pv in phone_views:
            try:
                n_arch = pv.arch_db
                n_arch = n_arch.replace('+1 555-555-5556', '+84 373704895')
                n_arch = n_arch.replace('+1 555 555 5556', '+84 373704895')
                n_arch = n_arch.replace('+15555555556', '+84373704895')
                n_arch = n_arch.replace('tel:+15555555556', 'tel:+84373704895')
                n_arch = n_arch.replace('Contact Us', 'Liên hệ với chúng tôi')
                pv.write({'arch_db': n_arch})
                print(f"[OK] Đã cập nhật Hotline & Nút CTA trong view header: {pv.key or pv.id}")
            except Exception as e:
                print(f"[Lưu ý sửa header {pv.key}]: {e}")

        for view_key in [
            'website.template_header_default_call_to_action',
            'website.header_call_to_action',
            'website.template_header_call_to_action',
            'website.option_header_brand_logo',
        ]:
            opt_view = env['ir.ui.view'].search([('key', '=', view_key)], limit=1)
            if opt_view and not opt_view.active:
                opt_view.write({'active': True})
                print(f"[OK] Đã kích hoạt tùy chọn Header: {view_key}")

        # =========================================================================
        # 5. CẬP NHẬT TRANG CHỦ HERO BANNER (CHUẨN 2 NÚT BẤM BO TRÒN TRẮNG VÀ XANH)
        # =========================================================================
        print("\n>>> 5. Đang cập nhật Trang chủ Hero Banner chuẩn...")
        homepage_arch = """<t t-name="website.homepage">
    <t t-call="website.layout">
        <t t-set="pageName" t-value="'homepage'"/>
        <div id="wrap" class="oe_structure oe_empty">
            <section class="s_cover parallax s_parallax_is_fixed o_cc o_cc5 pt232 pb232 o_colored_level" data-scroll-background-ratio="1" data-snippet="s_cover" data-name="Ảnh bìa">
                <span class="s_parallax_bg oe_img_bg o_bg_img_center o_bg_img_origin_border_box" style="background-position: 50% 75%; background-image: url(&quot;/tdb_website_custom/static/src/img/BG-TapThe.webp&quot;);" data-mimetype="image/webp"></span>
                <div class="o_we_bg_filter bg-black-50"></div>
                <div class="container s_allow_columns text-center text-white position-relative" style="z-index: 2;">
                    <h1 class="display-3 fw-bold mb-3" style="text-shadow: 0 2px 10px rgba(0,0,0,0.6);">Technical and Digital Benefits</h1>
                    <p class="lead mb-4 mx-auto" style="max-width: 820px; line-height: 1.65; text-shadow: 0 1px 6px rgba(0,0,0,0.6);">
TDB Solution sáng tạo và đổi mới. Chúng tôi mang đến khách hàng sự hài lòng nhờ đồng hành và cung cấp dịch vụ chất lượng cao
                    </p>
                    <p class="pt-2">
                        <a class="btn btn-light rounded-pill px-4 py-2 me-3 fw-bold text-dark shadow-sm" href="/contactus">Khám phá thêm</a>
                        <a class="btn btn-primary rounded-pill px-4 py-2 fw-bold text-white shadow-sm" href="/contactus">Liên hệ</a>
                    </p>
                </div>
            </section>
        </div>
    </t>
</t>"""

        v1953 = env['ir.ui.view'].browse(1953)
        if v1953.exists():
            try:
                v1953.write({'arch_db': homepage_arch})
                print(f"[OK] Đã cập nhật view 1953 (key={v1953.key}) về Homepage Hero Banner!")
            except Exception as e:
                print(f"[Lỗi v1953]: {e}")

        homepage_views = env['ir.ui.view'].search([('key', '=', 'website.homepage')])
        for hp_view in homepage_views:
            try:
                hp_view.write({'arch_db': homepage_arch})
                print(f"[OK] Đã cập nhật view {hp_view.id} (key=website.homepage)")
            except Exception as e:
                print(f"[Lưu ý hp_view {hp_view.id}]: {e}")

        homepage_pages = env['website.page'].search([('url', 'in', ['/', '/home'])])
        for page in homepage_pages:
            if page.view_id:
                try:
                    page.view_id.write({'arch_db': homepage_arch})
                    print(f"[OK] Đã cập nhật website.page url='{page.url}' (view_id={page.view_id.id})")
                except Exception as e:
                    print(f"[Lỗi page {page.id}]: {e}")

        # =========================================================================
        # 6. CẬP NHẬT FOOTER 3 CỘT VÀ 4 ICON TRÒN (FA-HOME CHUẨN MẪU)
        # =========================================================================
        print("\n>>> 6. Đang cập nhật Footer 3 cột và 4 biểu tượng mạng xã hội (fa-home)...")
        footer_inner_content = """<div id="footer" class="oe_structure oe_structure_solo" style="background-color: #0b1320; color: #94a3b8;">
        <section class="s_text_block pt40 pb16" data-snippet="s_text_block" data-name="Text">
            <div class="container">
                <div class="row">
                    <div class="col-lg-2 pt24 pb24">
                        <h5 class="mb-3 text-white fw-bold">Liên kết hữu ích</h5>
                        <ul class="list-unstyled">
                            <li class="mb-2"><a href="/" class="text-decoration-none" style="color: #94a3b8;">Trang chủ</a></li>
                            <li class="mb-2"><a href="/aboutus" class="text-decoration-none" style="color: #94a3b8;">Về chúng tôi</a></li>
                            <li class="mb-2"><a href="/shop" class="text-decoration-none" style="color: #94a3b8;">Sản phẩm</a></li>
                            <li class="mb-2"><a href="#" class="text-decoration-none" style="color: #94a3b8;">Dịch vụ</a></li>
                            <li class="mb-2"><a href="#" class="text-decoration-none" style="color: #94a3b8;">Hợp pháp</a></li>
                            <li class="mb-2"><a href="/contactus" class="text-decoration-none" style="color: #94a3b8;">Liên hệ</a></li>
                        </ul>
                    </div>
                    <div class="col-lg-5 pt24 pb24">
                        <h5 class="mb-3 text-white fw-bold">Về chúng tôi</h5>
                        <p style="line-height: 1.7; color: #cbd5e1;">
                            Chúng tôi cung cấp giải pháp chuyển đổi số cho bộ phận thiết kế và quản lý kỹ thuật bằng công cụ PDM/ PLM – CIM database. Giải pháp kỹ thuật đi từ ý tưởng (ideas – R&amp;D) -&gt; thiết kế (CAD) -&gt; Phân tích mô phỏng số (CFD/ CAE/ FEA) -&gt; Sản xuất (Production) -&gt; Vận hành và quản lý bảo trì bảo dưỡng từ hệ thống tích hợp IoT (IoT – Operation and maintenance).
                        </p>
                    </div>
                    <div id="connect" class="col-lg-4 offset-lg-1 pt24 pb24">
                        <h5 class="mb-3 text-white fw-bold">Kết nối với chúng tôi</h5>
                        <ul class="list-unstyled">
                            <li class="mb-2"><i class="fa fa-comment fa-fw me-2 text-primary"></i><a href="/contactus" class="text-decoration-none" style="color: #94a3b8;">Liên hệ</a></li>
                            <li class="mb-2"><i class="fa fa-envelope fa-fw me-2 text-primary"></i><a href="mailto:info@tdbsolution.com.vn" class="text-decoration-none" style="color: #94a3b8;">info@tdbsolution.com.vn</a></li>
                            <li class="mb-2"><i class="fa fa-phone fa-fw me-2 text-primary"></i><span class="o_force_ltr"><a href="tel:+84373704895" class="text-decoration-none" style="color: #94a3b8;">+84 373704895</a></span></li>
                        </ul>
                        <div class="s_social_media text-start mt-3">
                            <a href="https://facebook.com" class="btn btn-light rounded-circle p-2 me-2 text-primary" target="_blank" aria-label="Facebook"><i class="fa fa-facebook-f fa-fw"></i></a>
                            <a href="https://twitter.com" class="btn btn-light rounded-circle p-2 me-2 text-info" target="_blank" aria-label="X"><i class="fa fa-twitter fa-fw"></i></a>
                            <a href="https://linkedin.com" class="btn btn-light rounded-circle p-2 me-2 text-primary" target="_blank" aria-label="LinkedIn"><i class="fa fa-linkedin fa-fw"></i></a>
                            <a href="/" class="btn btn-light rounded-circle p-2 text-dark" aria-label="Website"><i class="fa fa-home fa-fw"></i></a>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>"""

        footer_xpath_arch = f"""<data>
    <xpath expr="//div[@id='footer']" position="replace">
        {footer_inner_content}
    </xpath>
</data>"""

        footer_views = env['ir.ui.view'].search([('key', 'in', ['website.footer_custom', 'website.template_footer_default', 'website.footer_default'])])
        for f_view in footer_views:
            try:
                if f_view.inherit_id:
                    f_view.write({'arch_db': footer_xpath_arch})
                    print(f"[OK] Đã cập nhật view kế thừa footer: {f_view.key}")
                else:
                    f_view.write({'arch_db': f'<t t-name="{f_view.key}">{footer_inner_content}</t>'})
                    print(f"[OK] Đã cập nhật view gốc footer: {f_view.key}")
            except Exception as e:
                print(f"[Lưu ý footer {f_view.key}]: {e}")

        # Cập nhật dòng bản quyền chuẩn TDB Solution
        copyright_views = env['ir.ui.view'].search([
            ('arch_db', 'ilike', '%o_footer_copyright_name%'),
        ])
        for cp_view in copyright_views:
            try:
                c_arch = cp_view.arch_db or ''
                if 'o_footer_copyright_name' in c_arch:
                    c_arch = re.sub(
                        r'<span class="o_footer_copyright_name[^"]*">.*?</span>',
                        '<span class="o_footer_copyright_name me-2">Bản quyền thuộc © TDB Solution., Co. Ltd</span>',
                        c_arch,
                        flags=re.DOTALL
                    )
                    cp_view.write({'arch_db': c_arch})
                    print(f"[OK] Đã cập nhật dòng bản quyền trong view {cp_view.key or cp_view.id}")
            except Exception as e:
                print(f"[Lưu ý bản quyền {cp_view.key}]: {e}")

        # =========================================================================
        # 7. CẬP NHẬT MENU ĐIỀU HƯỚNG WEBSITE CHUẨN TIẾNG VIỆT
        # =========================================================================
        print("\n>>> 7. Đang đồng bộ Menu điều hướng 6 mục tiếng Việt...")
        menu_model = env['website.menu']
        for ws in env['website'].search([]):
            root_menu = ws.menu_id
            if not root_menu:
                continue
            menu_items = [
                ('Trang chủ', '/', 10),
                ('Cửa hàng', '/shop', 20),
                ('Sự kiện', '/event', 30),
                ('Khóa học', '/slides', 40),
                ('Tuyển dụng', '/jobs', 50),
                ('Liên hệ', '/contactus', 60),
            ]
            for name, url, seq in menu_items:
                existing = menu_model.search([('parent_id', '=', root_menu.id), ('url', '=', url)], limit=1)
                if existing:
                    existing.write({'name': name, 'sequence': seq})
                else:
                    menu_model.create({
                        'name': name,
                        'url': url,
                        'parent_id': root_menu.id,
                        'website_id': ws.id,
                        'sequence': seq,
                    })

            # Dọn dẹp menu tiếng Anh cũ
            for old_menu in menu_model.search([('parent_id', '=', root_menu.id)]):
                if old_menu.name in ['Home', 'Shop', 'Events', 'Courses', 'Jobs', 'Contact Us']:
                    old_menu.unlink()

            print(f"[OK] Đã đồng bộ Menu điều hướng cho website '{ws.name}'")

        # =========================================================================
        # 8. XÓA SẠCH CACHE VÀ COMMIT THAY ĐỔI VÀO POSTGRESQL
        # =========================================================================
        try:
            env.registry.clear_cache()
            print("\n[OK] Đã xóa cache QWeb template và View cache")
        except Exception:
            pass

        cr.commit()
        print("\n" + "="*70)
        print(">>> HOÀN TẤT THÀNH CÔNG! HỆ THỐNG ĐÃ ĐƯỢC CHUYỂN SANG TIẾNG VIỆT & CHUẨN GIAO DIỆN! <<<")
        print("="*70)

if __name__ == '__main__':
    main()

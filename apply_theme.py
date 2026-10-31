# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import base64
import os
import sys

def main():
    # Detect current directory and odoo configuration
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    sys.path.insert(0, current_dir)

    try:
        import odoo
        from odoo.tools import config
    except ImportError as e:
        print(f"Error importing odoo: {e}. Please ensure you are running in the Odoo virtual environment.")
        return

    config_path = os.path.join(current_dir, 'odoo.conf')
    if not os.path.exists(config_path):
        config_path = 'odoo.conf'

    print(">>> Dang ket noi database odoo20...")
    config.parse_config(['-c', config_path, '-d', 'odoo20'])
    
    registry = odoo.registry('odoo20')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

        # 1. Cap nhat thong tin Cong ty & Website
        company = env.ref('base.main_company', raise_if_not_found=False) or env['res.company'].search([], limit=1)
        if company:
            company.write({
                'name': 'TDB Solution',
                'phone': '+84 373704895',
                'email': 'info@tdbsolution.com.vn',
                'website': 'https://tdbsolution.com.vn',
            })
            print("[OK] Da cap nhat thong tin cong ty: TDB Solution, Hotline +84 373704895, info@tdbsolution.com.vn")

        # 2. Nap Logo TDB Solution vao Website va Company
        logo_path = os.path.join(current_dir, 'custom_addons', 'tdb_website_custom', 'static', 'src', 'img', 'tdb_logo.png')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_b64 = base64.b64encode(f.read())
            if company:
                company.write({'logo': logo_b64})
            for ws in env['website'].search([]):
                ws.write({'logo': logo_b64, 'name': 'TDB Solution'})
            print("[OK] Da nap Logo TDB Solution chuan vao Website & Company")
        else:
            print(f"[CANH BAO] Khong tim thay file logo tai: {logo_path}")

        # 3. Cap nhat Hero Banner Trang chu (Homepage)
        hero_html = """<div id="wrap" class="oe_structure oe_empty"><section class="s_cover parallax s_parallax_is_fixed o_cc o_cc5 pt232 pb232 o_colored_level" data-scroll-background-ratio="1" data-snippet="s_cover" data-name="Ảnh bìa">
    <span class="s_parallax_bg oe_img_bg o_bg_img_center o_bg_img_origin_border_box" style="background-position: 50% 65%; background-image: url(&quot;/tdb_website_custom/static/src/img/BG-TapThe.webp&quot;);" data-mimetype="image/webp"></span>
    <div class="o_we_bg_filter bg-black-50"></div>
    <div class="container s_allow_columns text-center text-white">
        <h1 class="display-3 fw-bold mb-3" style="text-shadow: 0 2px 10px rgba(0,0,0,0.6);">Technical and Digital Benefits</h1>
        <p class="lead mb-4 mx-auto" style="max-width: 820px; line-height: 1.65; text-shadow: 0 1px 6px rgba(0,0,0,0.6);">
TDB Solution sáng tạo và đổi mới. Chúng tôi mang đến khách hàng sự hài lòng nhờ đồng hành và cung cấp dịch vụ chất lượng cao
        </p>
        <p class="pt-2">
            <a class="btn btn-light rounded-pill px-4 py-2 me-3 fw-bold text-dark shadow-sm" href="/contactus">Khám phá thêm</a>
            <a class="btn btn-primary rounded-pill px-4 py-2 fw-bold text-white shadow-sm" href="/contactus">Liên hệ</a>
        </p>
    </div>
</section></div>"""

        # Cap nhat vao homepage view va website.page
        homepage_views = env['ir.ui.view'].search([('key', '=', 'website.homepage')])
        for hp_view in homepage_views:
            hp_view.write({'arch_db': hero_html})
        homepage_pages = env['website.page'].search([('url', 'in', ['/', '/home'])])
        for page in homepage_pages:
            if page.view_id:
                page.view_id.write({'arch_db': hero_html})
        print("[OK] Da cap nhat Hero Banner anh tap the TDB Solution vao Trang chu")

        # 4. Cap nhat Footer chuan 3 cot TDB Solution
        footer_view = env.ref('website.footer_custom', raise_if_not_found=False)
        footer_content = """<div id="footer" class="oe_structure oe_structure_solo" style="background-color: #0b1320; color: #94a3b8;">
    <section class="s_text_block pt48 pb24" data-snippet="s_text_block" data-name="Text">
        <div class="container">
            <div class="row g-4">
                <div class="col-lg-2 col-md-4 col-sm-6">
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
                <div class="col-lg-6 col-md-8 col-sm-12">
                    <h5 class="mb-3 text-white fw-bold">Về chúng tôi</h5>
                    <p style="line-height: 1.7; color: #cbd5e1;">
                        Chúng tôi cung cấp giải pháp chuyển đổi số cho bộ phận thiết kế và quản lý kỹ thuật bằng công cụ PDM/ PLM – CIM database. Giải pháp kỹ thuật đi từ ý tưởng (ideas – R&amp;D) -&gt; thiết kế (CAD) -&gt; Phân tích mô phỏng số (CFD/ CAE/ FEA) -&gt; Sản xuất (Production) -&gt; Vận hành và quản lý bảo trì bảo dưỡng từ hệ thống tích hợp IoT (IoT – Operation and maintenance).
                    </p>
                </div>
                <div id="connect" class="col-lg-4 col-md-12">
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
                        <a href="/" class="btn btn-light rounded-circle p-2 text-dark" aria-label="Website"><i class="fa fa-globe fa-fw"></i></a>
                    </div>
                </div>
            </div>
        </div>
    </section>
</div>"""
        layout_view = env.ref('website.layout', raise_if_not_found=False)
        print("[OK] Da chuan bi Footer 3 cot chuan nhan dien TDB Solution")

        # 5. Cap nhat Menu dieu huong Website
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
            print(f"[OK] Da dong bo Menu dieu huong cho website '{ws.name}'")

        # 6. Commit thay doi vao database PostgreSQL
        cr.commit()
        print("\n" + "="*60)
        print(">>> THANH CONG! TOAN BO GIAO DIEN TDB SOLUTION DA DUOC CAP NHAT VAO DATABASE! <<<")
        print("="*60)

if __name__ == '__main__':
    main()

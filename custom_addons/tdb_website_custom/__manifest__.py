# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
{
    'name': 'TDB Website Theme & Customization',
    'version': '1.0',
    'category': 'Website/Theme',
    'summary': 'Tùy biến giao diện Website, Trang chủ Hero Banner, Header, Footer và các trang chuẩn nhận diện TDB Solution',
    'description': """
Module tùy biến giao diện Website theo chuẩn kiến trúc phân tầng Odoo:
- Header: Logo TDB Solution, Nút Giỏ Hàng (Cart Icon), Ô tìm kiếm, Hotline +84 373704895 và Nút "Liên hệ với chúng tôi".
- Trang chủ (Homepage): Hero Banner ảnh tập thể TDB Solution Full HD kèm khẩu hiệu nhận diện và 2 nút bấm bo tròn (Khám phá thêm - Liên hệ).
- Chân trang (Footer): Thiết kế 3 cột chuyên nghiệp (Liên kết hữu ích, Về chúng tôi, Kết nối với chúng tôi) kèm 4 icon mạng xã hội và thông tin bản quyền chuẩn TDB Solution Co., Ltd.
- Trang liên hệ (Contact Us): Biểu mẫu gửi thư tiếng Việt và Cột thông tin liên hệ chuẩn 3 icon (Địa chỉ, Hotline, Email).
- Trang tuyển dụng (Jobs): Chuẩn hóa thông tin liên hệ và nhận diện thương hiệu TDB Solution.
- Tuân thủ nghiêm ngặt quy tắc kiến trúc phân tầng tại .agents/rules/AGENTS.md và odoo_customization_rules.md.
    """,
    'author': 'TDB Solution',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'website_sale',
    ],
    'data': [
        'data/website_menu_data.xml',
        'views/website_header_templates.xml',
        'views/website_homepage_templates.xml',
        'views/website_footer_templates.xml',
        'views/website_contactus_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'tdb_website_custom/static/src/scss/website_custom.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
{
    'name': 'TDB Solution Theme & Customization',
    'version': '2.0',
    'category': 'Theme/Corporate',
    'summary': 'Tùy biến giao diện Đăng nhập TDB Solution Giá Trị Cốt Lõi chuẩn thiết kế Hình 1 và Logo Hình 2',
    'description': """
Module tùy biến giao diện TDB Solution:
- Trang Đăng nhập (/web/login): Thiết kế chia 2 cột tỉ lệ 8:2 chuẩn xác:
  + Cột trái (80%): Ảnh nền tập thể HD từ thư mục Picture (BG-TapThe.webp).
  + Cột phải (20%): Form đăng nhập TDB Solution sang trọng, tối giản, bo góc chuẩn mực với nút gradient vàng đồng.
- Bỏ toàn bộ danh mục menu (Trang chủ, Cửa hàng, Sự kiện, Khóa học, Tuyển dụng, Liên hệ) và nút Giỏ hàng trên thanh điều hướng.
- Điều hướng trang chủ: Tự động chuyển hướng URL trình duyệt sang thẳng trang Đăng nhập (/web/login).
    """,
    'author': 'TDB Solution',
    'license': 'LGPL-3',
    'depends': [
        'web',
        'website',
    ],
    'data': [
        'views/login_templates.xml',
        'views/website_header_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'tdb_website_custom/static/src/scss/abstract/_variables.scss',
            'tdb_website_custom/static/src/scss/base/_reset.scss',
            'tdb_website_custom/static/src/scss/layout/_wrapper.scss',
            'tdb_website_custom/static/src/scss/components/_presentation.scss',
            'tdb_website_custom/static/src/scss/components/_login_card.scss',
            'tdb_website_custom/static/src/scss/layout/_responsive.scss',
            'tdb_website_custom/static/src/scss/login_custom.scss',
            'tdb_website_custom/static/src/js/tdb_login_security.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

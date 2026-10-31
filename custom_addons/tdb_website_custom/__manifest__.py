# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
{
    'name': 'TDB Website Theme & Customization',
    'version': '1.0',
    'category': 'Website/Theme',
    'summary': 'Tùy biến giao diện Website, Trang chủ Hero Banner, Header và Footer chuẩn TDB Solution',
    'description': """
Module tùy biến giao diện Website cho TDB Solution:
- Header: Logo TDB Solution chuẩn, menu điều hướng đầy đủ, số hotline và nút bấm "Liên hệ với chúng tôi".
- Trang chủ (Homepage): Hero Banner ảnh tập thể TDB Solution Full HD với lớp phủ gradient tối và khẩu hiệu:
  "Technical and Digital Benefits - TDB Solution sáng tạo và đổi mới...".
- Chân trang (Footer): Thiết kế 3 cột chuyên nghiệp (Liên kết hữu ích, Về chúng tôi, Kết nối với chúng tôi)
  kèm các biểu tượng mạng xã hội và thông tin bản quyền chuẩn TDB Solution Co., Ltd.
- Tuân thủ kiến trúc phân tầng chuẩn Odoo tại .agents/rules/AGENTS.md.
    """,
    'author': 'TDB Solution',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'data/website_menu_data.xml',
        'views/website_templates.xml',
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

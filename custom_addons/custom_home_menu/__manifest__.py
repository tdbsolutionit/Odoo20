# -*- coding: utf-8 -*-
{
    'name': 'Enterprise Style Home Menu (Menu 9 Chấm)',
    'version': '1.0',
    'category': 'Customization',
    'summary': 'Chuyển đổi giao diện Home Menu và thanh điều hướng 9 chấm phong cách Enterprise',
    'description': """
Module Home Menu 9 chấm:
- Bổ sung nút 9 chấm trên thanh navbar chuyển đổi sang chế độ xem ứng dụng toàn màn hình.
- Tìm kiếm nhanh ứng dụng theo thời gian thực (hỗ trợ phím tắt Enter, Escape).
- Giao diện hiện đại phong cách Odoo Enterprise với icon bo góc bóng bẩy.
- Đóng gói hoàn chỉnh dạng module độc lập trong custom_addons, không can thiệp mã nguồn core Odoo.
    """,
    'author': 'TDB Solution',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            ('prepend', 'custom_home_menu/static/src/js/clipboard_polyfill.js'),
            'custom_home_menu/static/src/scss/home_menu.scss',
            'custom_home_menu/static/src/xml/home_menu.xml',
            'custom_home_menu/static/src/js/home_menu.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

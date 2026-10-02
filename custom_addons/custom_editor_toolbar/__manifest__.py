{
    'name': 'Custom Editor Toolbar & WYSIWYG Enhancements',
    'version': '1.0',
    'category': 'Customization',
    'summary': 'Thanh công cụ soạn thảo cố định phía trên cho modal, nút +/- cỡ chữ, font selector',
    'description': """
Module chuẩn hóa giao diện Odoo 20:
- Cố định thanh công cụ soạn thảo HTML Editor (Stationary Toolbar) trong modal/popup.
- Bổ sung nút tăng giảm cỡ chữ (+) và (−) trực quan.
- Tùy chỉnh bộ chọn kiểu chữ và tổ chức nhóm nút khoa học.
    """,
    'author': 'Antigravity / Odoo Team',
    'depends': ['web', 'html_editor', 'sale'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_editor_toolbar/static/src/scss/font_size_selector.scss',
            'custom_editor_toolbar/static/src/xml/wysiwyg_templates.xml',
            'custom_editor_toolbar/static/src/js/wysiwyg_patch.js',
            'custom_editor_toolbar/static/src/js/toolbar_plugin_patch.js',
            'custom_editor_toolbar/static/src/js/font_size_patch.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

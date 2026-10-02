{
    'name': 'TDB Sales Customization & Quotation Report',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Tùy biến quy trình Báo giá, Popup điều khoản & Mẫu in Báo giá chuẩn TDB Solution',
    'description': """
Module tùy biến riêng cho TDB SOLUTION:
- Mẫu in Báo giá (Quotation PDF) chuẩn nhận diện TDB Solution kèm Logo và bảng điều khoản.
- Quy trình: Báo giá -> Đặt hàng -> Đơn bán hàng.
- Popup xem trước Báo giá (Preview Modal 95vw).
- Popup tùy chỉnh Điều khoản & Điều kiện với 4 mục mặc định (BIDV).
- Nút xóa sản phẩm an toàn (kiểm tra Combo và Lịch sử bán hàng).
    """,
    'author': 'TDB Solution',
    'depends': ['sale', 'product', 'web'],
    'data': [
        'report/ir_actions_report.xml',
        'report/sale_report_templates.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tdb_sale_custom/static/src/scss/sale_preview.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
{
    "name": "TDB PLM Customization - Giao diện & Access Token 180 Ngày SolidWorks",
    "version": "20.0.1.1.0",
    "category": "Manufacturing/Product Lifecycle Management (PLM)",
    "summary": "Tùy biến chuẩn hóa PLM, Access Token 180 ngày cho SolidWorks 2022 Add-in và giao diện thu hồi từ xa",
    "description": """
TDB Solution - Module tùy biến phân hệ PLM (Product Lifecycle Management)
========================================================================
Tính năng chính:
1. Chuẩn hóa 100% tiêu đề cột trên danh sách linh kiện kỹ thuật (Engineering Parts) song ngữ Anh - Việt.
2. Tự động cấp Access Token & Session Cookie 180 ngày (15,552,000s) cho Add-in CAD SolidWorks 2022 (PLM Omi).
3. Model plm.desktop.token quản lý đa thiết bị, lưu IP, tên máy trạm CAD, thời hạn 180 ngày và lần truy cập cuối.
4. Giao diện Backend quản trị: Menu PLM -> Cấu hình -> Desktop Access Tokens, tích hợp nút bấm đỏ 'Thu hồi quyền (Revoke)' từ xa.
5. Cơ chế bảo vệ thời gian thực: Tự động ngắt kết nối và trả về 401 Unauthorized khi token bị thu hồi hoặc hết hạn.
6. Căn lề chuẩn hóa SCSS và thanh cuộn ngang mượt mà cho bảng linh kiện.
    """,
    "author": "TDB Solution",
    "website": "https://tdbsolution.com",
    "license": "LGPL-3",
    "depends": [
        "plm",
        "product",
    ],
    "data": [
        "security/ir.access.csv",
        "views/plm_component_views.xml",
        "views/plm_document_views.xml",
        "views/plm_desktop_token_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "tdb_plm_custom/static/src/scss/plm_variables.scss",
            "tdb_plm_custom/static/src/scss/plm_table_layout.scss",
            "tdb_plm_custom/static/src/scss/plm_table_header.scss",
            "tdb_plm_custom/static/src/scss/plm_table_cells.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}

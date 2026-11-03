# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
{
    "name": "TDB PLM Customization - Giao diện & Tiêu đề Song ngữ PLM",
    "version": "20.0.1.0.0",
    "category": "Manufacturing/Product Lifecycle Management (PLM)",
    "summary": "Tùy biến chuẩn hóa giao diện danh sách linh kiện PLM, tiêu đề song ngữ Anh - Việt và căn lề đồng đều",
    "description": """
TDB Solution - Module tùy biến phân hệ PLM (Product Lifecycle Management)
========================================================================
Tính năng chính:
1. Chuẩn hóa 100% tiêu đề cột trên danh sách linh kiện kỹ thuật (Engineering Parts):
   - Image (Hình ảnh)
   - Name (Tên)
   - Engineering Code (Mã kỹ thuật)
   - Internal Reference (Tham chiếu nội bộ)
   - Engineering Revision (Phiên bản kỹ thuật)
   - Engineering Status (Trạng thái kỹ thuật)
   - Description (Mô tả)
   - Writable (Có thể chỉnh sửa)
   - CAD Raw Material (Vật liệu thô CAD)
   - CAD Surface Finishing (Hoàn thiện bề mặt CAD)
   - Linked Documents (Tài liệu liên kết)
   - Checked-Out By (Được kiểm xuất bởi)
2. Căn lề chuẩn hóa, đồng đều cho cả tiêu đề cột và ô dữ liệu.
3. Thiết lập độ rộng cột tối thiểu và thanh cuộn ngang mượt mà, khắc phục triệt để tình trạng cắt chữ.
4. Tách tầng CSS theo 5 tệp modular độc lập, an toàn tuyệt đối không gây lỗi Sass compiler.
    """,
    "author": "TDB Solution",
    "website": "https://tdbsolution.com",
    "license": "LGPL-3",
    "depends": [
        "plm",
        "product",
    ],
    "data": [
        "views/plm_component_views.xml",
        "views/plm_document_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "tdb_plm_custom/static/src/css/variables.css",
            "tdb_plm_custom/static/src/css/typography.css",
            "tdb_plm_custom/static/src/css/table_layout.css",
            "tdb_plm_custom/static/src/css/table_header.css",
            "tdb_plm_custom/static/src/css/table_cells.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}

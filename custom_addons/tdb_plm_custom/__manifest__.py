# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
{
    "name": "TDB PLM Customization - Giao diện & Access Token 180 Ngày SolidWorks",
    "version": "20.0.1.3.4",
    "category": "Manufacturing/Product Lifecycle Management (PLM)",
    "summary": "Tùy biến chuẩn hóa PLM, Document Lock Key Holder, File History và Access Token 180 ngày SolidWorks",
    "description": """
TDB Solution - Module tùy biến phân hệ PLM (Product Lifecycle Management)
========================================================================
Tính năng chính:
1. Chuẩn hóa 100% tiêu đề cột trên danh sách linh kiện kỹ thuật (Engineering Parts) song ngữ Anh - Việt.
2. Cơ chế khóa tài liệu theo Kiến trúc Người giữ Key (Key Holder Architecture):
   - Kỹ sư đầu tiên tạo / check-in tài liệu từ máy trạm sẽ giữ Key độc quyền.
   - Mọi kỹ sư đều được quyền Check-out tải file về máy trạm phục vụ thiết kế, tham chiếu.
   - Duy nhất kỹ sư giữ Key mới được quyền Check-in cập nhật file lên máy chủ.
   - Quản trị viên / Trưởng phòng có quyền Phá khóa cưỡng chế (Force Unlock) và chuyển giao Key qua Wizard có ghi nhận nhật ký kiểm toán.
3. Lịch sử phiên bản tệp (Task T4 File History): Tự động lưu snapshot phiên bản cũ (v1, v2,...) khi Check-in.
4. Tự động cấp Access Token & Session Cookie 180 ngày cho Add-in CAD SolidWorks 2022.
    """,
    "author": "TDB Solution",
    "website": "https://tdbsolution.com",
    "license": "LGPL-3",
    "depends": [
        "plm",
        "product",
    ],
    "data": [
        "security/plm_desktop_token_security.xml",
        "security/ir.access.csv",
        "wizard/plm_transfer_key_wizard_views.xml",
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

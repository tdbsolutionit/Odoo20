# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Kịch bản tự động hóa nâng cấp TOÀN BỘ các module Custom của TDB Solution trên Server:
- tdb_plm_custom (Phân hệ PLM: giao diện song ngữ Anh - Việt, căn lề đồng đều, SCSS Odoo)
- tdb_slides_custom (Phân hệ eLearning: Video từ ổ đĩa máy chủ, xem video fullscreen, i18n)
- tdb_dms_custom (Phân hệ DMS: Thư mục con, Thùng rác khôi phục file, i18n)
- tdb_website_custom (Giao diện đăng nhập chuẩn doanh nghiệp TDB Solution, i18n)
- custom_home_menu (Menu chính Odoo tùy biến)
- custom_editor_toolbar (Thanh công cụ soạn thảo phong phú)
"""
from update_plm import main

if __name__ == '__main__':
    main()

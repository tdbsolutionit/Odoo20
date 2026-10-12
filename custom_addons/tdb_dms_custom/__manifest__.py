# -*- coding: utf-8 -*-
{
    'name': 'TDB DMS Customization - Subfolders & Recycle Bin',
    'version': '1.0',
    'category': 'Document Management',
    'summary': 'Tạo thư mục con trong phòng ban & Thùng rác khôi phục file dành cho Admin',
    'description': """
Module tùy biến DMS cho TDB Solution:
1. Chức năng tạo thư mục con chứa file trong phòng ban (có quyền bật/tắt tải về).
2. Phòng ban Thùng Rác (Recycle Bin) bảo mật:
   - Chỉ Sếp/Admin mới có quyền truy cập.
   - Khi xóa file, file được tự động chuyển vào Thùng Rác (kèm tên người xóa, thời gian xóa, thư mục gốc).
   - Sếp/Admin có quyền Khôi phục (Restore) về thư mục ban đầu hoặc Xóa vĩnh viễn.
    """,
    'author': 'TDB Solution',
    'depends': ['dms', 'base', 'web', 'mail'],
    'data': [
        'security/ir.access.csv',
        'data/recycle_bin_data.xml',
        'views/create_subfolder_wizard_views.xml',
        'views/file_date_filter_wizard_views.xml',
        'views/directory_views.xml',
        'views/dms_file_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    slide_base_video_path = fields.Char(
        string='Thư mục Video Gốc trên Máy tính',
        config_parameter='tdb_slides_custom.base_video_path',
        default='/mnt/videos',
        help='Đường dẫn thư mục gốc trên server (mặc định /mnt/videos tương ứng thư mục videos trong dự án trên máy tính). '
             'Người dùng có thể tạo các thư mục con trong Odoo để quản lý video theo từng khóa học mà không cần can thiệp code.'
    )
    iis_media_server_url = fields.Char(
        string='URL Máy chủ Video IIS',
        config_parameter='tdb_slides_custom.iis_media_url',
        default='',
        help='Địa chỉ máy chủ IIS chuyên phát video tĩnh (ví dụ: http://localhost:8088 hoặc http://192.168.1.50:8088). '
             'Nếu cấu hình, trình phát E-Learning sẽ lấy video trực tiếp từ IIS để tua siêu mượt và không làm nặng Odoo. '
             'Nếu để trống, Odoo sẽ tự stream video từ ổ đĩa.'
    )


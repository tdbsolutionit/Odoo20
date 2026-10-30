# -*- coding: utf-8 -*-
{
    'name': 'TDB eLearning Customization - Video Ổ đĩa Máy tính',
    'version': '1.0',
    'category': 'Website/eLearning',
    'summary': 'Chỉ định thư mục video ổ đĩa cho từng khóa học, người dùng tự chọn video và phát stream',
    'description': """
Module tùy biến eLearning (Học trực tuyến) cho TDB Solution:
1. Cho phép người dùng tự chỉ định hoặc tạo Thư mục Video trên ổ đĩa máy tính cho từng khóa học mà không bị khóa cứng code.
2. Trong mỗi khóa học, người dùng chỉ được chọn những video có sẵn trong thư mục mà khóa học đó quản lý.
3. Người dùng chủ động chọn video cần đưa lên thành bài học (không tự động tải lên ồ ạt).
4. Khi chọn video, có giao diện nhập đầy đủ thông tin: Tên bài học, Chương/Phần học, Thời lượng, Cho phép xem thử, Thứ tự, Mô tả.
5. Khi xóa bài học trên Odoo, file video vật lý trên ổ đĩa KHÔNG bị xóa.
6. Phát video trực tiếp từ ổ đĩa qua HTTP 206 Partial Content (tua nhanh mượt mà) hỗ trợ cả chế độ xem thường và toàn màn hình (Fullscreen).
    """,
    'author': 'TDB Solution',
    'depends': ['website_slides', 'base', 'web'],
    'data': [
        'security/ir.access.csv',
        'views/slide_video_folder_views.xml',
        'views/slide_channel_views.xml',
        'views/slide_slide_views.xml',
        'views/slide_question_views.xml',
        'wizard/slide_add_video_wizard_views.xml',
        'wizard/slide_host_folder_browser_views.xml',
        'views/res_config_settings_views.xml',
        'views/website_slides_embed_template.xml',
        'views/website_slides_templates_course.xml',
        'views/website_slides_quiz_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tdb_slides_custom/static/src/js/slide_video_uploader.js',
            'tdb_slides_custom/static/src/xml/slide_video_uploader.xml',
        ],
        'web.assets_frontend': [
            'tdb_slides_custom/static/src/css/slide_quiz_custom.css',
            'tdb_slides_custom/static/src/xml/website_slides_fullscreen.xml',
            'tdb_slides_custom/static/src/js/website_slides_folder_video.js',
            'tdb_slides_custom/static/src/js/website_slides_quiz_custom.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

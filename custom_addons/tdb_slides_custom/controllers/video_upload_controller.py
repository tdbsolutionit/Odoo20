# -*- coding: utf-8 -*-
import base64
import json
import logging
import os
import re
import shutil
import tempfile
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class VideoUploadController(http.Controller):

    @http.route('/slides/upload_video_chunk', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_video_chunk(self, **kwargs):
        """Tiếp nhận từng phân đoạn (chunk) video từ trình duyệt và ghi trực tiếp vào ổ đĩa máy tính/server"""
        try:
            upload_id = (kwargs.get('upload_id') or '').strip()
            channel_id = int(kwargs.get('channel_id') or 0)
            chunk_index = int(kwargs.get('chunk_index') or 0)
            total_chunks = int(kwargs.get('total_chunks') or 1)
            raw_filename = kwargs.get('filename') or 'video.mp4'
            filename = os.path.basename(raw_filename).replace('/', '').replace('\\', '').strip() or 'video.mp4'
            lesson_name = (kwargs.get('lesson_name') or '').strip()
            folder_name = (kwargs.get('folder_name') or '').strip()
            category_id = int(kwargs.get('category_id') or 0) or False
            chunk_file = request.httprequest.files.get('chunk')

            if not channel_id or not upload_id or not chunk_file:
                return request.make_response(
                    json.dumps({'error': 'Thiếu tham số bắt buộc'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            channel = request.env['slide.channel'].sudo().browse(channel_id)
            if not channel.exists():
                return request.make_response(
                    json.dumps({'error': 'Khóa học không tồn tại'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )

            base_path = request.env['slide.video.folder']._get_base_video_path()

            # Xác định thư mục đích trên ổ đĩa
            if folder_name and folder_name != channel.video_folder_path:
                channel.write({'video_folder_path': folder_name})
                folder_obj = channel._ensure_video_folder()
                target_folder_path = folder_obj.full_path
            elif channel.video_folder_id and channel.video_folder_id.full_path:
                target_folder_path = channel.video_folder_id.full_path
            elif channel.video_folder_path:
                folder_obj = channel._ensure_video_folder()
                target_folder_path = folder_obj.full_path
            else:
                sub = folder_name or channel.name
                safe_sub = re.sub(r'[^\w\-_\. ]', '_', sub).strip() or f"channel_{channel.id}"
                channel.write({'video_folder_path': safe_sub})
                folder_obj = channel._ensure_video_folder()
                target_folder_path = folder_obj.full_path or os.path.join(base_path, safe_sub)

            # Đảm bảo thư mục đích tồn tại
            try:
                os.makedirs(target_folder_path, exist_ok=True)
            except PermissionError:
                return request.make_response(
                    json.dumps({'error': f'Không có quyền tạo hoặc ghi vào thư mục: {target_folder_path}'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            # Ghi chunk vào file tạm trong thư mục tạm hệ thống (luôn luôn có quyền ghi)
            temp_dir = os.path.join(tempfile.gettempdir(), 'odoo_video_chunks')
            os.makedirs(temp_dir, exist_ok=True)
            safe_id = re.sub(r'[^\w\-]', '_', upload_id)
            temp_file_path = os.path.join(temp_dir, f"{safe_id}.part")

            mode = 'wb' if chunk_index == 0 else 'ab'
            with open(temp_file_path, mode) as f:
                while True:
                    buf = chunk_file.read(65536)
                    if not buf:
                        break
                    f.write(buf)

            # Khi đến chunk cuối cùng -> di chuyển file vào thư mục đích
            if chunk_index >= total_chunks - 1:
                final_file_path = os.path.join(target_folder_path, filename)
                if os.path.exists(final_file_path):
                    try:
                        os.remove(final_file_path)
                    except Exception:
                        pass
                shutil.move(temp_file_path, final_file_path)

                # Cập nhật số liệu thư mục
                if channel.video_folder_id:
                    channel.video_folder_id._compute_folder_stats()
                channel._compute_folder_stats()

                # Xử lý Chương / Phần học (Category)
                category_name = (kwargs.get('category_name') or '').strip()
                if category_name and not category_id:
                    existing_cat = request.env['slide.slide'].sudo().search([
                        ('channel_id', '=', channel.id),
                        ('is_category', '=', True),
                        ('name', '=ilike', category_name),
                    ], limit=1)
                    if existing_cat:
                        category_id = existing_cat.id
                    else:
                        slides = request.env['slide.slide'].sudo().search([('channel_id', '=', channel.id)])
                        cat_seq = (max(slides.mapped('sequence') or [0])) + 1
                        new_cat = request.env['slide.slide'].sudo().create({
                            'name': category_name,
                            'channel_id': channel.id,
                            'is_category': True,
                            'sequence': cat_seq,
                            'is_published': True,
                        })
                        category_id = new_cat.id

                # Tạo bài học slide.slide nếu chưa có
                clean_title = lesson_name or os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').strip().title()
                existing_slide = request.env['slide.slide'].sudo().search([
                    ('channel_id', '=', channel.id),
                    ('local_video_filename', '=', filename),
                ], limit=1)

                minutes = float(kwargs.get('duration_minutes') or 15)
                completion_time = max(0.01, round(minutes / 60.0, 2))
                desc = (kwargs.get('description') or '').strip()

                if not existing_slide:
                    slides = request.env['slide.slide'].sudo().search([('channel_id', '=', channel.id)])
                    next_seq = (max(slides.mapped('sequence') or [0])) + 1
                    new_slide = request.env['slide.slide'].sudo().create({
                        'name': clean_title,
                        'channel_id': channel.id,
                        'category_id': category_id or False,
                        'slide_category': 'video',
                        'is_local_video': True,
                        'local_video_filename': filename,
                        'completion_time': completion_time,
                        'description': desc or False,
                        'sequence': next_seq,
                        'is_published': True,
                    })
                    slide_record = new_slide
                    slide_id = new_slide.id
                else:
                    vals = {
                        'name': clean_title,
                        'completion_time': completion_time,
                    }
                    if desc:
                        vals['description'] = desc
                    if category_id:
                        vals['category_id'] = category_id
                    existing_slide.write(vals)
                    slide_record = existing_slide
                    slide_id = existing_slide.id

                # Resequence nếu có category_id để bài học vào đúng chương
                if category_id:
                    cat_record = request.env['slide.slide'].sudo().browse(category_id)
                    if cat_record.exists():
                        channel._resequence_slides(slide_record, force_category=cat_record)

                return request.make_response(
                    json.dumps({'success': True, 'done': True, 'slide_id': slide_id, 'filename': filename}),
                    headers=[('Content-Type', 'application/json')]
                )

            return request.make_response(
                json.dumps({'success': True, 'done': False, 'chunk_index': chunk_index}),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.exception("Lỗi khi tải video chunk: %s", e)
            return request.make_response(
                json.dumps({'error': f"Lỗi máy chủ khi lưu video: {str(e)}"}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

    @http.route('/slides/resource/upload', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_slide_resource(self, **kwargs):
        """Cho phép người hướng dẫn / admin đính kèm tài liệu học tập vào bài học video"""
        slide_id = int(kwargs.get('slide_id') or 0)
        slide = request.env['slide.slide'].sudo().browse(slide_id)
        if not slide.exists():
            return request.make_response(
                json.dumps({'error': 'Bài học không tồn tại'}),
                headers=[('Content-Type', 'application/json')],
                status=404
            )

        file = request.httprequest.files.get('file')
        res_name = (kwargs.get('name') or '').strip()
        link_url = (kwargs.get('link') or '').strip()

        try:
            if file:
                raw_data = file.read()
                encoded = base64.b64encode(raw_data)
                filename = os.path.basename(file.filename or 'tai_lieu')
                new_resource = request.env['slide.slide.resource'].sudo().create({
                    'slide_id': slide.id,
                    'resource_type': 'file',
                    'name': res_name or filename,
                    'file_name': filename,
                    'data': encoded,
                })
            elif link_url:
                new_resource = request.env['slide.slide.resource'].sudo().create({
                    'slide_id': slide.id,
                    'resource_type': 'url',
                    'name': res_name or link_url,
                    'link': link_url,
                })
            else:
                return request.make_response(
                    json.dumps({'error': 'Vui lòng chọn file tải lên hoặc nhập đường dẫn link tài liệu'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            dl_url = new_resource.download_url or f'/web/content/slide.slide.resource/{new_resource.id}/data?download=true'
            return request.make_response(
                json.dumps({
                    'success': True,
                    'resource': {
                        'id': new_resource.id,
                        'name': new_resource.name,
                        'file_name': new_resource.file_name or '',
                        'resource_type': new_resource.resource_type,
                        'download_url': dl_url,
                        'link': new_resource.link or '',
                    }
                }),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.exception("Lỗi đính kèm tài liệu vào bài học: %s", e)
            return request.make_response(
                json.dumps({'error': f'Lỗi lưu tài liệu: {str(e)}'}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

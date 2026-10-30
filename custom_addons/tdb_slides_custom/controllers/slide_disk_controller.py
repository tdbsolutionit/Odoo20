# -*- coding: utf-8 -*-
import logging
import os
import re
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SlideDiskController(http.Controller):

    @http.route('/slides/get_channel_disk_videos', type='jsonrpc', auth='user', methods=['POST'])
    def get_channel_disk_videos(self, channel_id, **kwargs):
        """Quét và trả về danh sách các file video đang có sẵn trong thư mục ổ đĩa của khóa học"""
        channel = request.env['slide.channel'].sudo().browse(int(channel_id))
        if not channel.exists():
            return {'error': 'Khóa học không tồn tại'}

        # Lấy danh sách các Chương/Phần học đang có trong khóa học
        categories = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', channel.id),
            ('is_category', '=', True),
        ], order='sequence, id')
        cat_list = [{'id': c.id, 'name': c.name} for c in categories]

        folder = channel._ensure_video_folder()
        if not folder or not folder.full_path or not os.path.exists(folder.full_path):
            return {
                'channel_id': channel.id,
                'channel_name': channel.name,
                'folder_name': channel.video_folder_path or '',
                'folder_display': channel.video_folder_disk_display or '',
                'exists': False,
                'categories': cat_list,
                'videos': []
            }

        video_files = folder.get_video_files()
        existing_slides = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', channel.id),
            ('is_local_video', '=', True),
        ])
        existing_filenames = set(existing_slides.mapped('local_video_filename') or [])

        result_videos = []
        host_folder = channel.video_folder_disk_display or folder.folder_path
        for vf in video_files:
            fpath = os.path.join(folder.full_path, vf)
            size_mb = 0.0
            if os.path.exists(fpath):
                size_mb = os.path.getsize(fpath) / (1024 * 1024)

            base_name, _ext = os.path.splitext(vf)
            clean_title = re.sub(r'[_\-]+', ' ', base_name).strip().title()
            already = vf in existing_filenames

            existing_s = existing_slides.filtered(lambda s: s.local_video_filename == vf)[:1] if already else None
            slide_id = existing_s.id if existing_s else 0
            if existing_s:
                clean_title = existing_s.name or clean_title
                cat_id = existing_s.category_id.id if existing_s.category_id else 0
                cat_name = existing_s.category_id.name if existing_s.category_id else ''
                duration_mins = round((existing_s.completion_time or 0.25) * 60)
                description = existing_s.description or ''
            else:
                cat_id = 0
                cat_name = ''
                duration_mins = 15
                description = ''

            result_videos.append({
                'slide_id': slide_id,
                'filename': vf,
                'title': clean_title,
                'size_str': f"{size_mb:.1f} MB",
                'disk_path': os.path.join(host_folder, vf).replace('/', '\\'),
                'already_in_course': already,
                'selected': not already,
                'category_id': cat_id,
                'category_name': cat_name,
                'duration_minutes': duration_mins,
                'description': description,
            })

        return {
            'channel_id': channel.id,
            'channel_name': channel.name,
            'folder_name': channel.video_folder_path or folder.folder_path,
            'folder_display': channel.video_folder_disk_display or folder.folder_path,
            'exists': True,
            'categories': cat_list,
            'videos': result_videos
        }

    @http.route('/slides/add_disk_videos_to_channel', type='jsonrpc', auth='user', methods=['POST'])
    def add_disk_videos_to_channel(self, channel_id, videos, category_id=None, **kwargs):
        """Thêm hàng loạt các video có sẵn trên ổ đĩa vào khóa học slide.channel với đầy đủ thông tin chuẩn Coursera"""
        channel = request.env['slide.channel'].sudo().browse(int(channel_id))
        if not channel.exists():
            return {'error': 'Khóa học không tồn tại'}

        if not videos:
            return {'error': 'Không có video nào được chọn'}

        default_cat_id = int(category_id or kwargs.get('category_id') or 0) or False

        existing_slides = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', channel.id),
            ('is_local_video', '=', True),
        ])
        existing_filenames = set(existing_slides.mapped('local_video_filename') or [])

        slides = request.env['slide.slide'].sudo().search([('channel_id', '=', channel.id)])
        next_seq = (max(slides.mapped('sequence') or [0])) + 1
        added_count = 0
        slides_map = {}

        for item in videos:
            fn = item.get('filename')
            title = (item.get('title') or '').strip()
            if not fn:
                continue

            item_cat_id = int(item.get('category_id') or 0) or default_cat_id
            cat_name = (item.get('category_name') or '').strip()
            if cat_name and not item_cat_id:
                existing_cat = request.env['slide.slide'].sudo().search([
                    ('channel_id', '=', channel.id),
                    ('is_category', '=', True),
                    ('name', '=ilike', cat_name),
                ], limit=1)
                if existing_cat:
                    item_cat_id = existing_cat.id
                else:
                    new_cat = request.env['slide.slide'].sudo().create({
                        'name': cat_name,
                        'channel_id': channel.id,
                        'is_category': True,
                        'sequence': next_seq,
                        'is_published': True,
                    })
                    item_cat_id = new_cat.id
                    next_seq += 1

            if fn in existing_filenames:
                existing_s = request.env['slide.slide'].sudo().search([
                    ('channel_id', '=', channel.id),
                    ('local_video_filename', '=', fn),
                ], limit=1)
                if existing_s:
                    slides_map[fn] = existing_s.id
                    up_vals = {}
                    if title:
                        up_vals['name'] = title
                    if item.get('description'):
                        up_vals['description'] = item.get('description').strip()
                    if item_cat_id:
                        up_vals['category_id'] = item_cat_id
                    if up_vals:
                        existing_s.write(up_vals)
                    if item_cat_id:
                        cat_record = request.env['slide.slide'].sudo().browse(item_cat_id)
                        if cat_record.exists():
                            channel._resequence_slides(existing_s, force_category=cat_record)
                continue

            if not title:
                base_name, _ext = os.path.splitext(fn)
                title = re.sub(r'[_\-]+', ' ', base_name).strip().title()

            minutes = float(item.get('duration_minutes') or item.get('completion_time_minutes') or 15)
            completion_hours = max(0.01, round(minutes / 60.0, 2))
            desc = (item.get('description') or '').strip()

            new_s = request.env['slide.slide'].sudo().create({
                'name': title,
                'channel_id': channel.id,
                'category_id': item_cat_id or False,
                'slide_category': 'video',
                'is_local_video': True,
                'local_video_filename': fn,
                'completion_time': completion_hours,
                'description': desc or False,
                'sequence': next_seq,
                'is_published': True,
            })
            if item_cat_id:
                cat_record = request.env['slide.slide'].sudo().browse(item_cat_id)
                if cat_record.exists():
                    channel._resequence_slides(new_s, force_category=cat_record)

            slides_map[fn] = new_s.id
            existing_filenames.add(fn)
            next_seq += 1
            added_count += 1

        # Cập nhật số liệu khóa học
        channel._compute_folder_stats()

        return {'success': True, 'added_count': added_count, 'slide_ids': slides_map}

    @http.route('/slides/update_lesson_details', type='jsonrpc', auth='user', methods=['POST'])
    def update_lesson_details(self, slide_id=None, filename=None, channel_id=None, title=None, name=None, category_id=None, category_name=None, description=None, duration_minutes=None, **kwargs):
        """Cho phép người hướng dẫn / admin sửa đổi thiết lập bài học (đổi chương, đổi tên, mô tả...) kể cả sau khi đã tải lên"""
        slide = None
        if slide_id:
            slide = request.env['slide.slide'].sudo().browse(int(slide_id))
        elif channel_id and filename:
            slide = request.env['slide.slide'].sudo().search([
                ('channel_id', '=', int(channel_id)),
                ('local_video_filename', '=', filename),
            ], limit=1)

        if not slide or not slide.exists():
            return {'error': 'Không tìm thấy bài học để cập nhật'}

        channel = slide.channel_id
        target_name = (title or name or '').strip()
        cat_id = int(category_id or 0) if category_id != 'new' else 0
        new_cat_name = (category_name or '').strip()

        # Tạo chương mới nếu người dùng chọn '+ Tạo chương mới...'
        if new_cat_name and not cat_id:
            existing_cat = request.env['slide.slide'].sudo().search([
                ('channel_id', '=', channel.id),
                ('is_category', '=', True),
                ('name', '=ilike', new_cat_name),
            ], limit=1)
            if existing_cat:
                cat_id = existing_cat.id
            else:
                slides = request.env['slide.slide'].sudo().search([('channel_id', '=', channel.id)])
                cat_seq = (max(slides.mapped('sequence') or [0])) + 1
                new_cat = request.env['slide.slide'].sudo().create({
                    'name': new_cat_name,
                    'channel_id': channel.id,
                    'is_category': True,
                    'sequence': cat_seq,
                    'is_published': True,
                })
                cat_id = new_cat.id

        vals = {}
        if target_name:
            vals['name'] = target_name
        if description is not None:
            vals['description'] = description.strip() or False
        if duration_minutes is not None:
            mins = float(duration_minutes or 15)
            vals['completion_time'] = max(0.01, round(mins / 60.0, 2))

        cat_record = request.env['slide.slide'].sudo().browse(cat_id) if cat_id else False
        if cat_record and cat_record.exists():
            vals['category_id'] = cat_id
            slide.write(vals)
            channel._resequence_slides(slide, force_category=cat_record)
        else:
            slide.write(vals)

        # Cập nhật danh sách categories mới nhất của khóa học
        all_cats = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', channel.id),
            ('is_category', '=', True)
        ], order='sequence, id')
        cat_list = [{'id': c.id, 'name': c.name} for c in all_cats]

        return {
            'success': True,
            'slide_id': slide.id,
            'title': slide.name,
            'category_id': slide.category_id.id if slide.category_id else 0,
            'category_name': slide.category_id.name if slide.category_id else '',
            'categories': cat_list,
        }

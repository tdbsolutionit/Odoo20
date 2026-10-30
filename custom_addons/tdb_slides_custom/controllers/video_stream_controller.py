# -*- coding: utf-8 -*-
import json
import mimetypes
import os
from markupsafe import Markup
from odoo import http
from odoo.http import request


class VideoStreamController(http.Controller):

    @http.route('/slides/embed/local_video/<int:slide_id>', type='http', auth='public', website=True)
    def embed_local_video(self, slide_id, **kwargs):
        """Render trang nhúng trình phát video HTML5 chuẩn Coursera cho bài học video cục bộ"""
        slide = request.env['slide.slide'].sudo().browse(slide_id)
        if not slide.exists():
            return request.not_found()

        mime_type, _ = mimetypes.guess_type(slide.local_video_filename or '')
        if not mime_type:
            mime_type = 'video/mp4'

        is_officer = request.env.user.has_group('website_slides.group_website_slides_officer') or request.env.user._is_admin()
        resources = []
        for r in slide.slide_resource_ids:
            resources.append({
                'id': r.id,
                'name': r.name or r.file_name or 'Tài liệu đính kèm',
                'file_name': r.file_name or '',
                'resource_type': r.resource_type,
                'download_url': r.download_url or f'/web/content/slide.slide.resource/{r.id}/data?download=true',
                'link': r.link or '',
            })

        # 1. Quiz gắn liền với video bài giảng (Inline Quiz)
        inline_questions = []
        for q in slide.question_ids:
            inline_questions.append({
                'id': q.id,
                'question': q.question or '',
                'question_type': getattr(q, 'question_type', 'single') or 'single',
                'sequence': q.sequence,
                'answers': [{
                    'id': a.id,
                    'text': a.text_value or '',
                    'is_correct': a.is_correct,
                    'sequence': a.sequence,
                } for a in q.answer_ids]
            })

        all_quizzes = [{
            'id': slide.id,
            'name': f"Quiz bài giảng ({slide.name})",
            'is_inline': True,
            'questions': inline_questions,
            'questions_count': len(inline_questions),
        }]

        # 2. Các bài Quiz độc lập trong khóa học liên kết tiên quyết với video này
        linked_quiz_slides = request.env['slide.slide'].sudo().search([
            ('channel_id', '=', slide.channel_id.id),
            ('prerequisite_video_id', '=', slide.id),
            ('slide_category', '=', 'quiz'),
        ], order='sequence, id')

        for lqs in linked_quiz_slides:
            lqs_questions = []
            for q in lqs.question_ids:
                lqs_questions.append({
                    'id': q.id,
                    'question': q.question or '',
                    'question_type': getattr(q, 'question_type', 'single') or 'single',
                    'sequence': q.sequence,
                    'answers': [{
                        'id': a.id,
                        'text': a.text_value or '',
                        'is_correct': a.is_correct,
                        'sequence': a.sequence,
                    } for a in q.answer_ids]
                })
            all_quizzes.append({
                'id': lqs.id,
                'name': lqs.name,
                'is_inline': False,
                'questions': lqs_questions,
                'questions_count': len(lqs_questions),
            })

        total_q_count = sum(q['questions_count'] for q in all_quizzes)

        video_stream_url = slide._get_iis_video_url() or f"/slides/video/stream/{slide.id}"

        values = {
            'slide': slide,
            'channel': slide.channel_id,
            'mime_type': mime_type,
            'video_stream_url': video_stream_url,
            'is_officer': is_officer,
            'resources': resources,
            'csrf_token': request.csrf_token(),
            'category_id': slide.category_id.id if slide.category_id else 0,
            'all_quizzes_json': Markup(json.dumps(all_quizzes)),
            'has_quiz': bool(total_q_count > 0 or len(all_quizzes) > 1),
            'quiz_count': total_q_count,
        }
        response = request.render('tdb_slides_custom.embed_local_video', values)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @http.route('/slides/video/stream/<int:slide_id>', type='http', auth='public', website=True)
    def stream_local_video(self, slide_id, **kwargs):
        """Phát luồng (stream) video từ thư mục ổ đĩa hỗ trợ HTTP 206 Partial Content (tua nhanh, tua lại mượt mà)"""
        slide = request.env['slide.slide'].sudo().browse(slide_id)
        if not slide.exists() or not slide.is_local_video:
            return request.not_found()

        # Nếu đã cấu hình máy chủ IIS phát video, chuyển hướng thẳng sang IIS để giảm tải 100% cho Odoo
        iis_url = slide._get_iis_video_url()
        if iis_url:
            return request.redirect(iis_url, code=302)

        file_path = slide.local_video_path

        if not file_path or not os.path.exists(file_path) or not os.path.isfile(file_path):
            return request.make_response(
                b"Video file does not exist on disk",
                status=404,
                headers=[('Content-Type', 'text/plain')]
            )

        file_size = os.path.getsize(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'video/mp4'

        if kwargs.get('download') in [True, 'True', 'true', '1', 1]:
            return request.make_response(
                b"Chuc nang tai ve video bi khoa de bao ve ban quyen khoa hoc.",
                status=403,
                headers=[('Content-Type', 'text/plain; charset=utf-8')]
            )

        range_header = request.httprequest.headers.get('Range', None)
        if not range_header:
            def file_iterator():
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        yield chunk

            return request.make_response(
                file_iterator(),
                headers=[
                    ('Content-Type', content_type),
                    ('Content-Length', str(file_size)),
                    ('Accept-Ranges', 'bytes'),
                    ('Content-Disposition', 'inline'),
                    ('X-Content-Type-Options', 'nosniff'),
                ]
            )

        byte_range = range_header.replace('bytes=', '').strip()
        parts = byte_range.split('-')
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

        if start >= file_size or end >= file_size or start > end:
            return request.make_response(
                b'Requested Range Not Satisfiable',
                status=416,
                headers=[('Content-Range', f'bytes */{file_size}')]
            )

        chunk_size = end - start + 1

        def range_iterator(start_pos, length):
            with open(file_path, 'rb') as f:
                f.seek(start_pos)
                remaining = length
                while remaining > 0:
                    read_size = min(remaining, 65536)
                    chunk = f.read(read_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return request.make_response(
            range_iterator(start, chunk_size),
            status=206,
            headers=[
                ('Content-Type', content_type),
                ('Content-Range', f'bytes {start}-{end}/{file_size}'),
                ('Content-Length', str(chunk_size)),
                ('Accept-Ranges', 'bytes'),
                ('Content-Disposition', 'inline'),
                ('X-Content-Type-Options', 'nosniff'),
            ]
        )

    @http.route('/slides/video/sync_duration', type='jsonrpc', auth='public', methods=['POST'])
    def sync_slide_duration(self, slide_id, duration_seconds=0):
        """Tự động đồng bộ thời lượng thực tế của video vào bài học (completion_time)"""
        slide = request.env['slide.slide'].sudo().browse(int(slide_id))
        if slide.exists() and slide.is_local_video and duration_seconds > 0:
            hours = max(0.01, round(float(duration_seconds) / 3600.0, 2))
            if not slide.completion_time or abs(slide.completion_time - hours) > 0.05:
                slide.sudo().write({'completion_time': hours})
            return {'success': True, 'completion_time': hours}
        return {'success': False}

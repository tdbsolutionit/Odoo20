# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request
from odoo.addons.website_slides.controllers.main import WebsiteSlides

_logger = logging.getLogger(__name__)


class QuizController(WebsiteSlides):

    @http.route('''/slides/slide/<model("slide.slide"):slide>''', type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        return super().slide_view(slide, **kwargs)

    @http.route('/slides/slide/quiz/get', type="jsonrpc", auth="public", website=True)
    def slide_quiz_get(self, slide_id):
        return super().slide_quiz_get(slide_id)

    @http.route('/slides/quiz/quick_create', type='jsonrpc', auth='user', methods=['POST'])
    def quick_create_quiz(self, channel_id, slide_id=None, lesson_title=None, category_id=None, questions=None, prerequisite_video_id=None, **kwargs):
        """Tạo hoặc Cập nhật bài trắc nghiệm (Quiz) với số lượng đáp án tùy chọn và hỗ trợ nhiều đáp án đúng"""
        channel = request.env['slide.channel'].sudo().browse(int(channel_id))
        if not channel.exists():
            return {'error': 'Khóa học không tồn tại'}

        if not questions or not isinstance(questions, list):
            return {'error': 'Danh sách câu hỏi không hợp lệ'}

        # Kiểm tra tính toàn vẹn câu hỏi: mỗi câu phải có ít nhất 1 đáp án đúng và 1 đáp án sai
        for idx, q in enumerate(questions):
            q_title = (q.get('question') or '').strip()
            answers = q.get('answers') or []
            if not q_title:
                return {'error': f'Câu hỏi #{idx + 1} chưa có nội dung!'}
            if len(answers) < 2:
                return {'error': f'Câu hỏi "{q_title}" cần có ít nhất 2 lựa chọn đáp án!'}
            correct = [a for a in answers if a.get('is_correct')]
            incorrect = [a for a in answers if not a.get('is_correct')]
            if not correct:
                return {'error': f'Câu hỏi "{q_title}" bắt buộc phải có ít nhất 1 đáp án đúng!'}
            if not incorrect:
                return {'error': f'Câu hỏi "{q_title}" bắt buộc phải có ít nhất 1 phương án sai!'}

        target_slide = None
        if slide_id:
            target_slide = request.env['slide.slide'].sudo().browse(int(slide_id))

        slides = request.env['slide.slide'].sudo().search([('channel_id', '=', channel.id)])
        next_seq = (max(slides.mapped('sequence') or [0])) + 1

        # Xử lý chế độ tiên quyết: all_chapter (tất cả video trong chương), single (1 video cụ thể), none (không yêu cầu)
        prereq_mode = kwargs.get('prerequisite_mode') or kwargs.get('prerequisite_type')
        prereq_id = None
        if isinstance(prerequisite_video_id, str):
            if prerequisite_video_id in ('all_chapter', 'none'):
                prereq_mode = prerequisite_video_id
                prereq_id = False
            else:
                try:
                    prereq_id = int(prerequisite_video_id) or False
                except (ValueError, TypeError):
                    prereq_id = False
        elif prerequisite_video_id:
            prereq_id = int(prerequisite_video_id) or False

        if not prereq_mode:
            prereq_mode = 'single' if prereq_id else 'all_chapter'

        if not target_slide or not target_slide.exists():
            cat_id = int(category_id or 0) or False
            prereq_slide = request.env['slide.slide'].sudo().browse(prereq_id) if prereq_id else None
            if prereq_slide and prereq_slide.exists():
                cat_id = cat_id or (prereq_slide.category_id.id if prereq_slide.category_id else False)
                next_seq = prereq_slide.sequence + 1
            elif cat_id:
                cat_slides = request.env['slide.slide'].sudo().search([
                    ('channel_id', '=', channel.id),
                    ('category_id', '=', cat_id)
                ])
                next_seq = (max(cat_slides.mapped('sequence') or [0])) + 1
            else:
                slides = request.env['slide.slide'].sudo().search([('channel_id', '=', channel.id)])
                next_seq = (max(slides.mapped('sequence') or [0])) + 1

            title = (lesson_title or '').strip() or 'Bài kiểm tra trắc nghiệm'
            vals = {
                'name': title,
                'channel_id': channel.id,
                'category_id': cat_id,
                'slide_category': 'quiz',
                'sequence': next_seq,
                'is_published': True,
                'prerequisite_type': prereq_mode,
                'prerequisite_video_id': prereq_id if (prereq_mode == 'single' and prereq_id) else False,
            }
            target_slide = request.env['slide.slide'].sudo().create(vals)
        else:
            update_vals = {'prerequisite_type': prereq_mode}
            if prereq_mode == 'single':
                update_vals['prerequisite_video_id'] = prereq_id or False
            elif prereq_mode in ('all_chapter', 'none'):
                update_vals['prerequisite_video_id'] = False
            target_slide.sudo().write(update_vals)

        # ĐỒNG BỘ CÂU HỎI & ĐÁP ÁN (HỖ TRỢ CẢ TẠO MỚI, SỬA ĐỔI, XÓA VÀ THÊM CÂU)
        existing_q_map = {q.id: q for q in target_slide.question_ids}
        incoming_q_ids = set()
        q_seq = 1

        for q in questions:
            q_id = int(q.get('id') or 0)
            answers = q.get('answers', [])
            correct_count = len([a for a in answers if a.get('is_correct')])
            q_type = q.get('question_type')
            if not q_type:
                q_type = 'multiple' if correct_count > 1 else 'single'

            if q_id and q_id in existing_q_map:
                current_q = existing_q_map[q_id]
                current_q.sudo().write({
                    'question': q.get('question').strip(),
                    'question_type': q_type,
                    'sequence': q_seq,
                })
                incoming_q_ids.add(q_id)
            else:
                current_q = request.env['slide.question'].sudo().create({
                    'slide_id': target_slide.id,
                    'question': q.get('question').strip(),
                    'question_type': q_type,
                    'sequence': q_seq,
                })
                incoming_q_ids.add(current_q.id)

            q_seq += 1

            # Đồng bộ các phương án trả lời cho câu hỏi current_q
            existing_a_map = {a.id: a for a in current_q.answer_ids}
            incoming_a_ids = set()
            a_seq = 1

            for a in answers:
                a_id = int(a.get('id') or 0)
                a_vals = {
                    'text_value': (a.get('text') or '').strip(),
                    'is_correct': bool(a.get('is_correct')),
                    'comment': (a.get('comment') or '').strip() or False,
                    'sequence': a_seq,
                }
                if a_id and a_id in existing_a_map:
                    existing_a_map[a_id].sudo().write(a_vals)
                    incoming_a_ids.add(a_id)
                else:
                    new_a = request.env['slide.answer'].sudo().create({
                        'question_id': current_q.id,
                        **a_vals
                    })
                    incoming_a_ids.add(new_a.id)
                a_seq += 1

            # Xóa các phương án đã bị người dùng xóa khỏi giao diện
            for old_a_id, old_a in existing_a_map.items():
                if old_a_id not in incoming_a_ids:
                    old_a.sudo().unlink()

        # Xóa các câu hỏi đã bị người dùng xóa khỏi giao diện
        for old_q_id, old_q in existing_q_map.items():
            if old_q_id not in incoming_q_ids:
                old_q.sudo().unlink()

        # Trả về danh sách câu hỏi đã lưu kèm ID cập nhật
        updated_questions = []
        for q in target_slide.question_ids:
            updated_questions.append({
                'id': q.id,
                'question': q.question,
                'question_type': getattr(q, 'question_type', 'single') or 'single',
                'answers': [{
                    'id': a.id,
                    'text': a.text_value or '',
                    'is_correct': a.is_correct,
                } for a in q.answer_ids]
            })

        return {
            'success': True,
            'slide_id': target_slide.id,
            'slide_name': target_slide.name,
            'created_questions_count': len(target_slide.question_ids),
            'questions_count': len(target_slide.question_ids),
            'questions': updated_questions,
        }

    @http.route('/slides/quiz/get_questions', type='jsonrpc', auth='user', methods=['POST'])
    def get_quiz_questions(self, slide_id, **kwargs):
        """Lấy danh sách các câu hỏi và đáp án hiện có của bài học để chỉnh sửa"""
        slide = request.env['slide.slide'].sudo().browse(int(slide_id))
        if not slide.exists():
            return {'error': 'Bài học không tồn tại', 'questions': []}

        questions = []
        for q in slide.question_ids:
            questions.append({
                'id': q.id,
                'question': q.question or '',
                'question_type': getattr(q, 'question_type', 'single') or 'single',
                'sequence': q.sequence,
                'answers': [{
                    'id': a.id,
                    'text': a.text_value or '',
                    'is_correct': a.is_correct,
                    'comment': a.comment or '',
                    'sequence': a.sequence,
                } for a in q.answer_ids]
            })
        return {
            'success': True,
            'slide_id': slide.id,
            'slide_name': slide.name,
            'has_quiz': len(questions) > 0,
            'questions': questions,
        }

    @http.route('/slides/quiz/delete', type='jsonrpc', auth='user', methods=['POST'])
    def delete_slide_quiz(self, slide_id, **kwargs):
        """Xóa câu hỏi hoặc xóa hẳn bài Quiz nếu là bài trắc nghiệm độc lập"""
        slide = request.env['slide.slide'].sudo().browse(int(slide_id))
        if not slide.exists():
            return {'error': 'Bài học không tồn tại'}
        if slide.slide_category == 'quiz':
            slide.sudo().unlink()
            return {'success': True, 'deleted_slide': True, 'slide_id': int(slide_id)}
        else:
            slide.question_ids.sudo().unlink()
            return {'success': True, 'deleted_questions': True, 'slide_id': int(slide_id)}

    @http.route('/slides/slide/quiz/submit', type='jsonrpc', auth='public', website=True)
    def slide_quiz_submit(self, slide_id, answer_ids):
        """Xử lý nộp bài quiz: kiểm tra khóa bài học và chấm điểm trắc nghiệm (cho phép chọn nhiều đáp án đúng)"""
        if self.env.website.is_public_user():
            return {'error': 'public_user'}

        fetch_res = self._fetch_slide(slide_id)
        if fetch_res.get('error'):
            return fetch_res
        slide = fetch_res['slide']

        # KIỂM TRA ĐIỀU KIỆN KHÓA QUIZ: BẮT BUỘC HOÀN THÀNH VIDEO TIÊN QUYẾT
        if getattr(slide, 'is_quiz_locked', False):
            video_name = getattr(slide, 'prerequisite_video_name', '') or 'bài giảng'
            return {
                'error': 'quiz_locked',
                'error_message': f'Bài kiểm tra đang bị khóa! Bạn cần xem và hoàn thành video "{video_name}" trước khi làm bài.'
            }

        if slide.user_has_completed:
            self._channel_remove_session_answers(slide.channel_id, slide)
            return {'error': 'slide_quiz_done'}

        all_questions = request.env['slide.question'].sudo().search([('slide_id', '=', slide.id)])
        user_answers = request.env['slide.answer'].sudo().search([('id', 'in', answer_ids)])

        if user_answers.mapped('question_id') != all_questions:
            return {'error': 'slide_quiz_incomplete'}

        # CHẤM ĐIỂM CHÍNH XÁC:
        # Với câu hỏi nhiều đáp án đúng: học viên phải chọn ĐÚNG VÀ ĐỦ toàn bộ đáp án đúng, không chọn đáp án sai
        all_correct = True
        question_eval = {}

        for q in all_questions:
            correct_ids = set(q.answer_ids.filtered('is_correct').ids)
            user_selected = set(user_answers.filtered(lambda a: a.question_id.id == q.id).ids)
            is_q_correct = (user_selected == correct_ids)
            if not is_q_correct:
                all_correct = False

            # Thu thập phản hồi / comment
            comments = [a.comment for a in q.answer_ids if a.comment and (a.id in user_selected or a.is_correct)]
            question_eval[q.id] = {
                'is_correct': is_q_correct,
                'comment': '\n'.join(comments) if comments else False
            }

        self._set_viewed_slide(slide, quiz_attempts_inc=True)
        quiz_info = self._get_slide_quiz_partner_info(slide, quiz_done=True)

        rank_progress = {}
        if all_correct:
            rank_progress['previous_rank'] = self._get_rank_values(request.env.user)
            slide._action_mark_completed()
            rank_progress['new_rank'] = self._get_rank_values(request.env.user)
            rank_progress.update({
                'description': request.env.user.rank_id.description,
                'last_rank': not request.env.user._get_next_rank(),
                'level_up': rank_progress['previous_rank']['lower_bound'] != rank_progress['new_rank']['lower_bound']
            })

        self._channel_remove_session_answers(slide.channel_id, slide)
        return {
            'answers': question_eval,
            'completed': slide.user_has_completed,
            'channel_completion': slide.channel_id.completion,
            'quizKarmaWon': quiz_info['quiz_karma_won'],
            'quizKarmaGain': quiz_info['quiz_karma_gain'],
            'quizAttemptsCount': quiz_info['quiz_attempts_count'],
            'rankProgress': rank_progress,
        }

    def _get_slide_quiz_data(self, slide):
        """Bổ sung thông tin loại câu hỏi (Single/Multiple) và trạng thái khóa vào dữ liệu quiz"""
        values = super()._get_slide_quiz_data(slide)
        for q_data in values.get('slide_questions', []):
            q_id = q_data.get('id')
            q_rec = request.env['slide.question'].sudo().browse(q_id)
            if q_rec.exists():
                q_data['question_type'] = getattr(q_rec, 'question_type', 'single') or 'single'
                q_data['correct_count'] = len(q_rec.answer_ids.filtered('is_correct'))
        values['is_quiz_locked'] = getattr(slide, 'is_quiz_locked', False)
        values['prerequisite_video_name'] = getattr(slide, 'prerequisite_video_name', False)
        values['prerequisite_video_url'] = getattr(slide, 'prerequisite_video_url', False)
        return values

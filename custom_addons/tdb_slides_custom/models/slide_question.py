# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SlideQuestion(models.Model):
    _inherit = 'slide.question'

    question_type = fields.Selection([
        ('single', 'Một đáp án đúng (Single Choice)'),
        ('multiple', 'Nhiều đáp án đúng (Multiple Choice)')
    ], string='Loại câu hỏi', compute='_compute_question_type', store=True, readonly=False, default='single',
       help='Tự động nhận diện nhiều đáp án đúng nếu có trên 1 phương án được tích đúng.')

    @api.depends('answer_ids.is_correct')
    def _compute_question_type(self):
        for question in self:
            correct_count = len(question.answer_ids.filtered('is_correct'))
            if correct_count > 1:
                question.question_type = 'multiple'
            else:
                question.question_type = 'single'

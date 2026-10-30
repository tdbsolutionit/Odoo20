# -*- coding: utf-8 -*-
import os
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SlideAddVideoWizard(models.TransientModel):
    _name = 'slide.channel.add.video.wizard'
    _description = 'Chọn Video từ Thư mục cho Khóa học'

    channel_id = fields.Many2one(
        'slide.channel',
        string='Khóa học',
        required=True,
        readonly=True
    )
    video_folder_id = fields.Many2one(
        'slide.video.folder',
        string='Thư mục Video Quản lý',
        related='channel_id.video_folder_id',
        readonly=True
    )
    video_file = fields.Selection(
        selection='_get_video_file_selection',
        string='Chọn File Video từ Thư mục',
        help='Chỉ hiển thị các file video có sẵn trong thư mục quản lý của khóa học này.'
    )
    name = fields.Char(
        string='Tên Bài học / Tiêu đề',
    )
    category_id = fields.Many2one(
        'slide.slide',
        string='Phần / Chương học (Section)',
        domain="[('channel_id', '=', channel_id), ('is_category', '=', True)]",
        help='Chọn phần/chương trong khóa học mà bài học này thuộc về.'
    )
    completion_time_minutes = fields.Float(
        string='Thời lượng ước tính (Phút)',
        default=15.0,
        help='Thời lượng học viên cần hoàn thành bài học này (tính theo phút).'
    )
    is_preview = fields.Boolean(
        string='Cho phép xem thử miễn phí (Preview)',
        default=False,
        help='Nếu bật, người học chưa đăng ký hoặc chưa đăng nhập vẫn có thể xem bài này.'
    )
    sequence = fields.Integer(
        string='Thứ tự bài học',
        default=10,
        help='Thứ tự hiển thị bài học trong khóa học.'
    )
    description = fields.Html(
        string='Mô tả nội dung bài học'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        channel_id = self.env.context.get('default_channel_id')
        if channel_id:
            channel = self.env['slide.channel'].browse(channel_id)
            if channel.exists():
                # Tự động tính sequence tiếp theo
                max_seq = 0
                slides = self.env['slide.slide'].search([('channel_id', '=', channel.id)])
                if slides:
                    max_seq = max(slides.mapped('sequence') or [0])
                res['sequence'] = max_seq + 1
        return res

    def _get_video_file_selection(self):
        """Lấy danh sách các file video từ thư mục của khóa học"""
        channel_id = self.env.context.get('default_channel_id') or self.channel_id.id
        if not channel_id:
            return []
        channel = self.env['slide.channel'].browse(channel_id)
        if not channel.video_folder_id:
            return []

        video_files = channel.video_folder_id.get_video_files()
        if not video_files:
            return []

        # Lấy danh sách video đã được thêm vào khóa học này để đánh dấu
        existing_slides = self.env['slide.slide'].search([
            ('channel_id', '=', channel.id),
            ('is_local_video', '=', True),
        ])
        existing_filenames = set(existing_slides.mapped('local_video_filename'))

        selection = []
        for vf in video_files:
            if vf in existing_filenames:
                label = f"{vf} (Đã có trong khóa học)"
            else:
                label = vf
            selection.append((vf, label))
        return selection

    @api.onchange('video_file')
    def _onchange_video_file(self):
        if self.video_file:
            # Tự động tạo tiêu đề gợi ý từ tên file (bỏ đuôi mở rộng, thay gạch dưới thành khoảng trắng)
            base_name, _ext = os.path.splitext(self.video_file)
            clean_title = re.sub(r'[_\-]+', ' ', base_name).strip().title()
            if not self.name or self.name == _('Bài học mới'):
                self.name = clean_title

    def _prepare_slide_vals(self):
        self.ensure_one()
        if not self.video_file:
            raise UserError(_("Vui lòng chọn file video từ thư mục!"))
        if not self.name or not self.name.strip():
            raise UserError(_("Vui lòng nhập tên bài học / tiêu đề!"))
        # Chuyển thời lượng phút thành giờ cho float_time của Odoo (ví dụ 30 phút = 0.5 giờ)
        duration_hours = (self.completion_time_minutes or 0.0) / 60.0
        return {
            'name': self.name.strip(),
            'channel_id': self.channel_id.id,
            'slide_category': 'video',
            'is_local_video': True,
            'local_video_filename': self.video_file,
            'category_id': self.category_id.id if self.category_id else False,
            'completion_time': duration_hours,
            'is_preview': self.is_preview,
            'sequence': self.sequence,
            'description': self.description,
            'is_published': True,
        }

    def action_create_slide(self):
        """Tạo bài học từ video đã chọn và đóng popup"""
        self.ensure_one()
        vals = self._prepare_slide_vals()
        new_slide = self.env['slide.slide'].create(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công'),
                'message': _('Đã thêm bài học "%s" vào khóa học thành công!', new_slide.name),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_create_and_continue(self):
        """Tạo bài học và giữ cửa sổ mở để tiếp tục chọn video khác"""
        self.ensure_one()
        vals = self._prepare_slide_vals()
        new_slide = self.env['slide.slide'].create(vals)

        # Chuẩn bị dữ liệu cho bài tiếp theo
        self.write({
            'video_file': False,
            'name': '',
            'sequence': self.sequence + 1,
            'description': False,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đã thêm bài học'),
                'message': _('Đã thêm bài học "%s"! Bạn có thể tiếp tục chọn video tiếp theo.', new_slide.name),
                'type': 'info',
                'sticky': False,
            }
        }


class SlideChannelBatchVideoWizard(models.TransientModel):
    _name = 'slide.channel.batch.video.wizard'
    _description = 'Tích chọn Video từ Thư mục đưa vào Khóa học'

    channel_id = fields.Many2one('slide.channel', string='Khóa học', required=True, readonly=True)
    folder_path = fields.Char(string='Thư mục Ổ đĩa', readonly=True)
    line_ids = fields.One2many(
        'slide.channel.batch.video.line',
        'wizard_id',
        string='Danh sách Video trong Thư mục'
    )
    total_files = fields.Integer(string='Tổng số video', compute='_compute_counts')
    selected_count = fields.Integer(string='Đã chọn', compute='_compute_counts')

    @api.depends('line_ids', 'line_ids.selected')
    def _compute_counts(self):
        for record in self:
            record.total_files = len(record.line_ids)
            record.selected_count = sum(1 for line in record.line_ids if line.selected)

    def action_select_all(self):
        """Tích chọn tất cả video"""
        self.ensure_one()
        self.line_ids.write({'selected': True})
        return self._reopen()

    def action_deselect_all(self):
        """Bỏ chọn tất cả video"""
        self.ensure_one()
        self.line_ids.write({'selected': False})
        return self._reopen()

    def action_select_new(self):
        """Chỉ tích chọn những video chưa có trong khóa học"""
        self.ensure_one()
        for line in self.line_ids:
            line.selected = not line.already_in_course
        return self._reopen()

    def action_create_slides(self):
        """Tạo bài học cho tất cả các video được tích chọn"""
        self.ensure_one()
        selected_lines = self.line_ids.filtered(lambda l: l.selected)
        if not selected_lines:
            raise UserError(_("Vui lòng tích chọn ít nhất 1 video để đưa vào khóa học!"))

        # Xác định sequence tiếp theo
        slides = self.env['slide.slide'].search([('channel_id', '=', self.channel_id.id)])
        next_seq = (max(slides.mapped('sequence') or [0])) + 1

        created_count = 0
        for line in selected_lines:
            clean_name = (line.name or '').strip() or line.filename
            duration_hours = (line.completion_time_minutes or 15.0) / 60.0

            self.env['slide.slide'].create({
                'name': clean_name,
                'channel_id': self.channel_id.id,
                'slide_category': 'video',
                'is_local_video': True,
                'local_video_filename': line.filename,
                'category_id': line.category_id.id if line.category_id else False,
                'completion_time': duration_hours,
                'is_preview': line.is_preview,
                'sequence': next_seq,
                'is_published': True,
            })
            next_seq += 1
            created_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đã thêm bài học thành công!'),
                'message': _('Đã thêm thành công %d bài học từ thư mục vào khóa học "%s".', created_count, self.channel_id.name),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'slide.channel.batch.video.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class SlideChannelBatchVideoLine(models.TransientModel):
    _name = 'slide.channel.batch.video.line'
    _description = 'Dòng Video trong Bảng Tích chọn'
    _order = 'filename asc'

    wizard_id = fields.Many2one('slide.channel.batch.video.wizard', ondelete='cascade')
    selected = fields.Boolean(string='Chọn', default=True)
    filename = fields.Char(string='Tên file Video', readonly=True)
    name = fields.Char(string='Tên Bài học trên Odoo', required=True)
    file_size_display = fields.Char(string='Dung lượng', readonly=True)
    already_in_course = fields.Boolean(string='Đã có trong khóa học', readonly=True)
    category_id = fields.Many2one(
        'slide.slide',
        string='Chương / Phần học',
        domain="[('channel_id', '=', parent.channel_id), ('is_category', '=', True)]"
    )
    completion_time_minutes = fields.Float(string='Thời lượng (phút)', default=15.0)
    is_preview = fields.Boolean(string='Xem thử', default=False)


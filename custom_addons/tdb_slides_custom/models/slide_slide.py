# -*- coding: utf-8 -*-
import os
from markupsafe import Markup
from odoo import api, fields, models, _


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    is_local_video = fields.Boolean(
        string='Video từ Thư mục Máy tính',
        default=False,
        help='Đánh dấu bài học này sử dụng video phát trực tiếp từ thư mục trên ổ đĩa máy tính.'
    )
    local_video_folder_id = fields.Many2one(
        'slide.video.folder',
        string='Thư mục Video Quản lý',
        related='channel_id.video_folder_id',
        store=True,
        readonly=True
    )
    local_video_filename = fields.Char(
        string='Tên file Video trên ổ đĩa',
        help='Tên file video được chọn từ thư mục quản lý của khóa học.'
    )
    local_video_path = fields.Char(
        string='Đường dẫn File Đầy đủ',
        compute='_compute_local_video_path',
        store=True,
        help='Đường dẫn tuyệt đối đến file video trên hệ thống.'
    )

    video_source_type = fields.Selection(
        selection_add=[('local', 'Local Video')],
        ondelete={'local': 'set null'}
    )
    slide_type = fields.Selection(
        selection_add=[('local_video', 'Local Video')],
        ondelete={'local_video': 'set null'}
    )

    category_id = fields.Many2one(
        'slide.slide',
        string="Chương / Phần học",
        compute="_compute_category_id",
        inverse="_inverse_category_id",
        store=True,
        readonly=False,
        domain="[('channel_id', '=', channel_id), ('is_category', '=', True)]"
    )

    prerequisite_type = fields.Selection([
        ('all_chapter', 'Tất cả video trong chương này'),
        ('single', 'Một video cụ thể'),
        ('none', 'Không yêu cầu tiên quyết')
    ], string="Điều Kiện Tiên Quyết", default='all_chapter',
       help="Học viên phải xem xong các video theo điều kiện này mới được mở khóa làm bài kiểm tra.")

    prerequisite_video_id = fields.Many2one(
        'slide.slide',
        string="Video Tiên Quyết",
        domain="[('channel_id', '=', channel_id), ('slide_category', '=', 'video'), ('id', '!=', id)]",
        help="Học viên bắt buộc phải xem xong video bài giảng này trước khi được mở khóa làm bài kiểm tra quiz."
    )
    is_quiz_locked = fields.Boolean(
        string="Quiz Bị Khóa",
        compute="_compute_is_quiz_locked",
        help="Tự động khóa nếu học viên chưa hoàn thành video tiên quyết."
    )
    prerequisite_video_name = fields.Char(
        string="Tên Video Tiên Quyết",
        compute="_compute_is_quiz_locked"
    )
    prerequisite_video_url = fields.Char(
        string="URL Video Tiên Quyết",
        compute="_compute_is_quiz_locked"
    )

    def _inverse_category_id(self):
        for slide in self:
            if not slide.is_category and slide.channel_id:
                slide.channel_id._resequence_slides(slide, force_category=slide.category_id)

    @api.depends('slide_category', 'question_ids', 'prerequisite_type', 'prerequisite_video_id', 'category_id', 'channel_id.slide_ids')
    def _compute_is_quiz_locked(self):
        for slide in self:
            has_quiz = (slide.slide_category == 'quiz') or bool(slide.question_ids)
            if not has_quiz:
                slide.is_quiz_locked = False
                slide.prerequisite_video_name = False
                slide.prerequisite_video_url = False
                continue

            # Trường hợp 1: Nếu bài học này là video và có câu hỏi quiz đính kèm trực tiếp
            if slide.slide_category == 'video':
                slide.is_quiz_locked = not slide.user_has_completed
                slide.prerequisite_video_name = slide.name
                slide.prerequisite_video_url = f"/slides/slide/{slide.id}"
                continue

            # Trường hợp 2: Bài học là Quiz độc lập
            prereq_mode = slide.prerequisite_type or ('single' if slide.prerequisite_video_id else 'all_chapter')

            if prereq_mode == 'none':
                slide.is_quiz_locked = False
                slide.prerequisite_video_name = False
                slide.prerequisite_video_url = False
                continue

            if prereq_mode == 'all_chapter':
                # Tìm tất cả video bài học trong cùng chương này
                if slide.category_id:
                    chapter_videos = slide.channel_id.slide_ids.filtered(
                        lambda s: s.category_id == slide.category_id and s.slide_category == 'video' and not s.is_category
                    )
                else:
                    chapter_videos = slide.channel_id.slide_ids.filtered(
                        lambda s: s.sequence < slide.sequence and s.slide_category == 'video' and not s.is_category
                    )

                if not chapter_videos:
                    slide.is_quiz_locked = False
                    slide.prerequisite_video_name = False
                    slide.prerequisite_video_url = False
                    continue

                uncompleted = chapter_videos.filtered(lambda s: not s.user_has_completed).sorted('sequence')
                if uncompleted:
                    slide.is_quiz_locked = True
                    first_uncompleted = uncompleted[0]
                    cat_name = slide.category_id.name if slide.category_id else "chương"
                    if len(chapter_videos) == 1:
                        slide.prerequisite_video_name = first_uncompleted.name
                    else:
                        slide.prerequisite_video_name = f"tất cả video trong {cat_name} (còn {len(uncompleted)}/{len(chapter_videos)} video: {first_uncompleted.name})"
                    slide.prerequisite_video_url = f"/slides/slide/{first_uncompleted.id}"
                else:
                    slide.is_quiz_locked = False
                    slide.prerequisite_video_name = False
                    slide.prerequisite_video_url = False
                continue

            # prereq_mode == 'single'
            target_video = slide.prerequisite_video_id
            if not target_video:
                all_slides = slide.channel_id.slide_ids.sorted(lambda s: s.sequence)
                prev_videos = all_slides.filtered(lambda s: s.sequence < slide.sequence and s.slide_category == 'video')
                if prev_videos:
                    target_video = prev_videos[-1]

            if target_video and not target_video.user_has_completed:
                slide.is_quiz_locked = True
                slide.prerequisite_video_name = target_video.name
                slide.prerequisite_video_url = f"/slides/slide/{target_video.id}"
            else:
                slide.is_quiz_locked = False
                slide.prerequisite_video_name = target_video.name if target_video else False
                slide.prerequisite_video_url = f"/slides/slide/{target_video.id}" if target_video else False

    @api.depends('local_video_folder_id.full_path', 'local_video_filename')
    def _compute_local_video_path(self):
        for record in self:
            if record.local_video_folder_id and record.local_video_folder_id.full_path and record.local_video_filename:
                record.local_video_path = os.path.normpath(
                    os.path.join(record.local_video_folder_id.full_path, record.local_video_filename)
                )
            else:
                record.local_video_path = False

    @api.depends('video_url', 'is_local_video')
    def _compute_video_source_type(self):
        super()._compute_video_source_type()
        for record in self:
            if record.is_local_video:
                record.video_source_type = 'local'

    @api.depends('slide_category', 'video_source_type', 'is_local_video')
    def _compute_slide_type(self):
        super()._compute_slide_type()
        for record in self:
            if record.is_local_video:
                record.slide_type = 'local_video'

    @api.depends('slide_category', 'google_drive_id', 'video_source_type', 'youtube_id', 'is_local_video')
    def _compute_embed_code(self):
        super()._compute_embed_code()
        for record in self:
            if record.slide_category == 'video' and record.is_local_video:
                embed_url = f"/slides/embed/local_video/{record.id}"
                embed_code = Markup(
                    f'<iframe src="{embed_url}" class="o_wslides_iframe_viewer w-100 h-100" '
                    f'allowfullscreen="true" frameborder="0" style="min-height: 480px; background: #000;" '
                    f'aria-label="{record.name or _("Video")}"></iframe>'
                )
                record.embed_code = embed_code
                record.embed_code_external = embed_code

    def _get_iis_video_url(self):
        """Tính toán URL phát trực tiếp từ máy chủ IIS (nếu có cấu hình)"""
        self.ensure_one()
        icp = self.env['ir.config_parameter'].sudo()
        getter = getattr(icp, 'get_str', getattr(icp, 'get_param', None))
        if getter:
            iis_base = (getter('tdb_slides_custom.iis_media_url', default='') or '').strip().rstrip('/')
        else:
            rec = icp.search([('key', '=', 'tdb_slides_custom.iis_media_url')], limit=1)
            iis_base = (rec.value or '').strip().rstrip('/') if rec else ''
        if not iis_base or not self.local_video_filename:
            return False

        folder_p = (self.local_video_folder_id.folder_path or '').strip().replace('\\', '/')
        sub_folder = ""
        is_managed_by_iis = False

        if not folder_p or folder_p in ('.', './', '/mnt/videos', 'videos'):
            is_managed_by_iis = True
            sub_folder = ""
        elif folder_p.startswith('/mnt/videos/'):
            is_managed_by_iis = True
            sub_folder = folder_p[12:].strip('/')
        elif 'videos/' in folder_p:
            is_managed_by_iis = True
            sub_folder = folder_p.split('videos/', 1)[1].strip('/')
        elif not folder_p.startswith('/') and not (len(folder_p) >= 2 and folder_p[1] == ':'):
            # Tên thư mục con tương đối (ví dụ 'Captures', 'KhoaHocTest') nằm trong videos
            is_managed_by_iis = True
            sub_folder = folder_p.strip('/')

        # Nếu video nằm ở ổ đĩa/thư mục khác ngoài C:\Work\odoo20-docker\videos:
        # Tự động trả về False để Odoo kích hoạt cơ chế phát nội bộ (Fallback an toàn)
        if not is_managed_by_iis:
            return False

        parts = [p for p in [sub_folder, self.local_video_filename] if p]
        rel_path = "/".join(parts)
        from urllib.parse import quote
        encoded_rel = "/".join([quote(seg) for seg in rel_path.split('/')])
        return f"{iis_base}/{encoded_rel}"



# -*- coding: utf-8 -*-
import os
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .slide_video_folder import is_in_docker


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    video_folder_path = fields.Char(
        string='Thư mục Video trên Ổ đĩa',
        help='Nhập hoặc dán bất kỳ đường dẫn thư mục nào trên ổ đĩa máy tính (ví dụ: C:\\Videos\\Python_Co_Ban hoặc D:\\KhoaHoc\\...) '
             'Hệ thống sẽ tự động quét các file video trong thư mục này để bạn tích chọn đưa lên Odoo.'
    )
    video_folder_id = fields.Many2one(
        'slide.video.folder',
        string='Thư mục Video của khóa học',
        help='Bản ghi quản lý thư mục video liên kết với khóa học này.'
    )
    folder_exists = fields.Boolean(
        string='Thư mục tồn tại',
        compute='_compute_folder_stats'
    )
    video_files_count = fields.Integer(
        string='Số video sẵn sàng trên ổ đĩa',
        compute='_compute_folder_stats',
        help='Số lượng file video hiện có trong thư mục trên ổ đĩa.'
    )
    video_imported_count = fields.Integer(
        string='Số video đã đưa vào khóa học',
        compute='_compute_folder_stats',
        help='Số lượng bài học video đã được thêm vào khóa học này.'
    )
    video_folder_disk_display = fields.Char(
        string='Đường dẫn Ổ đĩa Thư mục',
        compute='_compute_video_folder_disk_display',
        store=True,
        help='Đường dẫn hiển thị rõ ổ đĩa máy tính nơi lưu trữ video của khóa học.'
    )

    @api.onchange('video_folder_path')
    def _onchange_video_folder_path(self):
        if self.video_folder_path:
            p = self.video_folder_path.strip()
            self.video_folder_id = self._find_or_create_folder(p)

    @api.onchange('video_folder_id')
    def _onchange_video_folder_id(self):
        if self.video_folder_id and not self.video_folder_path:
            self.video_folder_path = self.video_folder_id.folder_path

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('video_folder_path') and not vals.get('video_folder_id'):
                folder = self._find_or_create_folder(vals['video_folder_path'])
                vals['video_folder_id'] = folder.id
        return super().create(vals_list)

    def write(self, vals):
        if 'video_folder_path' in vals and not vals.get('video_folder_id'):
            path = (vals.get('video_folder_path') or '').strip()
            if path:
                folder = self._find_or_create_folder(path)
                vals['video_folder_id'] = folder.id
            else:
                vals['video_folder_id'] = False
        return super().write(vals)

    def _find_or_create_folder(self, raw_path):
        p = raw_path.strip()
        folder = self.env['slide.video.folder'].search([('folder_path', '=', p)], limit=1)
        if not folder:
            name = os.path.basename(p.rstrip('\\/')) or p
            clean_name = re.sub(r'[_\-]+', ' ', name).strip().title()
            folder = self.env['slide.video.folder'].create({
                'name': clean_name or f"Thư mục {p}",
                'folder_path': p,
            })
        return folder

    def _ensure_video_folder(self):
        """Đảm bảo khóa học luôn có bản ghi slide.video.folder tương ứng với video_folder_path"""
        self.ensure_one()
        path = (self.video_folder_path or '').strip()
        if path:
            if not self.video_folder_id or self.video_folder_id.folder_path != path:
                folder = self._find_or_create_folder(path)
                self.video_folder_id = folder.id
        return self.video_folder_id

    @api.depends('video_folder_path', 'video_folder_id', 'video_folder_id.folder_path', 'slide_ids')
    def _compute_folder_stats(self):
        for record in self:
            folder = record.video_folder_id
            if not folder and record.video_folder_path:
                folder = record.env['slide.video.folder'].search([('folder_path', '=', record.video_folder_path.strip())], limit=1)
            
            if folder and folder.exists:
                record.folder_exists = True
                record.video_files_count = folder.video_count
            else:
                record.folder_exists = False
                record.video_files_count = 0

            # Đếm số bài học video đã được thêm vào khóa học này
            imported_slides = self.env['slide.slide'].search([
                ('channel_id', '=', record.id),
                ('is_local_video', '=', True),
            ])
            record.video_imported_count = len(imported_slides)

    @api.depends('video_folder_path', 'video_folder_id', 'video_folder_id.folder_path')
    def _compute_video_folder_disk_display(self):
        host_base_win = "C:\\Work\\odoo20-docker\\videos"
        for record in self:
            p = (record.video_folder_path or (record.video_folder_id.folder_path if record.video_folder_id else '') or '').strip()
            if not p:
                record.video_folder_disk_display = ""
            elif len(p) >= 2 and p[1] == ':':
                record.video_folder_disk_display = p.replace('/', '\\')
            elif p.startswith('/host_c/'):
                record.video_folder_disk_display = 'C:\\' + p[8:].replace('/', '\\')
            elif p.startswith('/host_d/'):
                record.video_folder_disk_display = 'D:\\' + p[8:].replace('/', '\\')
            elif p.startswith('/mnt/videos/'):
                sub = p[12:].replace('/', '\\')
                record.video_folder_disk_display = f"{host_base_win}\\{sub}"
            else:
                sub = p.replace('/', '\\').strip('\\')
                record.video_folder_disk_display = f"{host_base_win}\\{sub}"

    def action_open_batch_video_wizard(self):
        """Mở bảng quét và TÍCH CHỌN VIDEO từ thư mục để đưa hàng loạt vào Odoo"""
        self.ensure_one()
        folder = self._ensure_video_folder()
        if not folder or not folder.folder_path:
            raise UserError(_(
                "Khóa học này chưa được nhập Thư mục Video!\n"
                "Vui lòng nhập đường dẫn thư mục ổ đĩa vào ô 'Thư mục Video trên Ổ đĩa' trước."
            ))

        if not folder.exists:
            raise UserError(_(
                "Thư mục '%s' (%s) hiện chưa tồn tại trên ổ đĩa!\n\n"
                "Bạn có thể bấm nút 'Tạo Thư mục trên ổ đĩa' để hệ thống tự tạo thư mục trước, sau đó chép file video vào."
            ) % (folder.name, folder.full_path))

        video_files = folder.get_video_files()
        if not video_files:
            raise UserError(_(
                "Thư mục '%s' hiện chưa có file video nào (hỗ trợ .mp4, .mkv, .avi, .mov, .webm)!\n\n"
                "Bạn hãy chép các file video bài học vào thư mục này trên máy tính, rồi bấm lại nút này nhé."
            ) % folder.full_path)

        # Lấy danh sách video đã được thêm vào khóa học này
        existing_slides = self.env['slide.slide'].search([
            ('channel_id', '=', self.id),
            ('is_local_video', '=', True),
        ])
        existing_filenames = set(existing_slides.mapped('local_video_filename'))

        lines = []
        for vf in video_files:
            full_fpath = os.path.join(folder.full_path, vf)
            size_str = ""
            if os.path.exists(full_fpath):
                size_mb = os.path.getsize(full_fpath) / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            
            already = vf in existing_filenames
            base_name, _ext = os.path.splitext(vf)
            clean_title = re.sub(r'[_\-]+', ' ', base_name).strip().title()

            lines.append((0, 0, {
                'selected': not already,  # Tự động tích chọn nếu là video mới chưa thêm
                'filename': vf,
                'name': clean_title,
                'file_size_display': size_str,
                'already_in_course': already,
                'completion_time_minutes': 15.0,
                'is_preview': False,
            }))

        wizard = self.env['slide.channel.batch.video.wizard'].create({
            'channel_id': self.id,
            'folder_path': self.video_folder_path or folder.folder_path,
            'line_ids': lines,
        })

        return {
            'name': _('Tích chọn Video từ Thư mục đưa vào Khóa học: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'slide.channel.batch.video.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_folder_on_disk(self):
        """Tự động tạo thư mục rỗng trên ổ đĩa nếu người dùng chưa kịp tạo"""
        self.ensure_one()
        folder = self._ensure_video_folder()
        if not folder or not folder.full_path:
            raise UserError(_("Vui lòng nhập đường dẫn thư mục ổ đĩa trước!"))
        try:
            os.makedirs(folder.full_path, exist_ok=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Đã tạo thư mục thành công'),
                    'message': _('Đã tạo thư mục rỗng tại đường dẫn: %s\nBạn có thể chép các file video vào thư mục này ngay bây giờ.', folder.full_path),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }
        except Exception as e:
            raise UserError(_("Không thể tạo thư mục '%s': %s") % (folder.full_path, str(e)))

    def action_refresh_folder(self):
        """Quét lại thư mục trên ổ đĩa và cập nhật số lượng video"""
        self.ensure_one()
        folder = self._ensure_video_folder()
        if folder:
            folder._compute_folder_stats()
            self._compute_folder_stats()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Đã quét xong thư mục'),
                    'message': _('Thư mục "%s": Tìm thấy %d video (trong đó %d video đã đưa vào khóa học).',
                                 folder.folder_path, self.video_files_count, self.video_imported_count),
                    'type': 'info',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_add_video_from_folder(self):
        """Mở cửa sổ chọn video đơn lẻ (giữ tương thích)"""
        return self.action_open_batch_video_wizard()

    def action_sync_video_folders(self):
        """Đồng bộ nhanh danh sách thư mục từ máy tính ngay trên form Khóa học"""
        return self.env['slide.video.folder'].action_sync_folders_from_disk()

    def action_open_file_explorer(self):
        """Mở cửa sổ File Explorer duyệt và chọn thư mục máy tính cho khóa học"""
        self.ensure_one()
        curr_p = (self.video_folder_id.folder_path or self.video_folder_path or '').strip()
        if not curr_p:
            curr_p = self.env['slide.video.folder']._get_default_explorer_path()
        wizard = self.env['slide.host.folder.browser.wizard'].create({
            'current_path': curr_p,
            'target_model': 'slide.channel',
            'target_id': self.id,
        })
        wizard._load_folder(curr_p)
        return {
            'name': _('Trình duyệt thư mục máy tính'),
            'type': 'ir.actions.act_window',
            'res_model': 'slide.host.folder.browser.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }



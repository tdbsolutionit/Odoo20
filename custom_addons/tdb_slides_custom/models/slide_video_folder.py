# -*- coding: utf-8 -*-
import os
from odoo import api, fields, models, _
from odoo.exceptions import UserError

VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v')


def is_in_docker():
    return os.path.exists('/.dockerenv') or os.path.exists('/host_c')


class SlideVideoFolder(models.Model):
    _name = 'slide.video.folder'
    _description = 'Quản lý Thư mục Video Khóa học'
    _order = 'name asc'

    name = fields.Char(string='Tên gợi nhớ thư mục', required=True)
    folder_path = fields.Char(
        string='Đường dẫn thư mục',
        required=True,
        help='Bạn có thể nhập tên thư mục con (ví dụ: python) hoặc đường dẫn đầy đủ trên Server. '
             'Nếu nhập tên thư mục con, hệ thống sẽ tự gắn vào thư mục video gốc.'
    )
    full_path = fields.Char(
        string='Đường dẫn đầy đủ trên ổ đĩa',
        compute='_compute_full_path',
        store=True,
        help='Đường dẫn thực tế trên hệ thống được chuẩn hóa tự động.'
    )
    exists = fields.Boolean(
        string='Thư mục tồn tại',
        compute='_compute_folder_stats'
    )
    video_count = fields.Integer(
        string='Số lượng video',
        compute='_compute_folder_stats'
    )
    disk_folder = fields.Selection(
        selection='_get_disk_folder_selection',
        string='Chọn Thư mục có sẵn trên máy tính',
        help='Hệ thống tự động quét các thư mục đang có trong videos/ trên máy tính để bạn chọn bằng chuột, không cần gõ hay dán link.'
    )
    description = fields.Text(string='Mô tả / Ghi chú')
    channel_ids = fields.One2many(
        'slide.channel',
        'video_folder_id',
        string='Các khóa học đang sử dụng'
    )

    @api.model
    def _get_base_video_path(self):
        icp = self.env['ir.config_parameter'].sudo()
        param = ''
        getter = getattr(icp, 'get_str', getattr(icp, 'get_param', None))
        if getter:
            try:
                param = (getter('tdb_slides_custom.base_video_path', default='') or '').strip()
            except Exception:
                param = ''
        if not param:
            rec = icp.search([('key', '=', 'tdb_slides_custom.base_video_path')], limit=1)
            if rec and rec.value:
                param = (rec.value or '').strip()

        if param and os.path.exists(param):
            return os.path.normpath(param)

        # Danh sách đường dẫn video tự động nhận diện theo môi trường
        candidates = [
            'C:\\odoo20\\videos',
            'C:\\odoo20\\odoo\\videos',
            'C:\\Videos',
            'C:\\Work\\odoo20-docker\\videos',
            os.path.abspath(os.path.join(os.getcwd(), 'videos')),
            '/mnt/videos',
            '/data/videos',
        ]
        for c in candidates:
            if os.path.exists(c):
                return os.path.normpath(c)

        # Mặc định theo hệ điều hành nếu chưa tồn tại thư mục nào
        default_p = 'C:\\odoo20\\videos' if os.name == 'nt' else ('/mnt/videos' if is_in_docker() else '/data/videos')
        try:
            os.makedirs(default_p, exist_ok=True)
        except Exception:
            pass
        return os.path.normpath(default_p)

    @api.depends('folder_path')
    def _compute_full_path(self):
        base_path = self._get_base_video_path()
        for record in self:
            path = (record.folder_path or '').strip()
            if not path:
                record.full_path = ''
            elif is_in_docker():
                if len(path) >= 2 and path[1] == ':':
                    drive = path[0].lower()
                    sub = path[2:].replace('\\', '/').lstrip('/')
                    if drive == 'c':
                        record.full_path = os.path.normpath(f'/host_c/{sub}')
                    elif drive == 'd':
                        record.full_path = os.path.normpath(f'/host_d/{sub}')
                    else:
                        record.full_path = path
                elif path.startswith('/'):
                    record.full_path = os.path.normpath(path)
                else:
                    record.full_path = os.path.normpath(os.path.join(base_path, path))
            else:
                # Chạy Native trên Server thật (Ubuntu Linux hoặc Windows Server, không có Docker)
                if os.path.isabs(path):
                    record.full_path = os.path.normpath(path)
                else:
                    record.full_path = os.path.normpath(os.path.join(base_path, path))

    @api.model
    def _get_default_explorer_path(self):
        """Xác định đường dẫn mặc định khi mở File Explorer phù hợp với môi trường Docker hoặc Server thật"""
        if is_in_docker():
            if os.path.exists('/host_c/Users/Thinh/Videos'):
                return 'C:\\Users\\Thinh\\Videos'
            elif os.path.exists('/host_c'):
                return 'C:\\'
            return '/mnt/videos'
        elif os.name == 'nt':
            return 'C:\\'
        else:
            base_p = self._get_base_video_path()
            if base_p and os.path.exists(base_p):
                return base_p
            return '/'

    def action_open_file_explorer(self):
        """Mở trình duyệt thư mục máy tính trực quan để chọn thư mục bằng chuột"""
        self.ensure_one()
        curr_p = (self.folder_path or '').strip()
        if not curr_p:
            curr_p = self._get_default_explorer_path()
        wizard = self.env['slide.host.folder.browser.wizard'].create({
            'current_path': curr_p,
            'target_model': 'slide.video.folder',
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

    def _compute_folder_stats(self):
        for record in self:
            path = record.full_path
            if path and os.path.exists(path) and os.path.isdir(path):
                record.exists = True
                files = record.get_video_files()
                record.video_count = len(files)
            else:
                record.exists = False
                record.video_count = 0

    def get_video_files(self):
        """Trả về danh sách tên file video trong thư mục này"""
        self.ensure_one()
        path = self.full_path
        if not path or not os.path.exists(path) or not os.path.isdir(path):
            return []
        try:
            entries = os.listdir(path)
            video_files = [
                f for f in entries
                if os.path.isfile(os.path.join(path, f)) and f.lower().endswith(VIDEO_EXTENSIONS)
            ]
            video_files.sort()
            return video_files
        except Exception:
            return []

    def action_check_folder(self):
        """Kiểm tra sự tồn tại của thư mục và báo số file video"""
        self.ensure_one()
        path = self.full_path
        if not path:
            raise UserError(_("Vui lòng nhập đường dẫn thư mục!"))
        if not os.path.exists(path):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thư mục chưa tồn tại'),
                    'message': _('Đường dẫn "%s" hiện chưa tồn tại trên ổ đĩa. Bạn có thể bấm nút "Tạo thư mục trên ổ đĩa" để hệ thống tự tạo.', path),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        if not os.path.isdir(path):
            raise UserError(_('Đường dẫn "%s" không phải là một thư mục!', path))

        videos = self.get_video_files()
        video_sample = ", ".join(videos[:5]) if videos else _("(Chưa có file video nào)")
        if len(videos) > 5:
            video_sample += f" ... và {len(videos) - 5} file khác"

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Kiểm tra thành công'),
                'message': _('Thư mục hợp lệ.\nTìm thấy %d file video trong thư mục:\n%s', len(videos), video_sample),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_create_folder_on_disk(self):
        """Cho phép người dùng tự tạo thư mục con trên ổ đĩa trực tiếp từ giao diện Odoo"""
        self.ensure_one()
        path = self.full_path
        if not path:
            raise UserError(_("Vui lòng nhập đường dẫn thư mục trước!"))
        try:
            os.makedirs(path, exist_ok=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Tạo thư mục thành công'),
                    'message': _('Đã tạo thư mục thành công tại đường dẫn: %s. Bạn có thể chép video vào thư mục này ngay bây giờ.', path),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(_("Không thể tạo thư mục '%s': %s") % (path, str(e)))

    def _get_disk_folder_selection(self):
        """Tự động quét các thư mục con trong videos/ trên máy tính để hiển thị danh sách chọn"""
        base_path = self._get_base_video_path()
        if not base_path or not os.path.exists(base_path) or not os.path.isdir(base_path):
            return []
        try:
            subdirs = [
                d for d in os.listdir(base_path)
                if os.path.isdir(os.path.join(base_path, d))
            ]
            subdirs.sort()
            return [(d, d) for d in subdirs]
        except Exception:
            return []

    @api.onchange('disk_folder')
    def _onchange_disk_folder(self):
        """Khi người dùng chọn thư mục từ danh sách có sẵn, tự động điền Tên và Đường dẫn"""
        if self.disk_folder:
            self.folder_path = self.disk_folder
            if not self.name or self.name == _('Thư mục mới'):
                clean_name = self.disk_folder.replace('_', ' ').replace('-', ' ').strip().title()
                self.name = clean_name

    @api.model
    def action_sync_folders_from_disk(self):
        """Tự động quét và nhập tất cả các thư mục con trong videos/ trên máy tính vào Odoo"""
        base_path = self._get_base_video_path()
        if not base_path or not os.path.exists(base_path) or not os.path.isdir(base_path):
            raise UserError(_("Thư mục video gốc '%s' không tồn tại trên hệ thống!") % base_path)

        try:
            subdirs = [
                d for d in os.listdir(base_path)
                if os.path.isdir(os.path.join(base_path, d))
            ]
        except Exception as e:
            raise UserError(_("Lỗi khi đọc thư mục: %s") % str(e))

        if not subdirs:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Chưa có thư mục con trên máy tính'),
                    'message': _('Không tìm thấy thư mục con nào trong "%s" trên máy tính.\nBạn hãy vào thư mục videos/ trên máy tính tạo các thư mục chứa video rồi bấm nút này lại.', base_path),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        created_count = 0
        for d in subdirs:
            existing = self.search([('folder_path', '=', d)])
            if not existing:
                clean_name = d.replace('_', ' ').replace('-', ' ').strip().title()
                self.create({
                    'name': clean_name,
                    'folder_path': d,
                })
                created_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Đồng bộ thành công'),
                'message': _('Đã quét xong ổ đĩa máy tính!\nTìm thấy %d thư mục (trong đó %d thư mục mới được tự động thêm vào Odoo).', len(subdirs), created_count),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }


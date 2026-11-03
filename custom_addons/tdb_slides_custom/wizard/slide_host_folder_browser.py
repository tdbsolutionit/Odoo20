# -*- coding: utf-8 -*-
import os
import re
from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError

VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v')
SKIP_DIRS = {'$recycle.bin', '$sysreset', '$windows.~bt', '$winreagent', 'system volume information', 'perflogs'}


def is_in_docker():
    return os.path.exists('/.dockerenv') or os.path.exists('/host_c')


def win_to_container_path(path):
    r"""Chuyển đổi đường dẫn sang đường dẫn thực tế trên hệ thống (tương thích cả Docker và Server thật không dùng Docker)"""
    if not path:
        return ''
    p = path.strip()
    if not is_in_docker():
        # Server thật (Native Linux Ubuntu hoặc Windows Server): dùng đường dẫn thực tế trực tiếp
        return os.path.normpath(p)

    # Đang chạy trong môi trường Docker kiểm thử
    p_clean = p.replace('/', '\\')
    if len(p_clean) >= 2 and p_clean[1] == ':':
        drive = p_clean[0].lower()
        sub = p_clean[2:].replace('\\', '/').lstrip('/')
        if drive == 'c':
            return os.path.normpath(f'/host_c/{sub}')
        elif drive == 'd':
            return os.path.normpath(f'/host_d/{sub}')
    if p.startswith('/'):
        return os.path.normpath(p)
    return os.path.normpath(os.path.join('/mnt/videos', p))


def container_to_win_path(path):
    """Chuyển đổi đường dẫn hiển thị thân thiện với người dùng"""
    if not path:
        return ''
    if not is_in_docker():
        return os.path.normpath(path)
    p = path.replace('\\', '/')
    if p.startswith('/host_c'):
        sub = p[len('/host_c'):].lstrip('/')
        return f"C:\\{sub}".replace('/', '\\')
    elif p.startswith('/host_d'):
        sub = p[len('/host_d'):].lstrip('/')
        return f"D:\\{sub}".replace('/', '\\')
    if p.startswith('/mnt/videos'):
        sub = p[len('/mnt/videos'):].lstrip('/')
        return f"videos\\{sub}".replace('/', '\\') if sub else "videos"
    return path


class SlideHostFolderBrowserWizard(models.TransientModel):
    _name = 'slide.host.folder.browser.wizard'
    _description = 'Trình duyệt Thư mục Máy tính (File Explorer)'

    current_path = fields.Char(string='Đường dẫn hiện tại', required=True, default='C:\\')
    parent_path = fields.Char(string='Thư mục cha')
    target_model = fields.Char(string='Target Model')
    target_id = fields.Integer(string='Target ID')
    line_ids = fields.One2many(
        'slide.host.folder.browser.line',
        'wizard_id',
        string='Danh sách Thư mục con'
    )
    video_files_html = fields.Html(string='Video trong Thư mục hiện tại')
    current_video_count = fields.Integer(string='Số video trong thư mục hiện tại')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        base_dir = self.env['slide.video.folder']._get_base_video_path()
        if os.path.exists(base_dir):
            default_dir = base_dir
        elif os.path.exists(r'D:\KhoaHoc'):
            default_dir = r'D:\KhoaHoc'
        elif is_in_docker():
            if os.path.exists(win_to_container_path(base_dir)):
                default_dir = base_dir
            elif os.path.exists('/host_d/KhoaHoc'):
                default_dir = 'D:\\KhoaHoc'
            elif os.path.exists('/host_c'):
                default_dir = 'C:\\'
            else:
                default_dir = '/mnt/videos'
        elif os.name == 'nt':
            default_dir = r'D:\KhoaHoc' if os.path.exists(r'D:\KhoaHoc') else ('D:\\' if os.path.exists('D:\\') else 'C:\\')
        else:
            default_dir = '/'
        res['current_path'] = default_dir
        return res

    def _get_parent_path(self, path):
        p = (path or '').rstrip('\\/').strip()
        if not p or p == '/' or (len(p) <= 3 and p.endswith(':')) or (len(p) <= 3 and p.endswith(':\\')):
            return p or '/'
        if '/' in p and not ('\\' in p):
            parent = os.path.dirname(p)
            return parent or '/'
        parts = p.replace('/', '\\').split('\\')
        if len(parts) > 1:
            parent = '\\'.join(parts[:-1])
            if parent.endswith(':'):
                parent += '\\'
            return parent
        return '/'

    def _load_folder(self, raw_path):
        self.ensure_one()
        container_path = win_to_container_path(raw_path)
        self.current_path = raw_path
        self.parent_path = self._get_parent_path(raw_path)

        # Xóa các dòng cũ
        self.line_ids.unlink()

        if not os.path.exists(container_path) or not os.path.isdir(container_path):
            self.video_files_html = Markup("<div class='alert alert-warning'>Thư mục không tồn tại hoặc không thể truy cập.</div>")
            self.current_video_count = 0
            return

        lines = []
        try:
            entries = os.listdir(container_path)
            # Quét các thư mục con
            for entry in sorted(entries, key=lambda s: s.lower()):
                if entry.startswith('.') or entry.lower() in SKIP_DIRS:
                    continue
                sub_container = os.path.join(container_path, entry)
                if os.path.isdir(sub_container):
                    sep = '\\' if ('\\' in raw_path or (len(raw_path) >= 2 and raw_path[1] == ':')) else '/'
                    sub_display = f"{raw_path.rstrip(sep)}{sep}{entry}"
                    v_count = 0
                    try:
                        sub_entries = os.listdir(sub_container)
                        v_count = sum(1 for f in sub_entries if f.lower().endswith(VIDEO_EXTENSIONS))
                    except Exception:
                        pass
                    lines.append((0, 0, {
                        'name': entry,
                        'windows_path': sub_display,
                        'video_count': v_count,
                    }))
            self.line_ids = lines

            # Quét các video trong thư mục hiện tại
            videos = [
                f for f in entries
                if os.path.isfile(os.path.join(container_path, f)) and f.lower().endswith(VIDEO_EXTENSIONS)
            ]
            self.current_video_count = len(videos)
            if videos:
                items_html = ""
                for v in sorted(videos):
                    fpath = os.path.join(container_path, v)
                    size_mb = os.path.getsize(fpath) / (1024 * 1024)
                    items_html += f"<li><strong>{v}</strong> <span class='text-muted'>({size_mb:.1f} MB)</span></li>"
                self.video_files_html = Markup(
                    f"<div class='alert alert-success py-2 mb-0'>"
                    f"<strong>Tìm thấy {len(videos)} file video trong thư mục này:</strong>"
                    f"<ul class='mb-0 mt-1 ps-3'>{items_html}</ul>"
                    f"</div>"
                )
            else:
                self.video_files_html = Markup(
                    "<div class='text-muted py-1'><em>(Thư mục này hiện chưa có file video nào. Bạn có thể duyệt tiếp các thư mục con ở trên).</em></div>"
                )
        except PermissionError:
            self.video_files_html = Markup("<div class='alert alert-danger py-2'>Không có quyền truy cập vào thư mục này.</div>")
        except Exception as e:
            self.video_files_html = Markup(f"<div class='alert alert-danger py-2'>Lỗi: {str(e)}</div>")

    def action_go_up(self):
        """Lên thư mục cha một cấp"""
        self.ensure_one()
        parent = self.parent_path or self._get_parent_path(self.current_path)
        self._load_folder(parent)
        return self._reopen_wizard()

    def action_go_root(self):
        r"""Về thư mục gốc hệ thống (C:\ trên Windows hoặc / trên Linux Server)"""
        self.ensure_one()
        root_dir = 'C:\\' if (is_in_docker() or os.name == 'nt') else '/'
        self._load_folder(root_dir)
        return self._reopen_wizard()

    def action_go_base_videos(self):
        """Lối tắt vào Thư mục Video cấu hình mặc định của Server"""
        self.ensure_one()
        base_dir = self.env['slide.video.folder']._get_base_video_path()
        if is_in_docker():
            if not os.path.exists(win_to_container_path(base_dir)):
                base_dir = '/mnt/videos'
        self._load_folder(base_dir)
        return self._reopen_wizard()

    def action_go_user_videos(self):
        """Lối tắt đến Videos cá nhân / cấu hình"""
        return self.action_go_base_videos()

    def action_go_project_videos(self):
        """Lối tắt đến thư mục video dự án"""
        return self.action_go_base_videos()

    def action_go_c_drive(self):
        r"""Lối tắt đến ổ đĩa C:\ hoặc Root /"""
        return self.action_go_root()

    def action_go_d_drive(self):
        """Lối tắt đến ổ đĩa D:\\KhoaHoc hoặc D:\\"""
        self.ensure_one()
        d_path = r'D:\KhoaHoc' if os.path.exists(r'D:\KhoaHoc') else ('D:\\' if os.path.exists('D:\\') else 'C:\\')
        if is_in_docker():
            if os.path.exists('/host_d/KhoaHoc'):
                d_path = 'D:\\KhoaHoc'
            elif os.path.exists('/host_d'):
                d_path = 'D:\\'
        self._load_folder(d_path)
        return self._reopen_wizard()

    def action_select_current_folder(self):
        """Chọn thư mục hiện tại đang đứng"""
        self.ensure_one()
        return self._apply_path(self.current_path)

    def _apply_path(self, chosen_win_path):
        """Áp dụng đường dẫn Windows đã chọn vào target record"""
        folder_name = os.path.basename(chosen_win_path.rstrip('\\/')) or chosen_win_path
        clean_name = re.sub(r'[_\-]+', ' ', folder_name).strip().title()

        if self.target_model == 'slide.video.folder' and self.target_id:
            record = self.env['slide.video.folder'].browse(self.target_id)
            record.write({
                'folder_path': chosen_win_path,
                'name': clean_name or record.name,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Đã chọn Thư mục'),
                    'message': _('Đã chọn thư mục: %s', chosen_win_path),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

        elif self.target_model == 'slide.channel' and self.target_id:
            channel = self.env['slide.channel'].browse(self.target_id)
            # Tìm hoặc tạo slide.video.folder
            folder = self.env['slide.video.folder'].search([('folder_path', '=', chosen_win_path)], limit=1)
            if not folder:
                folder = self.env['slide.video.folder'].create({
                    'name': clean_name or f"Thư mục {folder_name}",
                    'folder_path': chosen_win_path,
                })
            channel.write({'video_folder_id': folder.id})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Đã gắn Thư mục vào Khóa học'),
                    'message': _('Khóa học "%s" đã được gán thư mục: %s (Tìm thấy %d video)', channel.name, chosen_win_path, folder.video_count),
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

        return {'type': 'ir.actions.act_window_close'}

    def _reopen_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'slide.host.folder.browser.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class SlideHostFolderBrowserLine(models.TransientModel):
    _name = 'slide.host.folder.browser.line'
    _description = 'Dòng Thư mục con trong File Explorer'
    _order = 'name asc'

    wizard_id = fields.Many2one('slide.host.folder.browser.wizard', ondelete='cascade')
    name = fields.Char(string='Tên Thư mục')
    windows_path = fields.Char(string='Đường dẫn Windows')
    video_count = fields.Integer(string='Số video')

    def action_open(self):
        """Mở thư mục con này ra để xem các thư mục bên trong"""
        self.ensure_one()
        wizard = self.wizard_id
        wizard._load_folder(self.windows_path)
        return wizard._reopen_wizard()

    def action_select(self):
        """Chọn ngay thư mục này làm thư mục video cho khóa học"""
        self.ensure_one()
        return self.wizard_id._apply_path(self.windows_path)

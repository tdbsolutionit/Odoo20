# Copyright 2020 Antoni Romera
# Copyright 2017-2019 MuK IT GmbH
# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import hashlib
import json
import logging
import os
import subprocess
import tempfile
from collections import defaultdict

from PIL import Image

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import consteq, human_size
from odoo.tools.mimetypes import guess_mimetype

from ..tools import file

_logger = logging.getLogger(__name__)

OFFICE_EXTENSIONS = {
    # Word
    "doc", "docx", "dot", "dotx", "odt", "rtf",
    # Excel
    "xls", "xlsx", "xlsm", "xlt", "xltx", "ods", "csv", "tsv",
    # PowerPoint
    "ppt", "pptx", "pps", "ppsx", "pot", "potx", "odp",
}

EXCEL_EXTENSIONS = {
    "xls", "xlsx", "xlsm", "xlt", "xltx", "ods", "csv", "tsv"
}

PDF_PREVIEW_DIR = "/tmp/odoo_dms_pdf_cache"



class DMSFile(models.Model):
    _name = "dms.file"
    _description = "File"

    _inherit = [
        "portal.mixin",
        "dms.security.mixin",
        "dms.mixins.thumbnail",
        "mail.thread",
        "mail.activity.mixin",
        "abstract.dms.mixin",
    ]

    _order = "name asc"

    # Database
    active = fields.Boolean(
        string="Archived",
        default=True,
        help="If a file is set to archived, it is not displayed, but still exists.",
    )
    directory_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Directory",
        domain="[('permission_create', '=', True)]",
        context={"dms_directory_show_path": True},
        ondelete="restrict",
        auto_join=True,
        required=True,
        index="btree",
        tracking=True,  # Leave log if "moved" to another directory
    )
    root_directory_id = fields.Many2one(related="directory_id.root_directory_id")
    # Override acording to defined in AbstractDmsMixin
    storage_id = fields.Many2one(
        related="directory_id.storage_id",
        readonly=True,
        prefetch=False,
    )

    path_names = fields.Char(
        compute="_compute_path",
        compute_sudo=True,
        readonly=True,
        store=False,
    )

    path_json = fields.Text(
        compute="_compute_path",
        compute_sudo=True,
        readonly=True,
        store=False,
    )

    tag_ids = fields.Many2many(
        comodel_name="dms.tag",
        relation="dms_file_tag_rel",
        column1="fid",
        column2="tid",
        domain="['|', ('category_id', '=', False),('category_id', '=?', category_id)]",
        string="Tags",
    )

    content = fields.Binary(
        compute="_compute_content",
        inverse="_inverse_content",
        attachment=False,
        prefetch=False,
        required=True,
        store=False,
    )

    extension = fields.Char(compute="_compute_extension", readonly=True, store=True)

    mimetype = fields.Char(
        compute="_compute_mimetype", string="Type", readonly=True, store=True
    )

    size = fields.Float(readonly=True)
    human_size = fields.Char(
        readonly=True,
        string="Size (human readable)",
        compute="_compute_human_size",
        store=True,
    )

    checksum = fields.Char(string="Checksum/SHA1", readonly=True, index="btree")

    content_binary = fields.Binary(attachment=False, prefetch=False)

    save_type = fields.Char(
        compute="_compute_save_type",
        string="Current Save Type",
        prefetch=False,
    )

    migration = fields.Char(
        compute="_compute_migration",
        string="Migration Status",
        readonly=True,
        prefetch=False,
        compute_sudo=True,
        store=True,
    )
    require_migration = fields.Boolean(
        compute="_compute_migration", store=True, compute_sudo=True
    )
    content_file = fields.Binary(attachment=True, prefetch=False)

    preview_html = fields.Html(
        string="Bản xem trước",
        compute="_compute_preview_html",
        sanitize=False,
    )
    is_downloadable = fields.Boolean(
        string="Cho phép tải về",
        default=True,
        tracking=True,
        help="Nếu bỏ chọn, chỉ Leader hoặc Sếp/Admin mới được tải tệp này về máy. Các thành viên khác chỉ được xem trước.",
    )
    is_sharing = fields.Boolean(
        string="Phòng ban Chia sẻ",
        related="directory_id.is_sharing",
        store=True,
        index="btree",
    )
    can_download = fields.Boolean(
        string="Được phép tải về",
        compute="_compute_can_download",
        help="Xác định người dùng hiện tại có quyền tải tệp tin này về máy hay không.",
    )
    can_manage_download = fields.Boolean(
        string="Có quyền sửa cấu hình tải về",
        compute="_compute_can_manage_download",
        help="Chỉ Leader của phòng ban hoặc Sếp/Admin mới có quyền bật/tắt quyền tải về.",
    )

    @api.depends("is_downloadable", "directory_id", "directory_id.is_sharing", "directory_id.leader_ids")
    def _compute_can_download(self):
        user = self.env.user
        is_admin = user._is_superuser() or user.has_group("base.group_system")
        for record in self:
            # 1. Sếp / Admin luôn luôn tải được tất cả các file
            if is_admin:
                record.can_download = True
                continue

            dir_rec = record.directory_id
            is_sharing = dir_rec._is_sharing_directory() if dir_rec else False
            if is_sharing:
                # Tại phòng ban Chia Sẻ (Sharing):
                # File nào tắt "Cho phép tải về" -> Ai cũng chỉ được xem trước, không ai được tải về (trừ Sếp/Admin)
                record.can_download = bool(record.is_downloadable)
            else:
                # Tại các phòng ban thông thường:
                # Leader của phòng ban đó được tải tất cả file trong ban mình
                is_leader = dir_rec._is_user_leader(user) if dir_rec else False
                if is_leader:
                    record.can_download = True
                else:
                    record.can_download = bool(record.is_downloadable)

    @api.depends("directory_id", "directory_id.is_sharing", "directory_id.leader_ids")
    def _compute_can_manage_download(self):
        user = self.env.user
        is_admin = user._is_superuser() or user.has_group("base.group_system")
        for record in self:
            if is_admin:
                record.can_manage_download = True
                continue
            dir_rec = record.directory_id
            if not dir_rec:
                record.can_manage_download = False
                continue
            is_sharing = dir_rec._is_sharing_directory()
            if is_sharing:
                # Tại phòng Chia Sẻ: CHỈ Sếp/Admin (hoặc Leader nếu được phân công) mới có quyền cho phép tải về hay không
                record.can_manage_download = bool(dir_rec._is_user_leader(user))
            else:
                # Tại các phòng ban thông thường: CHỈ LEADER của phòng ban đó mới có quyền quản lý cấu hình tải về
                record.can_manage_download = bool(dir_rec._is_user_leader(user))

    def write(self, vals):
        if "is_downloadable" in vals:
            for record in self:
                if not record.can_manage_download:
                    raise AccessError(_("Bạn không có quyền thay đổi cấu hình cho phép tải về của tệp tin này! Chỉ Sếp/Admin (hoặc Trưởng phòng) mới có quyền này."))
        return super().write(vals)

    @api.onchange("directory_id")
    def _onchange_directory_id_download(self):
        if self.directory_id:
            self.is_downloadable = self.directory_id.default_allow_download

    # Extend inherited field(s)
    image_1920 = fields.Image(compute="_compute_image_1920", store=True, readonly=False)

    @api.depends("mimetype", "content")
    def _compute_image_1920(self):
        """Provide thumbnail automatically if possible."""
        for one in self.filtered("mimetype"):
            # Image.MIME provides a dict of mimetypes supported by Pillow,
            # SVG is not present in the dict but is also a supported image format
            # lacking a better solution, it's being added manually
            # Some component modifies the PIL dictionary by adding PDF as a valid
            # image type, so it must be explicitly excluded.
            if one.mimetype != "application/pdf" and one.mimetype in (
                *Image.MIME.values(),
                "image/svg+xml",
            ):
                one.image_1920 = one.content

    def check_access(self, operation):
        self.mapped("directory_id").check_access(operation)
        return super().check_access(operation)

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for item in self:
            item.access_url = f"/my/dms/file/{item.id}/download"
        return res

    def check_access_token(self, access_token=False):
        if not access_token:
            return False

        if self.access_token and consteq(self.access_token, access_token):
            return True

        token_directory = (
            self.env["dms.directory"]
            .sudo()
            .search([("access_token", "=", access_token)], limit=1)
        )
        if token_directory:
            # The token is known to belong to some directory, but it is not yet
            # valid for this file: it only is when that directory is the file's
            # own directory or one of its ancestors. sudo() so the walk can
            # traverse ancestors the caller is not allowed to read.
            # `seen` bounds the walk: _check_directory_recursion rejects cycles
            # created through the ORM, but this path is reachable anonymously
            # and must not hang on corrupted data.
            directory = self.sudo().directory_id
            seen = set()
            while directory and directory.id not in seen:
                if directory.id == token_directory.id:
                    return True
                seen.add(directory.id)
                directory = directory.parent_id
        return False

    res_model = fields.Char(
        string="Linked attachments model", related="directory_id.res_model"
    )
    res_id = fields.Integer(
        string="Linked attachments record ID", related="directory_id.res_id"
    )
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Attachment File",
        prefetch=False,
        ondelete="cascade",
        index=True,
    )

    def get_human_size(self):
        return human_size(self.size)

    # Helper
    @api.model
    def _get_checksum(self, binary):
        return hashlib.sha1(binary or b"").hexdigest()

    @api.model
    def _get_content_inital_vals(self):
        return {"content_binary": False, "content_file": False}

    def _update_content_vals(self, vals, binary):
        new_vals = vals.copy()
        new_vals.update(
            {
                "checksum": self._get_checksum(binary),
                "size": binary and len(binary) or 0,
            }
        )
        if self.storage_id.save_type in ["file", "attachment"]:
            new_vals["content_file"] = self.content
        else:
            new_vals["content_binary"] = self.content and binary
        return new_vals

    @api.model
    def _get_binary_max_size(self):
        icp = self.env["ir.config_parameter"].sudo()
        if hasattr(icp, "get_int"):
            return icp.get_int("dms.binary_max_size", default=25)
        getter = getattr(icp, "get_str", getattr(icp, "get_param", lambda k, default: 25))
        return int(getter("dms.binary_max_size", default=25))

    @api.model
    def _get_forbidden_extensions(self):
        icp = self.env["ir.config_parameter"].sudo()
        getter = getattr(icp, "get_str", getattr(icp, "get_param", lambda k, default="": ""))
        extensions = getter("dms.forbidden_extensions", default="")
        return [extension.strip() for extension in (extensions or "").split(",") if extension.strip()]

    def _get_icon_placeholder_name(self):
        return self.extension and f"file_{self.extension}.svg" or ""

    def _get_raw_content(self):
        """Safely extract raw binary bytes from content (BinaryValue / bytes / base64)."""
        self.ensure_one()
        val = self.content
        if not val:
            return b""
        if hasattr(val, "content"):
            return val.content
        if isinstance(val, (bytes, bytearray)):
            return bytes(val)
        if isinstance(val, str):
            try:
                return base64.b64decode(val.encode("ascii"))
            except Exception:
                return val.encode("utf-8")
        try:
            return bytes(val)
        except Exception:
            return b""

    def _is_excel_spreadsheet(self):
        """Check if file is an Excel spreadsheet or tabular data format."""
        self.ensure_one()
        ext = (self.extension or "").lower()
        if ext in EXCEL_EXTENSIONS:
            return True
        mimetype = (self.mimetype or "").lower()
        if any(keyword in mimetype for keyword in [
            "spreadsheet", "ms-excel", "csv", "tab-separated"
        ]):
            return True
        return False

    def _is_office_document(self):
        """Check if file is a Microsoft Office or OpenOffice document format."""
        self.ensure_one()
        ext = (self.extension or "").lower()
        if ext in OFFICE_EXTENSIONS:
            return True
        mimetype = (self.mimetype or "").lower()
        if any(keyword in mimetype for keyword in [
            "officedocument", "msword", "ms-excel", "ms-powerpoint", "opendocument", "rtf"
        ]):
            return True
        return False

    def _convert_to_pdf(self):
        """Convert office/document content to PDF using headless LibreOffice.
        Caches the converted PDF to disk to speed up subsequent requests.
        """
        self.ensure_one()
        raw = self._get_raw_content()
        if not raw:
            return None

        try:
            os.makedirs(PDF_PREVIEW_DIR, exist_ok=True)
        except Exception as e:
            _logger.warning("Failed to create PDF cache dir %s: %s", PDF_PREVIEW_DIR, e)

        checksum = self.checksum or hashlib.sha1(raw).hexdigest()
        cache_path = os.path.join(PDF_PREVIEW_DIR, f"{self.id}_{checksum}.pdf")

        if os.path.isfile(cache_path) and os.path.getsize(cache_path) > 0:
            try:
                with open(cache_path, "rb") as f:
                    return f.read()
            except Exception as e:
                _logger.warning("Failed to read cached PDF for file %s: %s", self.id, e)

        ext = (self.extension or "bin").lower()
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, f"document.{ext}")
            try:
                with open(input_file, "wb") as f:
                    f.write(raw)
            except Exception as e:
                _logger.error("Failed to write temporary file for conversion: %s", e)
                return None

            profile_uri = f"file://{os.path.join(temp_dir, 'profile')}"
            cmd = [
                "soffice",
                "--headless",
                f"-env:UserInstallation={profile_uri}",
                "--convert-to",
                "pdf",
                "--outdir",
                temp_dir,
                input_file,
            ]
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=120,
                    check=False,
                )
                if result.returncode != 0:
                    _logger.error(
                        "LibreOffice conversion failed with code %s: %s",
                        result.returncode,
                        result.stderr.decode("utf-8", errors="ignore"),
                    )
                    return None

                # Locate generated PDF
                output_pdf = os.path.join(temp_dir, "document.pdf")
                if not os.path.isfile(output_pdf):
                    for fname in os.listdir(temp_dir):
                        if fname.lower().endswith(".pdf"):
                            output_pdf = os.path.join(temp_dir, fname)
                            break

                if os.path.isfile(output_pdf) and os.path.getsize(output_pdf) > 0:
                    with open(output_pdf, "rb") as f:
                        pdf_data = f.read()
                    try:
                        with open(cache_path, "wb") as f:
                            f.write(pdf_data)
                    except Exception as e:
                        _logger.warning("Failed to write cache for file %s: %s", self.id, e)
                    return pdf_data
                else:
                    _logger.warning("LibreOffice produced no PDF for file %s", self.id)
                    return None
            except subprocess.TimeoutExpired:
                _logger.error("LibreOffice conversion timed out (120s) for file %s", self.id)
                return None
            except FileNotFoundError:
                _logger.error("soffice command not found in system PATH.")
                return None
            except Exception as e:
                _logger.exception("Unexpected error in _convert_to_pdf for file %s: %s", self.id, e)
                return None

    # Actions
    def action_preview_file(self):
        self.ensure_one()
        try:
            action = self.env["ir.actions.actions"]._for_xml_id("dms.action_dms_file")
        except Exception:
            action = {
                "name": _("Files"),
                "type": "ir.actions.act_window",
                "res_model": "dms.file",
            }
        view_id = self.env.ref("dms.view_dms_file_preview_modal", raise_if_not_found=False)
        action["views"] = [(view_id.id if view_id else False, "form")]
        action["res_id"] = self.id
        action["target"] = "current"
        return action

    def action_download_file(self):
        self.ensure_one()
        if not self.can_download:
            raise AccessError(_("Bạn không có quyền tải tệp này về máy!"))
        return {
            "type": "ir.actions.act_url",
            "url": f"/dms/file/{self.id}/download",
            "target": "new",
        }

    def action_bulk_allow_download(self):
        for record in self:
            if not record.can_manage_download:
                raise AccessError(_("Bạn không có quyền quản lý cấu hình tải về cho file '%s'!") % record.name)
        self.write({"is_downloadable": True})

    def action_bulk_disallow_download(self):
        for record in self:
            if not record.can_manage_download:
                raise AccessError(_("Bạn không có quyền quản lý cấu hình tải về cho file '%s'!") % record.name)
        self.write({"is_downloadable": False})

    def action_toggle_downloadable(self):
        for record in self:
            if not record.can_manage_download:
                raise AccessError(_("Bạn không có quyền thay đổi cấu hình cho phép tải về của tệp tin này! Chỉ Trưởng phòng/Quản lý hoặc Quản trị viên mới có quyền này."))
            record.is_downloadable = not record.is_downloadable

    def _compute_preview_html(self):
        for record in self:
            if not record.id:
                record.preview_html = False
                continue
            raw = record._get_raw_content()
            if not raw:
                record.preview_html = (
                    '<div class="d-flex flex-column align-items-center justify-content-center h-100 text-center p-5 text-muted" style="min-height: 60vh;">'
                    '<i class="fa fa-file-o fa-5x mb-3 text-secondary"></i>'
                    '<h4>Tệp này chưa có dữ liệu nội dung.</h4>'
                    '</div>'
                )
                continue

            mimetype = (record.mimetype or "").lower()
            ext = (record.extension or "").lower()
            ts = int(fields.Datetime.now().timestamp())
            preview_url = f"/dms/file/{record.id}/preview?v={ts}"
            download_url = f"/dms/file/{record.id}/download"
            pdf_preview_url = preview_url if record.can_download else f"{preview_url}#toolbar=0&navpanes=0"

            # 1. PDF
            if mimetype == "application/pdf" or ext == "pdf":
                record.preview_html = (
                    f'<iframe src="{pdf_preview_url}" '
                    f'style="width: 100%; height: 86vh; border: none; display: block; background: #525659;"></iframe>'
                )
            # 2. Bảng tính Excel / CSV / ODS (Spreadsheet) -> Trực quan dạng lưới bảng tính tương tác Excel
            elif record._is_excel_spreadsheet():
                record.preview_html = (
                    f'<iframe src="{preview_url}" '
                    f'style="width: 100%; height: 86vh; border: none; display: block; background: #ffffff;"></iframe>'
                )
            # 3. Tài liệu văn phòng khác (Word, PowerPoint, OpenOffice, RTF) -> Preview qua PDF chuyển đổi
            elif record._is_office_document():
                office_pdf_url = f"/dms/file/{record.id}/preview?as_pdf=1&v={ts}"
                if not record.can_download:
                    office_pdf_url = f"{office_pdf_url}#toolbar=0&navpanes=0"
                record.preview_html = (
                    f'<iframe src="{office_pdf_url}" '
                    f'style="width: 100%; height: 86vh; border: none; display: block; background: #525659;"></iframe>'
                )
            # 3. Hình ảnh (Image)
            elif mimetype.startswith("image/") or ext in [
                "png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico", "tiff", "tif"
            ]:
                record.preview_html = (
                    f'<div class="d-flex align-items-center justify-content-center h-100 p-3" '
                    f'style="min-height: 84vh; background: #1e1e1e;">'
                    f'<img src="{preview_url}" '
                    f'style="max-width: 100%; max-height: 84vh; object-fit: contain; '
                    f'box-shadow: 0 4px 20px rgba(0,0,0,0.5); border-radius: 6px; background: #fff;" '
                    f'alt="{record.name}"/>'
                    f'</div>'
                )
            # 4. Video (HTML5 video player)
            elif mimetype.startswith("video/") or ext in [
                "mp4", "webm", "mkv", "mov", "ogg", "avi", "m4v", "wmv", "3gp", "flv"
            ]:
                video_type = mimetype if mimetype.startswith("video/") else f"video/{ext}"
                if ext in ["mp4", "m4v"]:
                    video_type = "video/mp4"
                elif ext == "mov":
                    video_type = "video/mp4"
                elif ext == "webm":
                    video_type = "video/webm"
                elif ext == "ogg":
                    video_type = "video/ogg"

                download_btn = (
                    f'<a href="{download_url}" class="btn btn-sm btn-outline-light"><i class="fa fa-download me-1"></i>Tải video về máy</a>'
                    if record.can_download
                    else '<span class="badge bg-secondary py-2 px-3"><i class="fa fa-lock me-1"></i>Tệp khóa tải về</span>'
                )

                record.preview_html = (
                    f'<div class="d-flex flex-column align-items-center justify-content-center h-100 p-3" '
                    f'style="min-height: 84vh; background: #0b0c10;">'
                    f'<video controls autoplay preload="metadata" style="max-width: 100%; max-height: 76vh; border-radius: 8px; box-shadow: 0 4px 24px rgba(0,0,0,0.8); outline: none;">'
                    f'<source src="{preview_url}" type="{video_type}">'
                    f'Trình duyệt không hỗ trợ phát trực tiếp định dạng video này.'
                    f'</video>'
                    f'<div class="mt-2 text-center">'
                    f'<span class="text-white-50 me-3">{record.name} ({record.human_size or ""})</span>'
                    f'{download_btn}'
                    f'</div>'
                    f'</div>'
                )
            # 5. Âm thanh (Audio)
            elif mimetype.startswith("audio/") or ext in ["mp3", "ogg", "wav", "aac", "m4a", "flac"]:
                audio_type = mimetype if mimetype.startswith("audio/") else f"audio/{ext}"
                if ext == "mp3":
                    audio_type = "audio/mpeg"

                download_btn = (
                    f'<a href="{download_url}" class="btn btn-outline-primary"><i class="fa fa-download me-1"></i>Tải file âm thanh về máy</a>'
                    if record.can_download
                    else '<span class="badge bg-secondary py-2 px-3"><i class="fa fa-lock me-1"></i>Tệp khóa tải về</span>'
                )

                record.preview_html = (
                    f'<div class="d-flex flex-column align-items-center justify-content-center h-100 text-center p-5" '
                    f'style="min-height: 70vh; background: #f8f9fa;">'
                    f'<div class="p-4 rounded-circle bg-primary-subtle text-primary mb-4" style="width: 100px; height: 100px; display: inline-flex; align-items: center; justify-content: center;">'
                    f'<i class="fa fa-music fa-4x"></i>'
                    f'</div>'
                    f'<h4 class="fw-bold mb-2">{record.name}</h4>'
                    f'<p class="text-muted mb-4">{record.human_size or ""}</p>'
                    f'<audio controls autoplay style="width: 70%; max-width: 550px;">'
                    f'<source src="{preview_url}" type="{audio_type}">'
                    f'Trình duyệt không hỗ trợ phát âm thanh.'
                    f'</audio>'
                    f'<div class="mt-4">'
                    f'{download_btn}'
                    f'</div>'
                    f'</div>'
                )
            # 6. Văn bản thuần / Mã nguồn / JSON / HTML / XML / Markdown / Log
            elif mimetype.startswith("text/") or ext in [
                "txt", "log", "json", "xml", "html", "htm", "css", "js", "py", "sql", "sh", "md", "markdown", "yml", "yaml", "ini", "conf"
            ]:
                record.preview_html = (
                    f'<iframe src="{preview_url}" '
                    f'style="width: 100%; height: 86vh; border: none; display: block; background: #fff;"></iframe>'
                )
            # 7. Định dạng khác (File nén, file nhị phân, v.v.)
            else:
                if record.can_download:
                    action_ui = (
                        f'<a href="{download_url}" class="btn btn-primary btn-lg px-4 shadow-sm">'
                        f'<i class="fa fa-download me-2"></i>Tải tệp về máy'
                        f'</a>'
                    )
                else:
                    action_ui = (
                        f'<div class="alert alert-warning d-inline-block py-2 px-4 shadow-sm mb-0">'
                        f'<i class="fa fa-lock me-2"></i>Tệp tin này bị khóa tải về theo chính sách bảo mật nội bộ.'
                        f'</div>'
                    )

                record.preview_html = (
                    f'<div class="d-flex flex-column align-items-center justify-content-center h-100 text-center p-5" '
                    f'style="min-height: 70vh; background: #f8f9fa;">'
                    f'<i class="fa fa-file-archive-o fa-5x text-secondary mb-4"></i>'
                    f'<h3 class="fw-bold mb-2">{record.name}</h3>'
                    f'<p class="text-muted mb-1">Định dạng: <strong>{mimetype or ext.upper()}</strong> ({record.human_size or ""})</p>'
                    f'<p class="text-muted mb-4">Định dạng tệp này không hỗ trợ xem trực tiếp trên trình duyệt.</p>'
                    f'{action_ui}'
                    f'</div>'
                )

    def action_migrate(self, should_logging=True):
        record_count = len(self)
        index = 1
        for dms_file in self:
            if should_logging:
                _logger.info(
                    _(
                        "Migrate File %(index)s of %(record_count)s [ %("
                        "dms_file_migration)s ]",
                        index=index,
                        record_count=record_count,
                        dms_file_migration=dms_file.migration,
                    )
                )
                index += 1
            dms_file.write(
                {
                    "content": dms_file.with_context(**{}).content,
                    "storage_id": dms_file.directory_id.storage_id.id,
                }
            )

    def action_save_onboarding_file_step(self):
        self.env.user.company_id.set_onboarding_step_done(
            "documents_onboarding_file_state"
        )

    def action_wizard_dms_file_move(self):
        items = self.browse(self.env.context.get("active_ids"))
        root_directories = items.mapped("root_directory_id")
        if len(root_directories) > 1:
            raise UserError(_("Only files in the same root directory can be moved."))
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "dms.wizard_dms_file_move_act_window"
        )
        result["context"] = dict(self.env.context)
        return result

    # SearchPanel
    @api.model
    def _search_panel_directory(self, **kwargs):
        search_domain = (kwargs.get("search_domain", []),)
        category_domain = kwargs.get("category_domain", [])
        if category_domain and len(category_domain):
            return "=", category_domain[0][2]
        if search_domain and len(search_domain):
            for domain in search_domain[0]:
                if domain[0] == "directory_id":
                    return domain[1], domain[2]
        return None, None

    @api.model
    def _search_panel_domain(self, field, operator, directory_id, comodel_domain=False):
        if not comodel_domain:
            comodel_domain = []
        files_ids = self.search([("directory_id", operator, directory_id)]).ids
        return expression.AND([comodel_domain, [(field, "in", files_ids)]])

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        """This method is overwritten to make it 'similar' to v13.
        The goal is that the directory searchpanel shows all directories
        (even if some folders have no files).
        """
        if field_name != "directory_id":
            context = {}
            if field_name == "category_id":
                context["category_short_name"] = True
            return super(
                DMSFile, self.with_context(**context)
            ).search_panel_select_range(field_name, **kwargs)

        domain = [("is_hidden", "=", False)]
        # If we pass by context something, we filter more about it we filter
        # the directories of the files, or we show all of them
        if self.env.context.get("active_model") == "dms.directory":
            active_id = self.env.context.get("active_id")
            files = self.env["dms.file"].search(
                [("directory_id", "child_of", active_id)]
            )
            all_directory_ids = []
            for file_record in files:
                directory = file_record.directory_id
                while directory:
                    all_directory_ids.append(directory.id)
                    directory = directory.parent_id
            domain.append(("id", "in", all_directory_ids))
        # Get all possible directories
        comodel_records = (
            self.env["dms.directory"]
            .with_context(directory_short_name=True)
            .search_read(domain, ["display_name", "parent_id"])
        )
        all_record_ids = [rec["id"] for rec in comodel_records]
        field_range = {}
        enable_counters = kwargs.get("enable_counters")
        for record in comodel_records:
            record_id = record["id"]
            parent = record["parent_id"]
            record_values = {
                "id": record_id,
                "display_name": record["display_name"],
                # If the parent directory is not in all the records we should not
                # set parent_id because the user does not have access to parent.
                "parent_id": (
                    parent[0] if parent and parent[0] in all_record_ids else False
                ),
            }
            if enable_counters:
                record_values["__count"] = 0
            field_range[record_id] = record_values
        if enable_counters:
            res = super().search_panel_select_range(field_name, **kwargs)
            for item in res["values"]:
                if item["id"] in field_range:
                    field_range[item["id"]]["__count"] = item["__count"]
        return {"parent_field": "parent_id", "values": list(field_range.values())}

    @api.model
    def search_panel_select_multi_range(self, field_name, **kwargs):
        operator, directory_id = self._search_panel_directory(**kwargs)
        if field_name == "tag_ids":
            sql_query = """
                SELECT t.name AS name, t.id AS id, c.name AS group_name,
                    c.id AS group_id, COUNT(r.fid) AS count
                FROM dms_tag t
                JOIN dms_category c ON t.category_id = c.id
                LEFT JOIN dms_file_tag_rel r ON t.id = r.tid
                WHERE %(filter_by_file_ids)s IS FALSE OR r.fid = ANY(%(file_ids)s)
                GROUP BY c.name, c.id, t.name, t.id
                ORDER BY c.name, c.id, t.name, t.id;
            """
            file_ids = []
            if directory_id:
                file_ids = self.search([("directory_id", operator, directory_id)]).ids
            self.env.cr.execute(
                sql_query,
                {"file_ids": file_ids, "filter_by_file_ids": bool(directory_id)},
            )
            return self.env.cr.dictfetchall()
        if directory_id and field_name in ["directory_id", "category_id"]:
            comodel_domain = kwargs.pop("comodel_domain", [])
            directory_comodel_domain = self._search_panel_domain(
                "file_ids", operator, directory_id, comodel_domain
            )
            return super(
                DMSFile, self.with_context(directory_short_name=True)
            ).search_panel_select_multi_range(
                field_name, comodel_domain=directory_comodel_domain, **kwargs
            )
        return super(
            DMSFile, self.with_context(directory_short_name=True)
        ).search_panel_select_multi_range(field_name, **kwargs)

    # Read
    @api.depends("name", "directory_id", "directory_id.parent_path")
    def _compute_path(self):
        model = self.env["dms.directory"]
        for record in self:
            path_names = [record.display_name]
            path_json = [
                {
                    "model": record._name,
                    "name": record.display_name,
                    "id": isinstance(record.id, int) and record.id or 0,
                }
            ]
            current_dir = record.directory_id
            while current_dir:
                path_names.insert(0, current_dir.name)
                path_json.insert(
                    0,
                    {
                        "model": model._name,
                        "name": current_dir.name,
                        "id": current_dir._origin.id,
                    },
                )
                current_dir = current_dir.parent_id
            record.update(
                {
                    "path_names": "/".join(path_names) if all(path_names) else "",
                    "path_json": json.dumps(path_json),
                }
            )

    @api.depends("name", "mimetype", "content")
    def _compute_extension(self):
        for record in self:
            record.extension = file.guess_extension(
                record.name, record.mimetype, record._get_raw_content()
            )

    @api.depends("content")
    def _compute_mimetype(self):
        for record in self:
            val = record.content
            if hasattr(val, "mimetype") and val.mimetype:
                record.mimetype = val.mimetype
            else:
                binary = record._get_raw_content()
                record.mimetype = guess_mimetype(binary) if binary else False

    @api.depends("size")
    def _compute_human_size(self):
        for item in self:
            item.human_size = human_size(item.size)

    @api.depends("content_binary", "content_file", "attachment_id")
    def _compute_content(self):
        bin_size = self.env.context.get("bin_size", False)
        for record in self:
            if record.content_file:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(**context).content_file
            elif record.content_binary:
                record.content = (
                    record.content_binary
                    if bin_size
                    else base64.b64encode(record.content_binary)
                )
            elif record.attachment_id:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(**context).attachment_id.datas

    @api.depends("content_binary", "content_file")
    def _compute_save_type(self):
        for record in self:
            if record.content_file:
                record.save_type = "file"
            else:
                record.save_type = "database"

    @api.depends("storage_id", "storage_id.save_type")
    def _compute_migration(self):
        storage_model = self.env["dms.storage"]
        save_field = storage_model._fields["save_type"]
        values = save_field._description_selection(self.env)
        selection = {value[0]: value[1] for value in values}
        for record in self:
            storage_type = record.storage_id.save_type
            if storage_type == "attachment" or storage_type == record.save_type:
                record.migration = selection.get(storage_type)
                record.require_migration = False
            else:
                storage_label = selection.get(storage_type)
                file_label = selection.get(record.save_type)
                record.migration = f"{file_label} > {storage_label}"
                record.require_migration = True

    # View
    @api.onchange("category_id")
    def _change_category(self):
        self.tag_ids = self.tag_ids.filtered(
            lambda rec: not rec.category_id or rec.category_id == self.category_id
        )

    # Constrains
    @api.constrains("storage_id", "res_model", "res_id")
    def _check_storage_id_attachment_res_model(self):
        for record in self:
            if record.storage_id.save_type == "attachment" and not (
                record.res_model and record.res_id
            ):
                raise ValidationError(
                    _("A file must have model and resource ID in attachment storage.")
                )

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if not file.check_name(record.name):
                raise ValidationError(_("The file name is invalid."))
            files = record.sudo().directory_id.file_ids
            if files.filtered(
                lambda file, record=record: file.name == record.name and file != record
            ):
                raise ValidationError(
                    _("A file with the same name already exists in this directory.")
                )

    @api.constrains("extension")
    def _check_extension(self):
        if self.filtered(
            lambda rec: rec.extension
            and rec.extension in self._get_forbidden_extensions()
        ):
            raise ValidationError(_("The file has a forbidden file extension."))

    @api.constrains("size")
    def _check_size(self):
        if self.filtered(
            lambda rec: rec.size > self._get_binary_max_size() * 1024 * 1024
        ):
            raise ValidationError(
                _("The maximum upload size is %s MB.") % self._get_binary_max_size()
            )

    # Create, Update, Delete
    def _inverse_content(self):
        updates = defaultdict(set)
        for record in self:
            values = self._get_content_inital_vals()
            binary = record._get_raw_content()
            values = record._update_content_vals(values, binary)
            updates[tools.frozendict(values)].add(record.id)
        for vals, ids in updates.items():
            self.browse(ids).write(dict(vals))

    def _create_model_attachment(self, vals):
        res_vals = vals.copy()
        directory_id = False
        if "directory_id" in res_vals:
            directory_id = res_vals["directory_id"]
        elif self.env.context.get("active_id"):
            directory_id = self.env.context.get("active_id")
        elif self.env.context.get("default_directory_id"):
            directory_id = self.env.context.get("default_directory_id")
        directory = self.env["dms.directory"].browse(directory_id)
        if (
            directory.res_model
            and directory.res_id
            and directory.storage_id_save_type == "attachment"
        ):
            attachment = (
                self.env["ir.attachment"]
                .with_context(dms_file=True)
                .create(
                    {
                        "name": vals["name"],
                        "datas": vals["content"],
                        "res_model": directory.res_model,
                        "res_id": directory.res_id,
                    }
                )
            )
            res_vals["attachment_id"] = attachment.id
            res_vals["res_model"] = attachment.res_model
            res_vals["res_id"] = attachment.res_id
            del res_vals["content"]
        return res_vals

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for dms_file, vals in zip(self, vals_list, strict=False):
            if vals.get("directory_id"):
                directory = self.env["dms.directory"].browse(vals.get("directory_id"))
                names = directory.sudo().file_ids.mapped("name")
            else:
                names = dms_file.sudo().directory_id.file_ids.mapped("name")
            vals["name"] = file.unique_name(dms_file.name, names, dms_file.extension)
        return vals_list

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("directory_id") and "is_downloadable" not in vals:
                directory = self.env["dms.directory"].browse(vals["directory_id"])
                if directory.exists():
                    vals["is_downloadable"] = directory.default_allow_download
        new_vals_list = []
        for vals in vals_list:
            if "attachment_id" not in vals:
                vals = self._create_model_attachment(vals)
            new_vals_list.append(vals)
        return super().create(new_vals_list)

    def unlink(self):
        attachments = self.mapped("attachment_id")
        res = super().unlink()
        if not self.env.context.get("dms_file"):
            attachments.with_context(dms_file=True).unlink()
        return res

    # ----------------------------------------------------------
    # Locking fields and functions
    locked_by = fields.Many2one(comodel_name="res.users")

    is_locked = fields.Boolean(compute="_compute_locked", string="Locked")

    is_lock_editor = fields.Boolean(compute="_compute_locked", string="Editor")

    # ----------------------------------------------------------
    # Locking
    # ----------------------------------------------------------

    def lock(self):
        self.write({"locked_by": self.env.uid})

    def unlock(self):
        self.write({"locked_by": None})

    # Read, View
    @api.depends("locked_by")
    def _compute_locked(self):
        for record in self:
            if record.locked_by.exists():
                record.update(
                    {
                        "is_locked": True,
                        "is_lock_editor": record.locked_by.id == record.env.uid,
                    }
                )
            else:
                record.update({"is_locked": False, "is_lock_editor": False})

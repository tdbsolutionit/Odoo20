# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Phân hệ OdooPLM - Quản lý File History (Lịch sử phiên bản tệp CAD):
1. Tự động lưu snapshot phiên bản cũ của tài liệu trước khi nội dung tệp (datas) bị ghi đè.
2. Đảm bảo tính bất biến (Immutability): Chặn mọi hành vi sửa đổi nội dung tệp hay thông tin lịch sử.
3. Chỉ Quản trị viên PLM hoặc Quản trị hệ thống mới có quyền xóa bản ghi lịch sử.
4. Cung cấp action tải về trực tiếp file snapshot của từng phiên bản cũ.
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PlmDocumentHistory(models.Model):
    _name = "plm.document.history"
    _description = "Lịch sử phiên bản tệp tài liệu PLM"
    _order = "version_number desc, id desc"
    _rec_name = "version"

    document_id = fields.Many2one(
        "ir.attachment",
        string="Tài liệu",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
        help="Tài liệu kỹ thuật / CAD liên kết với phiên bản lịch sử này."
    )
    version = fields.Char(
        string="Phiên bản",
        required=True,
        readonly=True,
        index=True,
        help="Ký hiệu phiên bản tệp (ví dụ: v1, v2, ...)."
    )
    version_number = fields.Integer(
        string="Số thứ tự phiên bản",
        default=1,
        readonly=True,
        index=True,
        help="Số thứ tự số học dùng để tính toán phiên bản tiếp theo."
    )
    datas = fields.Binary(
        string="Tệp snapshot",
        attachment=True,
        readonly=True,
        help="Dữ liệu tệp tại thời điểm snapshot."
    )
    file_name = fields.Char(
        string="Tên tệp",
        readonly=True,
        help="Tên file đính kèm tại thời điểm snapshot."
    )
    file_size = fields.Integer(
        string="Dung lượng (Bytes)",
        readonly=True,
        help="Dung lượng file tính theo bytes."
    )
    file_size_display = fields.Char(
        string="Dung lượng",
        compute="_compute_file_size_display",
        store=False,
        help="Dung lượng tệp hiển thị thân thiện (B, KB, MB)."
    )
    user_id = fields.Many2one(
        "res.users",
        string="Người thực hiện",
        readonly=True,
        default=lambda self: self.env.user,
        help="Kỹ sư đã thực hiện chỉnh sửa hoặc tạo ra phiên bản tệp này."
    )
    create_date = fields.Datetime(
        string="Thời điểm lưu",
        readonly=True,
        help="Thời điểm hệ thống tạo snapshot lịch sử."
    )
    description = fields.Text(
        string="Ghi chú thay đổi",
        help="Ghi chú hoặc lý do thay đổi tệp."
    )

    @api.depends("file_size")
    def _compute_file_size_display(self):
        """Tính toán định dạng dung lượng thân thiện cho người dùng."""
        for rec in self:
            size = rec.file_size or 0
            if size < 1024:
                rec.file_size_display = f"{size} B"
            elif size < 1024 * 1024:
                rec.file_size_display = f"{size / 1024:.1f} KB"
            else:
                rec.file_size_display = f"{size / (1024 * 1024):.2f} MB"

    def write(self, vals):
        """Bảo vệ tính bất biến (Immutability):
        Chặn tuyệt đối mọi hành vi chỉnh sửa nội dung tệp hay thông tin lịch sử.
        Chỉ cho phép cập nhật ghi chú (description).
        """
        allowed_fields = {"description"}
        if any(field not in allowed_fields for field in vals.keys()):
            raise UserError(
                _("Lịch sử phiên bản tệp có tính bất biến nhằm đảm bảo tính toàn vẹn kỹ thuật, không thể chỉnh sửa.")
            )
        return super().write(vals)

    def unlink(self):
        """Bảo vệ lịch sử: Chỉ Quản trị viên PLM hoặc Quản trị hệ thống mới có quyền xóa."""
        is_admin = self.env.user.has_group("plm.group_plm_admin") or self.env.user.has_group("base.group_system")
        if not is_admin:
            raise UserError(_("Chỉ Quản trị viên PLM mới có quyền xóa bản ghi lịch sử phiên bản tài liệu."))
        return super().unlink()

    def action_download_file(self):
        """Cho phép tải trực tiếp file snapshot từ danh sách lịch sử."""
        self.ensure_one()
        filename = self.file_name or f"document_{self.version}"
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/plm.document.history/{self.id}/datas/{filename}?download=true",
            "target": "self",
        }


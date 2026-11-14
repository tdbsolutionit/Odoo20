# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Phân hệ OdooPLM - Quản lý File History (Lịch sử phiên bản tệp CAD):
1. Tự động lưu snapshot phiên bản cũ của tài liệu trước khi nội dung tệp (datas) bị ghi đè.
2. Đảm bảo tính bất biến (Immutability): Chặn mọi hành vi sửa đổi nội dung tệp hay thông tin lịch sử.
3. Chỉ Quản trị viên PLM hoặc Quản trị hệ thống mới có quyền xóa bản ghi lịch sử.
4. Cung cấp action tải về trực tiếp file snapshot của từng phiên bản cũ.
5. Khôi phục phiên bản (Version Restore):
   - Cơ chế bảo vệ 2 lớp: Quyền giữ Key cục bộ và bảo vệ Cụm máy cha (Where-Used Protection).
   - Cơ chế khôi phục bất biến (Append-Only Rollback): Sinh phiên bản tiếp theo mang nội dung cũ mà không mất lịch sử.
   - Ghi nhận nhật ký kiểm toán (Audit Trail) vào Chatter và thông báo Client Action.
"""
import os
import re
import base64
import logging
from markupsafe import Markup
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
        string="Tệp bản vẽ",
        attachment=True,
        readonly=True,
        help="Dữ liệu tệp tại thời điểm lưu phiên bản."
    )
    file_name = fields.Char(
        string="Tên tệp",
        readonly=True,
        help="Tên file đính kèm tại thời điểm lưu phiên bản."
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
        help="Thời điểm hệ thống lưu phiên bản lịch sử."
    )
    description = fields.Text(
        string="Ghi chú",
        help="Ghi chú nghiệp vụ hoặc lý do thay đổi tệp."
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
        Chỉ cho phép cập nhật ghi chú (description) hoặc chạy cơ chế đồng bộ dữ liệu hệ thống (skip_immutability).
        """
        allowed_fields = {"description"}
        if not self.env.context.get("skip_immutability") and any(field not in allowed_fields for field in vals.keys()):
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

    def init(self):
        """Khởi tạo bảng và tự động chuẩn hóa tên tệp, ghi chú và khôi phục dữ liệu cho các bản ghi cũ."""
        super().init()
        self._fix_existing_history_records()

    @api.model
    def _fix_existing_history_records(self):
        """Tự động chuẩn hóa lại tên file, ghi chú nghiệp vụ và khôi phục dữ liệu tệp cho các bản ghi lịch sử cũ."""
        try:
            # 1. Chuẩn hóa tên file
            records = self.sudo().search([])
            for rec in records:
                clean_name = rec.get_clean_filename()
                if clean_name and clean_name != rec.file_name:
                    self.env.cr.execute(
                        "UPDATE plm_document_history SET file_name = %s WHERE id = %s",
                        (clean_name, rec.id)
                    )

            # 2. Thay thế các thuật ngữ snapshot khó hiểu bằng ngôn ngữ kỹ thuật cơ khí rõ ràng
            self.env.cr.execute("""
                UPDATE plm_document_history
                SET description = REPLACE(description, 'Snapshot lưu tại thời điểm Check-in từ SolidWorks CAD', 'Check-in từ SolidWorks CAD')
                WHERE description LIKE '%Snapshot lưu tại thời điểm Check-in từ SolidWorks CAD%';

                UPDATE plm_document_history
                SET description = REPLACE(description, 'Snapshot lưu tại thời điểm Check-in', 'Lưu khi Check-in bản vẽ')
                WHERE description LIKE '%Snapshot lưu tại thời điểm Check-in%';

                UPDATE plm_document_history
                SET description = REPLACE(description, 'Snapshot lưu trước khi chuyển giao Key cho', 'Lưu dự phòng trước khi chuyển Key cho')
                WHERE description LIKE '%Snapshot lưu trước khi chuyển giao Key cho%';

                UPDATE plm_document_history
                SET description = REPLACE(description, 'Tự động lưu snapshot trước khi cập nhật file mới', 'Lưu bản vẽ trước khi cập nhật')
                WHERE description LIKE '%Tự động lưu snapshot trước khi cập nhật file mới%';

                UPDATE plm_document_history
                SET description = REPLACE(description, 'Snapshot', 'Bản vẽ')
                WHERE description LIKE '%Snapshot%';
            """)

            # 3. Khôi phục dữ liệu tệp (datas) cho các bản ghi lịch sử bị thiếu từ tài liệu gốc
            for h in records:
                if not h.get_raw_data() and h.document_id:
                    doc = h.document_id.sudo()
                    doc_bytes = getattr(doc, 'raw', None) or getattr(doc, 'db_datas', None)
                    if not doc_bytes and hasattr(doc, 'datas') and doc.datas:
                        doc_bytes = doc.datas
                    if doc_bytes:
                        try:
                            if isinstance(doc_bytes, (bytes, bytearray)):
                                data_b64 = base64.b64encode(bytes(doc_bytes)).decode()
                            else:
                                data_b64 = str(doc_bytes)
                            h.with_context(skip_immutability=True).write({'datas': data_b64})
                        except Exception as e_backfill:
                            _logger.debug(f"[TDB PLM] Backfill datas for history ID {h.id}: {e_backfill}")
        except Exception as e:
            _logger.debug(f"[TDB PLM] Tự động chuẩn hóa bản ghi lịch sử: {e}")

    def get_raw_data(self):
        """Lấy dữ liệu nhị phân nguyên bản (bytes) của tệp snapshot:
        - Đọc với quyền sudo() để không bị chặn bởi ir.attachment record rules.
        - Xử lý giải mã an toàn cho cả định dạng raw bytes và base64 string/bytes.
        - Tự động fallback về dữ liệu tài liệu gốc (document_id) nếu snapshot chưa có dữ liệu.
        """
        self.ensure_one()
        rec = self.sudo()
        data = rec.datas
        raw_bytes = b""

        def _decode_binary(val):
            if not val:
                return b""
            if isinstance(val, str):
                try:
                    return base64.b64decode(val.strip(), validate=True)
                except Exception:
                    return val.encode('latin1')
            if isinstance(val, (bytes, bytearray)):
                try:
                    decoded = base64.b64decode(val, validate=True)
                    if decoded:
                        return decoded
                except Exception:
                    pass
                return bytes(val)
            return b""

        if data:
            raw_bytes = _decode_binary(data)

        # 1. Fallback tìm trong ir.attachment liên kết trường binary của plm.document.history
        if not raw_bytes:
            att = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('res_field', '=', 'datas'),
            ], limit=1)
            if att:
                raw_bytes = _decode_binary(att.raw or getattr(att, 'db_datas', None))

        # 2. Fallback tìm file từ tài liệu gốc document_id nếu bản ghi lịch sử bị thiếu file
        if not raw_bytes and self.document_id:
            doc = self.document_id.sudo()
            doc_data = getattr(doc, 'raw', None) or getattr(doc, 'db_datas', None)
            if not doc_data and hasattr(doc, 'datas') and doc.datas:
                doc_data = doc.datas
            if doc_data:
                raw_bytes = _decode_binary(doc_data)

        return raw_bytes

    def get_clean_filename(self):
        """Xác định tên tệp tải về có phần mở rộng CAD chuẩn xác (không bị .bin)."""
        self.ensure_one()
        doc = self.document_id
        raw_name = self.file_name or (doc and (doc.cad_name or doc.name)) or f"document_{self.version}"

        # 1. Xử lý trường hợp có slash '/' (ví dụ 'yR-000006/SLDASM' -> 'yR-000006.sldasm')
        if "/" in raw_name:
            base, ext = raw_name.rsplit("/", 1)
            raw_name = f"{base}.{ext.lower()}"

        # 2. Kiểm tra nếu chưa có đuôi mở rộng, tìm từ cad_name hoặc getFileExtension
        base, ext = os.path.splitext(raw_name)
        if not ext and doc:
            if doc.cad_name and "." in doc.cad_name:
                ext = os.path.splitext(doc.cad_name)[1]
            elif doc.name and "/" in doc.name:
                ext = "." + doc.name.rsplit("/", 1)[1].lower()
            elif doc.name and "." in doc.name:
                ext = "." + doc.name.rsplit(".", 1)[1]
            elif hasattr(doc, "getFileExtension"):
                ext = doc.getFileExtension(doc)

            if ext:
                raw_name = f"{base}{ext}"

        # 3. Làm sạch các ký tự đặc biệt không hợp lệ trong filename Windows
        clean_name = re.sub(r'[\\/*?:"<>|]', '_', raw_name)
        return clean_name

    def action_download_file(self):
        """Cho phép tải trực tiếp file snapshot từ danh sách lịch sử qua endpoint chuyên dụng chống đuôi .bin."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/plm/history/download/{self.id}",
            "target": "self",
        }

    def action_restore_version(self):
        """Khôi phục tài liệu về phiên bản snapshot được chọn (Version Restore).
        Áp dụng nguyên tắc Top-Down Key Authority và Linear Evolution (Append-Only Rollback):
        1. Kiểm tra quyền giữ Key cục bộ (Lớp 1 - Local Check):
           Bắt buộc người thực hiện phải là Người giữ Key của tài liệu hoặc Quản trị viên PLM/Hệ thống.
        2. Kiểm tra Cụm máy cha (Lớp 2 - Where-Used Protection):
           Tất cả các Cụm Assembly cha đang sử dụng chi tiết này không được có kỹ sư khác giữ Key.
        3. Thực hiện Khôi phục (Append-Only Rollback):
           Ghi đè nội dung file snapshot lên ir.attachment, tự động sinh phiên bản snapshot mới mang dữ liệu cũ.
        4. Ghi nhận nhật ký kiểm toán (Audit Log) vào Chatter và thông báo Client Action thành công.
        """
        self.ensure_one()
        doc = self.document_id
        if not doc:
            raise UserError(_("Không tìm thấy tài liệu gốc liên kết với bản ghi lịch sử này."))

        if not self.datas:
            raise UserError(_("Bản ghi lịch sử này không có dữ liệu tệp snapshot để khôi phục."))

        is_admin = (
            self.env.is_admin()
            or self.env.user.has_group("plm.group_plm_admin")
            or self.env.user.has_group("base.group_system")
        )

        # ---------------------------------------------------------------------
        # 1. KIỂM TRA QUYỀN GIỮ KEY CỤC BỘ (LỚP 1 - LOCAL CHECK)
        # ---------------------------------------------------------------------
        if not is_admin and doc.key_holder_id != self.env.user:
            raise UserError(_(
                "Bạn không phải Người giữ Key của tài liệu này nên không có quyền khôi phục phiên bản!"
            ))

        # ---------------------------------------------------------------------
        # 2. KIỂM TRA CỤM MÁY CHA (LỚP 2 - WHERE-USED PROTECTION)
        # ---------------------------------------------------------------------
        if not is_admin and hasattr(doc, "get_where_used_documents"):
            parent_assemblies = doc.get_where_used_documents()
            for parent in parent_assemblies:
                if parent.key_holder_id and parent.key_holder_id != self.env.user:
                    parent_name = parent.name or parent.engineering_code or str(parent.id)
                    key_holder_name = parent.key_holder_id.name or _("Kỹ sư khác")
                    raise UserError(_(
                        "Không thể khôi phục! Cụm máy cha '%s' hiện đang bị khóa/giữ Key bởi kỹ sư '%s'. "
                        "Vui lòng liên hệ người giữ Key cụm cha để phối hợp."
                    ) % (parent_name, key_holder_name))

        # ---------------------------------------------------------------------
        # 3. THỰC HIỆN KHÔI PHỤC (APPEND-ONLY ROLLBACK)
        # ---------------------------------------------------------------------
        old_version_name = self.version or f"v{self.version_number}"
        raw_bytes = self.get_raw_data()
        write_vals = {
            "raw": raw_bytes,
            "datas": self.datas,
            "name": self.file_name or doc.name,
            "history_description": _("Khôi phục từ phiên bản %s") % old_version_name,
            "desc_modify": _("Khôi phục nội dung từ phiên bản %s") % old_version_name,
        }

        # Bỏ qua kiểm tra token CAD vì đây là thao tác từ Web
        # Kích hoạt force_create_snapshot để không bị chặn bởi debounce 10s
        write_ctx = {
            "is_web_operation": True,
            "force_create_snapshot": True,
        }
        if is_admin:
            write_ctx["skip_key_holder_check"] = True

        doc.with_context(**write_ctx).write(write_vals)

        # ---------------------------------------------------------------------
        # 4. GHI NHẬN NHẬT KÝ KIỂM TOÁN (AUDIT TRAIL) VÀO CHATTER
        # ---------------------------------------------------------------------
        audit_body = Markup(_(
            "<p><b>Khôi phục phiên bản</b>: Đã khôi phục thành công nội dung từ phiên bản <b>%s</b>.</p>"
        )) % old_version_name

        doc.message_post(
            body=audit_body,
            message_type="notification"
        )

        _logger.info(
            f"[TDB PLM] Kỹ sư '{self.env.user.name}' đã khôi phục thành công tài liệu ID {doc.id} ({doc.name}) về phiên bản {old_version_name}"
        )

        # ---------------------------------------------------------------------
        # 5. PHẢN HỒI THÔNG BÁO CHO NGƯỜI DÙNG (NOTIFICATION BANNER)
        # ---------------------------------------------------------------------
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Khôi phục phiên bản"),
                "message": _("Đã khôi phục thành công tài liệu về phiên bản %s.") % old_version_name,
                "type": "success",
                "sticky": False,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "reload",
                },
            },
        }


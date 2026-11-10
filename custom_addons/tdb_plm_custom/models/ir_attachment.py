# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model ir.attachment cho phân hệ OdooPLM:
1. Quản trị vòng đời Access Token 180 ngày (Layer 2).
2. Xử lý Document Lock độc quyền (Chống sửa đồng thời):
   - Triệt tiêu Race Condition bằng Row-Level Locking (FOR UPDATE NOWAIT).
   - Nút Force Unlock (Cưỡng chế mở khóa) cho Admin/Trưởng phòng có ghi nhận Audit Log.
   - Thao tác Check-out / Check-in trực tiếp từ Web Browser.
   - Các trường tính toán trực quan hóa trạng thái khóa (lock_state, locked_user_id, locked_hostname).
"""
import logging
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    # =========================================================================
    # 1. CÁC TRƯỜNG DỮ LIỆU HIỂN THỊ TRẠNG THÁI KHÓA (DOCUMENT LOCK)
    # =========================================================================
    lock_state = fields.Selection(
        [
            ('unlocked', 'Sẵn sàng (Chưa khóa)'),
            ('locked', 'Đang bị khóa'),
        ],
        string="Trạng thái khóa",
        compute="_compute_lock_state",
        store=False,
        help="Trạng thái khóa độc quyền của tài liệu CAD chống sửa đồng thời."
    )
    locked_user_id = fields.Many2one(
        "res.users",
        string="Người giữ khóa",
        compute="_compute_lock_state",
        store=False
    )
    locked_hostname = fields.Char(
        string="Máy trạm giữ khóa",
        compute="_compute_lock_state",
        store=False
    )
    locked_date = fields.Datetime(
        string="Thời điểm khóa",
        compute="_compute_lock_state",
        store=False
    )

    @api.depends('checkout_ids', 'is_checkout')
    def _compute_lock_state(self):
        """Tính toán trạng thái khóa từ model plm.checkout."""
        for doc in self:
            if doc.checkout_ids:
                co = doc.checkout_ids[0]
                doc.lock_state = 'locked'
                doc.locked_user_id = co.userid
                doc.locked_hostname = co.hostname
                doc.locked_date = co.create_date
            else:
                doc.lock_state = 'unlocked'
                doc.locked_user_id = False
                doc.locked_hostname = False
                doc.locked_date = False

    # =========================================================================
    # 2. KIỂM SOÁT TOKEN 180 NGÀY CHO CAD CLIENT
    # =========================================================================
    def _check_cad_access_token(self):
        """Kiểm tra token thiết bị CAD tại tầng ORM:
        Chặn tuyệt đối mọi thao tác lưu bản vẽ, check-in, check-out từ SolidWorks nếu token bị thu hồi hoặc hết hạn.
        Bỏ qua hoàn toàn đối với các thao tác từ Web Browser.
        """
        # 1. Bỏ qua nếu có cờ định danh thao tác Web
        if self.env.context.get('is_web_operation'):
            return

        # 2. Bỏ qua hoàn toàn nếu request xuất phát từ trình duyệt Web (/web, /odoo)
        try:
            from odoo.http import request
            if request and hasattr(request, 'httprequest'):
                path = getattr(request.httprequest, 'path', '') or ''
                if path.startswith('/web') or path.startswith('/odoo'):
                    return
        except Exception:
            pass

        if 'plm.desktop.token' in self.env.registry:
            token_model = self.env['plm.desktop.token'].sudo()
            tokens = token_model.search([('user_id', '=', self.env.uid)], order='id desc')
            if tokens:
                if any(t.is_revoked for t in tokens):
                    raise UserError(_("Thiết bị CAD đã bị Quản trị viên thu hồi quyền truy cập. Vui lòng liên hệ Quản trị viên."))
                now = fields.Datetime.now()
                active = [t for t in tokens if (not t.is_revoked) and t.expires_at and (t.expires_at > now)]
                if not active:
                    raise UserError(_("Phiên làm việc CAD 180 ngày đã hết hạn. Vui lòng bấm 'Execute New Login' từ SolidWorks để tiếp tục."))

    # =========================================================================
    # 3. DOCUMENT LOCK & RACE CONDITION RESOLUTION
    # =========================================================================
    def checkout(self, hostName, hostPws, showError=True, user_id=False):
        """Khóa tài liệu độc quyền (Check-out) chống sửa đồng thời & chống Race Condition:
        1. Kiểm tra Token CAD 180 ngày.
        2. Dùng FOR UPDATE NOWAIT ở tầng PostgreSQL để triệt tiêu Race Condition khi 2 người cùng bấm một lúc.
        3. Phản hồi thông báo thân thiện rõ ràng nếu tài liệu đã có người khác giữ khóa.
        """
        self._check_cad_access_token()
        if not user_id:
            user_id = self.env.uid

        for doc in self:
            # Nếu đã được chính người này check-out thì cho phép tiếp tục
            if doc.isCheckedOutByMe():
                continue

            # Áp dụng khóa dòng DB (Row-level lock) tránh đụng độ race condition tại t=0
            try:
                self.env.cr.execute(
                    "SELECT id FROM ir_attachment WHERE id = %s FOR UPDATE NOWAIT",
                    [doc.id]
                )
            except Exception as e:
                _logger.warning(f"[TDB PLM LOCK] Xung đột khóa đồng thời cho Doc ID {doc.id}: {e}")
                msg = _("Tài liệu '%s' đang có giao dịch khóa khác xử lý đồng thời. Vui lòng thử lại sau giây lát.") % (doc.name or doc.engineering_code)
                if showError:
                    raise UserError(msg)
                return False, msg

            # Kiểm tra xem tài liệu đã có ai giữ khóa chưa
            existing_checkout = self.env['plm.checkout'].search([('documentid', '=', doc.id)], limit=1)
            if existing_checkout:
                holder_name = existing_checkout.userid.name if existing_checkout.userid else _("Người dùng khác")
                holder_host = existing_checkout.hostname or _("Máy trạm không xác định")
                msg = _("Tài liệu '%s' (Rev %s) HIỆN ĐANG BỊ KHÓA bởi kỹ sư '%s' trên máy trạm '%s'. Bạn chỉ được quyền mở xem (Chế độ Read-only).") % (
                    doc.name or doc.engineering_code,
                    doc.engineering_revision or 0,
                    holder_name,
                    holder_host
                )
                _logger.info(f">>> [TDB PLM LOCK] Từ chối check-out: {msg}")
                if showError:
                    raise UserError(msg)
                return False, msg

        return super().checkout(hostName, hostPws, showError=showError, user_id=user_id)

    # =========================================================================
    # 4. FORCE UNLOCK (PHÁ KHÓA CƯỠNG CHẾ CHO QUẢN TRỊ VIÊN)
    # =========================================================================
    def action_force_unlock(self):
        """Phá khóa cưỡng chế (Force Unlock) dành cho Quản trị viên / Trưởng phòng:
        Dùng khi kỹ sư giữ khóa nhưng nghỉ việc, vắng mặt hoặc máy trạm gặp sự cố.
        Ghi nhận nhật ký kiểm toán (Audit Log) vào Chatter để chống gian lận.
        """
        is_admin = self.env.user.has_group('plm.group_plm_admin') or self.env.user.has_group('base.group_system')
        if not is_admin:
            raise UserError(_("Bạn không có quyền thực hiện Phá khóa cưỡng chế. Chỉ Quản trị viên PLM hoặc Trưởng phòng mới được phép thực hiện."))

        checkout_model = self.env['plm.checkout'].sudo().with_context(is_web_operation=True)
        for doc in self.with_context(is_web_operation=True):
            checkouts = checkout_model.search([('documentid', '=', doc.id)])
            if not checkouts:
                continue

            prev_users = []
            prev_hosts = []
            for co in checkouts:
                if co.userid:
                    prev_users.append(co.userid.name)
                if co.hostname:
                    prev_hosts.append(co.hostname)

            prev_user_str = ", ".join(prev_users) or _("Không rõ")
            prev_host_str = ", ".join(prev_hosts) or _("Không rõ")

            # Xóa bản ghi khóa trong plm.checkout
            checkouts.unlink()

            # Hoàn nguyên cờ ghi được
            doc.write({'engineering_writable': False})
            doc.assign_must_update_flag()

            # Ghi nhận log kiểm toán vào Chatter
            audit_msg = Markup(_(
                "<p><strong>🚨 CƯỠNG CHẾ MỞ KHÓA (FORCE UNLOCK)</strong></p>"
                "<ul>"
                "<li>Người thực hiện phá khóa: <b>%s</b></li>"
                "<li>Kỹ sư từng giữ khóa: <b>%s</b></li>"
                "<li>Máy trạm từng giữ khóa: <b>%s</b></li>"
                "<li>Trạng thái tài liệu: Đã giải phóng khóa thành công, sẵn sàng để kỹ sư khác tiếp quản.</li>"
                "</ul>"
            )) % (self.env.user.name, prev_user_str, prev_host_str)
            doc.message_post(body=audit_msg, message_type='notification')
            _logger.warning(f">>> [TDB PLM FORCE UNLOCK] {self.env.user.name} đã cưỡng chế mở khóa tài liệu {doc.name} (ID {doc.id})")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Phá khóa thành công"),
                'message': _("Tài liệu đã được giải phóng khóa cưỡng chế và sẵn sàng cho kỹ sư khác tiếp quản."),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_web_checkout(self):
        """Cho phép kỹ sư bấm Check-out trực tiếp trên Web Browser."""
        self.ensure_one()
        plm_checkout_id, msg = self.with_context(is_web_operation=True).checkout(f"Web ({self.env.user.name})", "web_browser", showError=True)
        if plm_checkout_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Check-out thành công"),
                    'message': _("Bạn đã nhận quyền khóa độc quyền để chỉnh sửa tài liệu."),
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_web_checkin(self):
        """Cho phép kỹ sư bấm Check-in trực tiếp trên Web Browser."""
        self.ensure_one()
        if not self.isCheckedOutByMe():
            raise UserError(_("Bạn không phải người đang giữ khóa tài liệu này nên không thể Check-in."))
        self.with_context(is_web_operation=True)._check_in()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Check-in thành công"),
                'message': _("Đã hoàn tất chỉnh sửa và giải phóng khóa tài liệu."),
                'type': 'success',
                'sticky': False,
            }
        }

    # =========================================================================
    # 5. CÁC HÀM CAD CHẶN LƯU KHI HẾT HẠN TOKEN
    # =========================================================================
    @api.model
    def SaveOrUpdate(self, documents, default=None):
        """Chặn lưu/cập nhật tài liệu CAD khi token hết hạn."""
        self._check_cad_access_token()
        return super().SaveOrUpdate(documents, default=default)

    @api.model
    def CheckSaveUpdate(self, documents, default=None):
        """Chặn kiểm tra lưu tài liệu CAD khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckSaveUpdate(documents, default=default)

    def CheckIn(self, attrs):
        """Chặn Check-in đơn lẻ khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckIn(attrs)

    def CheckInRecursive(self, request, default=None):
        """Chặn Check-in đệ quy khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckInRecursive(request, default=default)

    def CheckOutRecursive(self, structure, pws_path="", hostname="", force=False):
        """Chặn Check-out đệ quy cây lắp ráp khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckOutRecursive(structure, pws_path=pws_path, hostname=hostname, force=force)

    def saveStructure(self, arguments):
        """Chặn lưu cấu trúc lắp ráp CAD khi token hết hạn."""
        self._check_cad_access_token()
        return super().saveStructure(arguments)

    @api.model
    def createFromProps(self, *args, **kwargs):
        """Chặn tạo/sửa bản vẽ từ hộp thoại Properties của SolidWorks."""
        self._check_cad_access_token()
        return super().createFromProps(*args, **kwargs)

    @api.model
    def saveSingleLevel(self, clientArg):
        """Chặn lưu bản vẽ đơn cấp khi token hết hạn."""
        self._check_cad_access_token()
        return super().saveSingleLevel(clientArg)

    def CheckIn2(self, request, default=None, force=False):
        """Chặn CheckIn2 khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckIn2(request, default=default, force=force)

    def CheckInRecursive2(self, involved_docs_dict, **kargs):
        """Chặn CheckInRecursive2 khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckInRecursive2(involved_docs_dict, **kargs)

    @api.model_create_multi
    def create(self, vals_list):
        """Chặn tạo tài liệu/bản vẽ từ SolidWorks khi token hết hạn."""
        if self.env.context.get('odooPLM'):
            self._check_cad_access_token()
        return super().create(vals_list)

    def write(self, vals):
        """Chặn cập nhật tài liệu/bản vẽ từ SolidWorks khi token hết hạn."""
        if self.env.context.get('odooPLM'):
            self._check_cad_access_token()
        return super().write(vals)

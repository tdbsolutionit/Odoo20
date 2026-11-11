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
    # LỊCH SỬ PHIÊN BẢN TỆP (FILE HISTORY - TASK T4)
    # =========================================================================
    history_ids = fields.One2many(
        "plm.document.history",
        "document_id",
        string="Lịch sử phiên bản",
        readonly=True,
        help="Danh sách các bản snapshot phiên bản tệp cũ của tài liệu này."
    )
    history_count = fields.Integer(
        string="Số phiên bản cũ",
        compute="_compute_history_count",
        store=False,
        help="Tổng số phiên bản tệp cũ đã được lưu trữ."
    )

    @api.depends("history_ids")
    def _compute_history_count(self):
        for doc in self:
            doc.history_count = len(doc.history_ids)

    def action_view_file_history(self):
        """Mở danh sách lịch sử phiên bản của tài liệu hiện tại."""
        self.ensure_one()
        return {
            "name": _("Lịch sử phiên bản: %s") % (self.name or ""),
            "type": "ir.actions.act_window",
            "res_model": "plm.document.history",
            "view_mode": "list,form",
            "domain": [("document_id", "=", self.id)],
            "context": {"default_document_id": self.id},
        }

    def _create_document_history_snapshot(self, description=None, user_id=None, custom_datas=None):
        """Tạo snapshot phiên bản tệp lưu vào plm.document.history khi Check-in hoặc cập nhật file mới."""
        if 'plm.document.history' not in self.env:
            return
        History = self.env['plm.document.history'].sudo()
        now = fields.Datetime.now()

        for doc in self:
            # Lấy dữ liệu file snapshot (ưu tiên custom_datas nếu có, ngược lại lấy từ doc)
            snapshot_datas = custom_datas or doc.datas
            if not snapshot_datas and doc.raw:
                try:
                    import base64
                    snapshot_datas = base64.b64encode(doc.raw).decode()
                except Exception:
                    snapshot_datas = False

            # Bỏ qua nếu tài liệu hoàn toàn không có tệp đính kèm
            if not snapshot_datas:
                continue

            last_history = History.search(
                [('document_id', '=', doc.id)],
                order='version_number desc, id desc',
                limit=1
            )

            # Tránh tạo snapshot trùng lặp nếu vừa tạo trong vòng 3 giây trước với cùng nội dung
            if last_history and last_history.create_date:
                time_diff = (now - last_history.create_date).total_seconds()
                if time_diff < 3 and last_history.datas == snapshot_datas:
                    continue

            next_ver_num = (last_history.version_number + 1) if last_history else 1
            version_str = f"v{next_ver_num}"

            import base64
            try:
                file_bytes = base64.b64decode(snapshot_datas)
                size_bytes = len(file_bytes)
            except Exception:
                size_bytes = doc.file_size or 0

            creator_user = user_id or self.env.user

            History.create({
                'document_id': doc.id,
                'version': version_str,
                'version_number': next_ver_num,
                'datas': snapshot_datas,
                'file_name': doc.name or 'document',
                'file_size': size_bytes,
                'user_id': creator_user.id,
                'description': description or _("Snapshot lưu tại thời điểm Check-in"),
            })
            _logger.info(
                f"[TDB PLM] Đã tạo snapshot phiên bản {version_str} cho tài liệu ID {doc.id} ({doc.name})"
            )

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

            # Xóa bản ghi khóa trong plm.checkout (bỏ qua log Checked-In mặc định vì đã có log Phá khóa)
            checkouts.with_context(skip_checkin_audit=True).unlink()

            # Hoàn nguyên cờ ghi được
            doc.write({'engineering_writable': False})
            doc.assign_must_update_flag()

            # Ghi nhận log kiểm toán vào Chatter (định dạng văn bản thuần, không icon, không in đậm)
            audit_msg = Markup(_(
                "<p>"
                "Cưỡng chế mở khóa (Force Unlock)<br/>"
                "Người thực hiện: %s<br/>"
                "Kỹ sư từng giữ khóa: %s<br/>"
                "Máy trạm từng giữ khóa: %s<br/>"
                "Trạng thái: Đã giải phóng khóa tài liệu thành công."
                "</p>"
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

    def _check_in(self):
        """Kế thừa _check_in để tự động tạo snapshot lịch sử phiên bản khi Check-in."""
        for doc in self:
            doc._create_document_history_snapshot(
                description=_("Snapshot lưu tại thời điểm Check-in"),
                user_id=self.env.user
            )
        return super()._check_in()

    def action_web_checkin(self):
        """Cho phép kỹ sư bấm Check-in trực tiếp trên Web Browser."""
        self.ensure_one()
        if not self.isCheckedOutByMe():
            raise UserError(_("Bạn không phải người đang giữ khóa tài liệu này nên không thể Check-in."))
        self._create_document_history_snapshot(
            description=_("Snapshot lưu tại thời điểm Check-in qua Web"),
            user_id=self.env.user
        )
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

    @api.model
    def CheckIn(self, attrs):
        """Chặn Check-in đơn lẻ khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckIn(attrs)

    @api.model
    def CheckInRecursive(self, request, default=None):
        """Chặn Check-in đệ quy khi token hết hạn và kiểm tra trạng thái khóa rõ ràng chống crash CAD COM."""
        self._check_cad_access_token()

        target_doc = False
        # Kiểm tra trạng thái khóa trước để thông báo rõ ràng cho kỹ sư SolidWorks
        if request and isinstance(request, (list, tuple)) and len(request) > 0:
            doc_args = request[0]
            if isinstance(doc_args, dict):
                eng_code = doc_args.get("engineering_code")
                doc_rev = doc_args.get("engineering_revision")
                if eng_code:
                    target_doc = self.search([
                        ("engineering_code", "=", eng_code),
                        ("engineering_revision", "=", doc_rev)
                    ], limit=1)
                    if target_doc:
                        existing_co = self.env["plm.checkout"].search([("documentid", "=", target_doc.id)], limit=1)
                        if not existing_co:
                            raise UserError(_(
                                "Tài liệu '%s' hiện chưa được Check-out (đang ở trạng thái mở khóa). "
                                "Vui lòng bấm nút Check-out trên SolidWorks trước khi thực hiện Check-in."
                            ) % (target_doc.name or eng_code))
                        elif existing_co.userid != self.env.user:
                            holder_name = existing_co.userid.name if existing_co.userid else _("kỹ sư khác")
                            holder_host = existing_co.hostname or _("máy trạm khác")
                            raise UserError(_(
                                "Tài liệu '%s' đang bị khóa bởi kỹ sư '%s' trên máy trạm '%s'. "
                                "Bạn không thể Check-in tài liệu do người khác đang giữ khóa."
                            ) % (target_doc.name or eng_code, holder_name, holder_host))

        if target_doc:
            target_doc._create_document_history_snapshot(
                description=_("Snapshot lưu tại thời điểm Check-in từ SolidWorks CAD"),
                user_id=self.env.user
            )

        res = super().CheckInRecursive(request, default=default)
        if res is False:
            return []
        return res

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

    @api.model
    def CheckIn2(self, request, default=None, force=False):
        """Chặn CheckIn2 khi token hết hạn."""
        self._check_cad_access_token()
        return super().CheckIn2(request, default=default, force=force)

    @api.model
    def CheckInRecursive2(self, involved_docs_dict, **kargs):
        """Chặn CheckInRecursive2 khi token hết hạn và lưu snapshot lịch sử."""
        self._check_cad_access_token()
        try:
            import json
            involved = json.loads(involved_docs_dict)
            for doc_vals in involved.get("to_check_in", []):
                docId = self.getDocId(doc_vals)
                if docId:
                    docId._create_document_history_snapshot(
                        description=_("Snapshot lưu tại thời điểm Check-in từ CAD Client"),
                        user_id=self.env.user
                    )
        except Exception as e:
            _logger.warning(f"[TDB PLM] Lỗi khi tạo snapshot CheckInRecursive2: {e}")

        return super().CheckInRecursive2(involved_docs_dict, **kargs)

    @api.model_create_multi
    def create(self, vals_list):
        """Chặn tạo tài liệu/bản vẽ từ SolidWorks khi token hết hạn."""
        if self.env.context.get('odooPLM'):
            self._check_cad_access_token()
        return super().create(vals_list)

    def write(self, vals):
        """Kế thừa write của ir.attachment:
        1. Tự động lưu snapshot phiên bản cũ vào plm.document.history khi nội dung file (datas/raw) thay đổi.
        2. Chặn cập nhật tài liệu/bản vẽ từ SolidWorks khi token hết hạn.
        """
        # 1. Bắt sự kiện cập nhật file để lưu snapshot phiên bản cũ
        has_file_change = ('datas' in vals or 'raw' in vals)
        if has_file_change and not self.env.context.get('skip_document_history'):
            if 'plm.document.history' in self.env:
                new_datas = vals.get('datas')
                new_raw = vals.get('raw')
                history_desc = vals.pop('history_description', None)

                for doc in self:
                    # Chỉ lưu cho tài liệu PLM có file cũ thực sự
                    if doc.is_plm and (doc.datas or doc.raw):
                        # Kiểm tra xem nội dung mới có thực sự khác nội dung cũ không
                        is_changed = False
                        if 'datas' in vals:
                            is_changed = (not new_datas or doc.datas != new_datas)
                        elif 'raw' in vals:
                            old_bytes = doc.raw or (base64.b64decode(doc.datas) if doc.datas else b"")
                            new_bytes = new_raw
                            if isinstance(new_raw, str):
                                try:
                                    new_bytes = base64.b64decode(new_raw)
                                except Exception:
                                    new_bytes = new_raw.encode()
                            is_changed = bool(not new_bytes or old_bytes != new_bytes)

                        if is_changed:
                            prev_user = doc.write_uid or doc.create_uid or self.env.user
                            doc._create_document_history_snapshot(
                                description=history_desc or _("Tự động lưu snapshot trước khi cập nhật file mới"),
                                user_id=prev_user
                            )

        # 2. Kiểm tra CAD token (đã miễn trừ Web)
        if self.env.context.get('odooPLM'):
            self._check_cad_access_token()

        return super().write(vals)

    # =========================================================================
    # 6. CHUẨN HÓA NHẬT KÝ CHATTER CHO CHECK-OUT & CHECK-IN
    # =========================================================================
    def message_post(self, **kwargs):
        """Chuẩn hóa nhật ký Chatter cho các sự kiện Check-out và Check-in:
        Ghi rõ chi tiết người thực hiện, máy trạm và trạng thái bằng văn bản thuần ERP.
        Không dùng icon màu mè hay danh sách bullet AI.
        """
        body = kwargs.get('body', '')
        body_str = str(body or '').strip()

        if 'Checked-Out ID' in body_str:
            user_name = self.env.user.name
            hostname = ''
            if self.checkout_ids:
                co = self.checkout_ids[0]
                if co.userid:
                    user_name = co.userid.name
                if co.hostname:
                    hostname = co.hostname
            if not hostname:
                hostname = self.env.context.get('hostname') or 'CAD Client'

            kwargs['body'] = Markup(_(
                "<p>"
                "Khóa tài liệu (Check-out)<br/>"
                "Người thực hiện: %s<br/>"
                "Máy trạm: %s"
                "</p>"
            )) % (user_name, hostname)

        elif body_str == 'Checked-In' or body_str == _('Checked-In'):
            if self.env.context.get('skip_checkin_audit'):
                return self.env['mail.message']
            user_name = self.env.user.name
            kwargs['body'] = Markup(_(
                "<p>"
                "Mở khóa tài liệu (Check-in)<br/>"
                "Người thực hiện: %s"
                "</p>"
            )) % user_name

        return super().message_post(**kwargs)

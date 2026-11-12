# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model ir.attachment cho phân hệ OdooPLM:
1. Kiến trúc Người giữ Key (Key Holder Architecture):
   - Kỹ sư đầu tiên tạo / check-in tài liệu từ máy trạm sẽ giữ Key độc quyền.
   - Kỹ sư giữ Key sau khi Check-in vẫn tiếp tục giữ Key độc quyền của tài liệu.
   - Mọi kỹ sư đều được quyền Check-out tải file về máy trạm phục vụ thiết kế, tham chiếu.
   - Duy nhất kỹ sư giữ Key mới được quyền Check-in cập nhật file lên máy chủ.
   - Kỹ sư khác chỉ được Check-in khi Kỹ sư giữ Key tự nguyện Bàn giao / Nhả Key hoặc Sếp Force Unlock.
2. Lịch sử phiên bản tệp (File History - Task T4):
   - Tự động lưu 1 snapshot phiên bản duy nhất (v1, v2,...) khi Check-in (có debounce chống trùng lặp).
   - Tự động khởi tạo phiên bản v1 cho các tài liệu đã có file gốc trên hệ thống.
3. Quản lý quan hệ file tham chiếu Assembly & Where-Used (Task 5).
4. Quản trị vòng đời Access Token 180 ngày cho CAD Client SolidWorks.
5. Chuẩn hóa nhật ký Chatter bằng văn bản ERP thuần (không icon, không bullet, không gạch đầu dòng).
"""
import logging
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    # =========================================================================
    # 1. KIẾN TRÚC NGƯỜI GIỮ KEY (KEY HOLDER ARCHITECTURE)
    # =========================================================================
    key_holder_id = fields.Many2one(
        "res.users",
        string="Người giữ Key",
        index=True,
        tracking=True,
        help="Kỹ sư giữ quyền Check-in độc quyền cho tài liệu CAD này."
    )
    is_key_holder = fields.Boolean(
        string="Tôi đang giữ Key",
        compute="_compute_is_key_holder",
        store=False
    )
    lock_state = fields.Selection(
        [
            ('unlocked', 'Sẵn sàng'),
            ('locked', 'Đang Check-out'),
        ],
        string="Trạng thái",
        compute="_compute_lock_state",
        store=False,
        help="Trạng thái Check-out của tài liệu."
    )
    locked_user_id = fields.Many2one(
        "res.users",
        string="Người Check-out",
        compute="_compute_lock_state",
        store=False
    )
    locked_hostname = fields.Char(
        string="Máy trạm Check-out",
        compute="_compute_lock_state",
        store=False
    )
    locked_date = fields.Datetime(
        string="Thời điểm Check-out",
        compute="_compute_lock_state",
        store=False
    )

    @api.depends('key_holder_id')
    def _compute_is_key_holder(self):
        for doc in self:
            doc.is_key_holder = (doc.key_holder_id == self.env.user)

    @api.depends('checkout_ids', 'key_holder_id')
    def _compute_lock_state(self):
        """Tính toán trạng thái Check-out từ model plm.checkout."""
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

    def _check_key_holder_permission(self):
        """Kiểm tra quyền giữ Key độc quyền trước khi Check-in:
        Chỉ kỹ sư giữ Key mới được quyền Check-in để ghi đè dữ liệu tệp lên hệ thống.
        Các kỹ sư khác chỉ có quyền Check-out tải file về máy trạm phục vụ tham chiếu.
        """
        for doc in self:
            if not doc.key_holder_id:
                doc.sudo().write({'key_holder_id': self.env.user.id})
                continue

            if doc.key_holder_id != self.env.user:
                key_holder_name = doc.key_holder_id.name
                raise UserError(_(
                    "Tài liệu '%s' hiện do kỹ sư '%s' giữ Key. "
                    "Chỉ người giữ Key mới có quyền Check-in để ghi đè dữ liệu. "
                    "Bạn chỉ được quyền Check-out ở chế độ tham chiếu. "
                    "Vui lòng liên hệ kỹ sư '%s' hoặc Quản trị viên để chuyển giao Key."
                ) % (doc.name or doc.engineering_code, key_holder_name, key_holder_name))

    # =========================================================================
    # 2. LỊCH SỬ PHIÊN BẢN TỆP (FILE HISTORY - TASK T4)
    # =========================================================================
    history_ids = fields.One2many(
        "plm.document.history",
        "document_id",
        string="Lịch sử phiên bản",
        readonly=True,
        help="Danh sách các bản snapshot phiên bản tệp cũ của tài liệu này."
    )
    history_count = fields.Integer(
        string="Số phiên bản",
        compute="_compute_history_count",
        store=False,
        help="Tổng số phiên bản tệp đã được lưu trữ."
    )

    @api.depends("history_ids")
    def _compute_history_count(self):
        for doc in self:
            count = len(doc.history_ids)
            # Tự động tạo snapshot v1 nếu tài liệu đã có file gốc nhưng chưa có lịch sử
            if count == 0 and doc.is_plm and (doc.raw or (doc.file_size and doc.file_size > 0)):
                try:
                    doc._create_document_history_snapshot(
                        description=_("Phiên bản gốc tải lên lần đầu"),
                        user_id=doc.create_uid or self.env.user
                    )
                    count = len(doc.history_ids)
                except Exception as e:
                    _logger.warning(f"[TDB PLM] Lỗi tự động tạo snapshot ban đầu: {e}")
            doc.history_count = count

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
        """Tạo snapshot phiên bản tệp lưu vào plm.document.history (chống trùng lặp tuyệt đối)."""
        if 'plm.document.history' not in self.env:
            return
        History = self.env['plm.document.history'].sudo()
        now = fields.Datetime.now()

        for doc in self:
            last_history = History.search(
                [('document_id', '=', doc.id)],
                order='version_number desc, id desc',
                limit=1
            )

            # Debounce: Bỏ qua tạo snapshot trùng lặp nếu vừa tạo trong vòng 10 giây trước
            if last_history and last_history.create_date:
                time_diff = (now - last_history.create_date).total_seconds()
                if time_diff < 10 and not self.env.context.get('force_create_snapshot'):
                    _logger.info(f"[TDB PLM] Bỏ qua snapshot trùng lặp (vừa tạo cách đây {time_diff:.1f}s)")
                    continue

            raw_bytes = b""
            snapshot_datas = custom_datas

            if not snapshot_datas:
                doc_raw = getattr(doc, 'raw', None)
                if doc_raw:
                    try:
                        raw_bytes = bytes(doc_raw)
                    except Exception:
                        raw_bytes = doc_raw if isinstance(doc_raw, bytes) else b""

                if not raw_bytes:
                    db_d = getattr(doc, 'db_datas', None)
                    if db_d:
                        try:
                            raw_bytes = bytes(db_d)
                        except Exception:
                            raw_bytes = db_d if isinstance(db_d, bytes) else b""

                if raw_bytes:
                    import base64
                    try:
                        snapshot_datas = base64.b64encode(raw_bytes).decode()
                    except Exception:
                        snapshot_datas = False
            else:
                if isinstance(snapshot_datas, bytes):
                    raw_bytes = snapshot_datas
                    import base64
                    snapshot_datas = base64.b64encode(raw_bytes).decode()
                elif isinstance(snapshot_datas, str):
                    import base64
                    try:
                        raw_bytes = base64.b64decode(snapshot_datas)
                    except Exception:
                        raw_bytes = snapshot_datas.encode()

            size_bytes = len(raw_bytes) if raw_bytes else (doc.file_size or 0)
            next_ver_num = (last_history.version_number + 1) if last_history else 1
            version_str = f"v{next_ver_num}"
            creator_user = user_id or self.env.user

            History.create({
                'document_id': doc.id,
                'version': version_str,
                'version_number': next_ver_num,
                'datas': snapshot_datas or False,
                'file_name': doc.name or 'document',
                'file_size': size_bytes,
                'user_id': creator_user.id,
                'description': description or _("Snapshot lưu tại thời điểm Check-in"),
            })
            _logger.info(
                f"[TDB PLM] Đã tạo snapshot phiên bản {version_str} cho tài liệu ID {doc.id} ({doc.name}), size: {size_bytes} B"
            )

    # =========================================================================
    # 3. QUẢN LÝ FILE THAM CHIẾU ASSEMBLY (RELATED REFERENCES & WHERE-USED)
    # =========================================================================
    child_relation_ids = fields.One2many(
        "ir.attachment.relation",
        "parent_id",
        string="Chi tiết con liên quan",
        help="Danh sách các file con mà Assembly này tham chiếu tới."
    )
    parent_relation_ids = fields.One2many(
        "ir.attachment.relation",
        "child_id",
        string="Nơi sử dụng (Where Used)",
        help="Danh sách các Assembly cha đang tham chiếu đến file này."
    )
    child_document_count = fields.Integer(
        string="Số file con liên quan",
        compute="_compute_relation_counts",
        store=False,
        help="Số lượng quan hệ chi tiết con mà tài liệu này tham chiếu tới."
    )
    parent_document_count = fields.Integer(
        string="Số nơi sử dụng",
        compute="_compute_relation_counts",
        store=False,
        help="Số lượng Assembly cha đang sử dụng tài liệu này."
    )

    @api.depends("child_relation_ids", "parent_relation_ids")
    def _compute_relation_counts(self):
        for doc in self:
            doc.child_document_count = len(doc.child_relation_ids)
            doc.parent_document_count = len(doc.parent_relation_ids)

    def get_child_documents(self, link_kinds=None):
        """Trả về Recordset các tài liệu ir.attachment con trực tiếp của tài liệu hiện tại.
        :param link_kinds: Danh sách loại liên kết (ví dụ: ['HiTree', 'LyTree', 'RfTree']),
                           hoặc chuỗi đơn. Nếu None, lấy tất cả loại liên kết trực tiếp.
        :return: Recordset ir.attachment các tài liệu con trực tiếp.
        """
        self.ensure_one()
        relations = self.child_relation_ids
        if link_kinds is not None:
            if isinstance(link_kinds, str):
                link_kinds = [link_kinds]
            relations = relations.filtered(lambda r: r.link_kind in link_kinds)
        return relations.mapped("child_id").exists()

    def get_where_used_documents(self):
        """Trả về Recordset các tài liệu ir.attachment cha đang trực tiếp sử dụng tài liệu này (Where Used).
        :return: Recordset ir.attachment các tài liệu cha.
        """
        self.ensure_one()
        return self.parent_relation_ids.mapped("parent_id").exists()

    def add_child_reference(self, child_doc_id, configuration="", link_kind="HiTree"):
        """Thêm liên kết tham chiếu cha-con an toàn giữa tài liệu hiện tại và tài liệu con.
        :param child_doc_id: ID (int) hoặc Recordset ir.attachment của tài liệu con.
        :param configuration: Tên cấu hình CAD (mặc định '').
        :param link_kind: Loại liên kết CAD (HiTree, LyTree, RfTree,... mặc định 'HiTree').
        :return: Recordset ir.attachment.relation được tạo hoặc đã tồn tại.
        """
        self.ensure_one()
        if not child_doc_id:
            raise UserError(_("Vui lòng chỉ định tài liệu con cần liên kết."))

        child = self.browse(child_doc_id) if isinstance(child_doc_id, int) else child_doc_id
        if not child.exists():
            raise UserError(_("Tài liệu con không tồn tại trên hệ thống."))

        if self.id == child.id:
            raise UserError(_("Tài liệu không thể tự tham chiếu chính mình làm file con."))

        rel_model = self.env["ir.attachment.relation"]
        link_kind = link_kind or "HiTree"
        configuration = configuration or ""

        # Kiểm tra quan hệ trùng lặp theo đúng unique constraint của Omnia: (parent_id, child_id, link_kind)
        existing = rel_model.search([
            ("parent_id", "=", self.id),
            ("child_id", "=", child.id),
            ("link_kind", "=", link_kind),
        ], limit=1)

        if existing:
            if configuration and existing.configuration != configuration:
                existing.write({"configuration": configuration})
            return existing

        return rel_model.create({
            "parent_id": self.id,
            "child_id": child.id,
            "configuration": configuration,
            "link_kind": link_kind,
        })

    def action_view_child_documents(self):
        """Mở danh sách các tài liệu con liên quan."""
        self.ensure_one()
        child_docs = self.get_child_documents()
        return {
            "name": _("Chi tiết con liên quan: %s") % (self.name or self.engineering_code or self.id),
            "type": "ir.actions.act_window",
            "res_model": "ir.attachment",
            "view_mode": "list,form",
            "domain": [("id", "in", child_docs.ids)],
            "context": {"default_is_plm": True},
        }

    def action_view_where_used_documents(self):
        """Mở danh sách các nơi sử dụng tài liệu này (Where Used)."""
        self.ensure_one()
        parent_docs = self.get_where_used_documents()
        return {
            "name": _("Nơi sử dụng (Where Used): %s") % (self.name or self.engineering_code or self.id),
            "type": "ir.actions.act_window",
            "res_model": "ir.attachment",
            "view_mode": "list,form",
            "domain": [("id", "in", parent_docs.ids)],
            "context": {"default_is_plm": True},
        }

    # =========================================================================
    # 4. KIỂM SOÁT TOKEN 180 NGÀY CHO CAD CLIENT
    # =========================================================================
    def _check_cad_access_token(self):
        """Kiểm tra token thiết bị CAD tại tầng ORM:
        Chặn tuyệt đối mọi thao tác lưu bản vẽ, check-in, check-out từ SolidWorks nếu token bị thu hồi hoặc hết hạn.
        Bỏ qua hoàn toàn đối với các thao tác từ Web Browser.
        """
        if self.env.context.get('is_web_operation'):
            return

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
    # 4. THAO TÁC CHECK-OUT VÀ CHECK-IN
    # =========================================================================
    def canCheckOut(self, showError=False):
        """Mở rộng canCheckOut: Cho phép tất cả kỹ sư đều có thể Check-out tài liệu để lấy file về máy trạm."""
        for doc in self:
            if doc.engineering_state not in ['draft', 'wip', False]:
                msg = _("Tài liệu '%s' đang ở trạng thái '%s' nên không thể Check-out.") % (
                    doc.name or doc.engineering_code, doc.engineering_state
                )
                if showError:
                    raise UserError(msg)
                return False, msg
        return True, ""

    def checkout(self, hostName, hostPws, showError=True, user_id=False):
        """Khóa tài liệu Check-out:
        Cho phép mọi kỹ sư Check-out để lấy file về máy trạm SolidWorks (PWS) phục vụ thiết kế và tham chiếu.
        Quyền Check-in ghi đè được kiểm soát riêng biệt bởi Người giữ Key (key_holder_id).
        Nếu tài liệu đang ở trạng thái Nhả Key tự do (chưa có người giữ Key), kỹ sư Check-out đầu tiên sẽ tiếp nhận Key!
        """
        self._check_cad_access_token()
        if not user_id:
            user_id = self.env.uid

        # Kỹ sư Check-out đầu tiên khi tài liệu chưa có người giữ Key sẽ tiếp nhận Key độc quyền
        for doc in self:
            if not doc.key_holder_id:
                user_obj = self.env['res.users'].browse(user_id)
                doc.sudo().write({'key_holder_id': user_id})
                doc.message_post(
                    body=Markup(_(
                        "<p>"
                        "Tiếp nhận quyền giữ Key<br/>"
                        "Kỹ sư tiếp nhận: %s<br/>"
                        "Trạng thái: Đã nhận quyền giữ Key khi Check-out tài liệu."
                        "</p>"
                    )) % user_obj.name,
                    message_type='notification'
                )
                _logger.info(f">>> [TDB PLM] Kỹ sư {user_obj.name} đã tiếp nhận Key tài liệu {doc.name} khi Check-out.")

        return super().checkout(hostName, hostPws, showError=showError, user_id=user_id)

    def action_web_checkout(self):
        """Cho phép kỹ sư bấm Check-out trực tiếp trên Web Browser để lấy file."""
        self.ensure_one()
        self.with_context(is_web_operation=True).checkout(f"Web ({self.env.user.name})", "web_browser", showError=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _check_in(self):
        """Kế thừa _check_in:
        1. Kiểm tra quyền giữ Key độc quyền (chỉ người giữ Key mới được Check-in).
        2. Tự động lưu duy nhất 1 snapshot lịch sử phiên bản.
        3. Giải phóng bản ghi check-out của người dùng này (kể cả khi file_size == 0).
        Người giữ Key sau khi Check-in vẫn tiếp tục giữ quyền Key cho tài liệu này.
        """
        self._check_key_holder_permission()

        for doc in self:
            # 1. Tạo snapshot lịch sử phiên bản duy nhất
            doc._create_document_history_snapshot(
                description=_("Snapshot lưu tại thời điểm Check-in"),
                user_id=self.env.user
            )

            # 2. Xóa bản ghi plm.checkout của chính người này để giải phóng trạng thái khóa
            checkout_records = self.env['plm.checkout'].sudo().search([
                ('documentid', '=', doc.id),
                ('userid', '=', self.env.user.id)
            ])
            if checkout_records:
                checkout_records.with_context(skip_checkin_audit=True).unlink()

            doc.write({'engineering_writable': False})

        # 3. Gọi super để PLM thực hiện các logic cơ sở khác (tránh bị chặn khi file_size <= 0)
        try:
            super()._check_in()
        except Exception as e:
            _logger.info(f"[TDB PLM] Base _check_in note: {e}")

        return True

    def action_web_checkin(self):
        """Cho phép kỹ sư giữ Key bấm Check-in trực tiếp trên Web Browser."""
        self.ensure_one()
        self._check_key_holder_permission()

        if not self.isCheckedOutByMe():
            self.with_context(is_web_operation=True).checkout(f"Web ({self.env.user.name})", "web_browser", showError=False)

        # _check_in() đã tự động tạo 1 snapshot duy nhất và xóa checkout
        self.with_context(is_web_operation=True)._check_in()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # =========================================================================
    # 5. FORCE UNLOCK & BÀN GIAO KEY CHO KỸ SƯ / QUẢN TRỊ VIÊN
    # =========================================================================
    def action_force_unlock(self):
        """Phá khóa cưỡng chế / Chuyển giao Key dành cho Quản trị viên PLM hoặc Trưởng phòng."""
        return self.action_open_transfer_key_wizard()

    def action_open_transfer_key_wizard(self):
        """Mở popup chuyển giao quyền giữ Key (Force Unlock hoặc Kỹ sư bàn giao Key)."""
        self.ensure_one()
        is_admin = self.env.user.has_group('plm.group_plm_admin') or self.env.user.has_group('base.group_system')
        is_holder = (self.key_holder_id == self.env.user)

        if not is_admin and not is_holder:
            raise UserError(_("Bạn không có quyền chuyển giao Key. Chỉ Quản trị viên PLM hoặc người đang giữ Key mới được phép thực hiện."))

        title = _("Chuyển giao quyền giữ Key (Force Unlock)") if is_admin else _("Bàn giao quyền giữ Key")
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': 'plm.transfer.key.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_id': self.id,
                'default_current_key_holder_id': self.key_holder_id.id if self.key_holder_id else False,
            }
        }

    # =========================================================================
    # 6. CÁC HÀM CAD CHẶN LƯU & BẢO VỆ CLIENT COM
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
        """Chặn Check-in đơn lẻ khi không giữ Key hoặc token hết hạn."""
        self._check_cad_access_token()
        doc_id = attrs.get("id")
        if doc_id:
            doc = self.browse(doc_id)
            doc._check_key_holder_permission()
        return super().CheckIn(attrs)

    @api.model
    def CheckInRecursive(self, request, default=None):
        """Chặn Check-in đệ quy khi token hết hạn, kiểm tra quyền giữ Key và bảo vệ client CAD chống crash COM."""
        self._check_cad_access_token()

        target_doc = False
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
                        # 1. Kiểm tra quyền giữ Key độc quyền
                        target_doc._check_key_holder_permission()

                        # 2. Đảm bảo bản ghi checkout tồn tại cho user này để tránh lỗi COM SolidWorks
                        if not target_doc.isCheckedOutByMe():
                            host_name = doc_args.get("hostname") or "SolidWorks CAD"
                            target_doc.checkout(host_name, "pws", showError=False)

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
        """Chặn CheckIn2 khi không giữ Key hoặc token hết hạn."""
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
                    docId._check_key_holder_permission()
                    docId._create_document_history_snapshot(
                        description=_("Snapshot lưu tại thời điểm Check-in từ CAD Client"),
                        user_id=self.env.user
                    )
        except Exception as e:
            _logger.warning(f"[TDB PLM] Lỗi khi tạo snapshot CheckInRecursive2: {e}")

        return super().CheckInRecursive2(involved_docs_dict, **kargs)

    @api.model_create_multi
    def create(self, vals_list):
        """Tự động thiết lập người tạo đầu tiên làm Người giữ Key."""
        if self.env.context.get('odooPLM'):
            self._check_cad_access_token()
        for vals in vals_list:
            if not vals.get('key_holder_id'):
                vals['key_holder_id'] = self.env.user.id
        return super().create(vals_list)

    def write(self, vals):
        """Kế thừa write của ir.attachment:
        1. Kiểm tra quyền giữ Key nếu có thay đổi nội dung file.
        2. Tự động lưu snapshot phiên bản cũ vào plm.document.history khi nội dung file thay đổi.
        3. Chặn cập nhật từ CAD khi token hết hạn.
        """
        has_file_change = ('raw' in vals or 'datas' in vals or 'db_datas' in vals)

        if has_file_change and not self.env.context.get('skip_key_holder_check'):
            is_admin = self.env.is_admin() or self.env.user.has_group('plm.group_plm_admin') or self.env.user.has_group('base.group_system')
            for doc in self:
                if doc.key_holder_id and doc.key_holder_id != self.env.user and not is_admin:
                    key_holder_name = doc.key_holder_id.name
                    raise UserError(_(
                        "Tài liệu '%s' hiện do kỹ sư '%s' giữ Key. "
                        "Chỉ người giữ Key mới có quyền cập nhật tệp lên hệ thống. "
                        "Vui lòng liên hệ kỹ sư '%s' hoặc Quản trị viên để chuyển giao Key."
                    ) % (doc.name or doc.engineering_code, key_holder_name, key_holder_name))

        if has_file_change and not self.env.context.get('skip_document_history'):
            if 'plm.document.history' in self.env:
                history_desc = vals.pop('history_description', None)
                for doc in self:
                    if getattr(doc, 'is_plm', False):
                        prev_user = doc.write_uid or doc.create_uid or self.env.user
                        doc._create_document_history_snapshot(
                            description=history_desc or _("Tự động lưu snapshot trước khi cập nhật file mới"),
                            user_id=prev_user
                        )

        if self.env.context.get('odooPLM'):
            self._check_cad_access_token()

        return super().write(vals)

    # =========================================================================
    # 7. CHUẨN HÓA NHẬT KÝ CHATTER CHO CHECK-OUT & CHECK-IN
    # =========================================================================
    def message_post(self, **kwargs):
        """Chuẩn hóa nhật ký Chatter cho các sự kiện Check-out và Check-in:
        Ghi rõ người thực hiện, máy trạm bằng văn bản thuần ERP (không icon, không bullet).
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

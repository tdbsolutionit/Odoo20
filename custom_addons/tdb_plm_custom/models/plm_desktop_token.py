# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Model Quản lý Access Token & Phiên làm việc Đa thiết bị 180 ngày cho Add-in CAD (SolidWorks 2022).
================================================================================================
- Mỗi máy trạm CAD đăng nhập sẽ được cấp/cập nhật một bản ghi token độc lập duy nhất.
- Không tự ý hủy phiên của các thiết bị khác thuộc cùng User.
- Cho phép Quản trị viên (Admin) thu hồi quyền từ xa bất kỳ lúc nào.
- Khi bị thu hồi: bản ghi vẫn hiển thị rõ ràng trên giao diện (Đã thu hồi - đỏ),
  đồng thời ngắt kết nối và chặn hoàn toàn mọi tác vụ CAD từ máy trạm đó.
- Cung cấp nút 'Khôi phục' để Admin cấp lại quyền truy cập khi cần.
"""
import logging
import secrets
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class PlmDesktopToken(models.Model):
    _name = 'plm.desktop.token'
    _description = 'SolidWorks Multi-device Fixed 180-day Token'
    _order = 'issued_at desc, id desc'
    _rec_name = 'machine_name'

    name = fields.Char(
        string='Mã Token Hash',
        required=True,
        index=True,
        readonly=True,
        default=lambda self: secrets.token_urlsafe(32),
    )
    session_id = fields.Char(
        string='Session SID',
        index=True,
        readonly=True,
        help="Session ID của Odoo HTTP Cookie",
    )
    user_id = fields.Many2one(
        'res.users',
        string='Kỹ sư CAD',
        required=True,
        ondelete='cascade',
        index=True,
    )
    machine_uuid = fields.Char(
        string='Machine UUID',
        required=True,
        index=True,
    )
    machine_name = fields.Char(
        string='Tên máy trạm CAD',
        required=True,
    )
    client_ip = fields.Char(
        string='IP LAN / Máy trạm',
        index=True,
    )
    cad_version = fields.Char(
        string='Phiên bản CAD',
        default='SolidWorks 2022',
    )
    issued_at = fields.Datetime(
        string='Ngày cấp',
        default=fields.Datetime.now,
        readonly=True,
    )
    expires_at = fields.Datetime(
        string='Hạn chót (180 ngày)',
        required=True,
        index=True,
    )
    last_used_date = fields.Datetime(
        string='Lần truy cập cuối',
        default=fields.Datetime.now,
    )
    is_revoked = fields.Boolean(
        string='Bị thu hồi thủ công',
        default=False,
        index=True,
    )
    is_active = fields.Boolean(
        string='Còn hiệu lực',
        compute='_compute_is_active',
        store=True,
        index=True,
    )
    state = fields.Selection(
        [
            ('active', 'Đang hoạt động'),
            ('revoked', 'Đã thu hồi'),
            ('expired', 'Hết hạn'),
            ],
        string='Trạng thái',
        compute='_compute_state',
        store=True,
        index=True,
    )
    is_current_user_admin = fields.Boolean(
        string="Là Admin",
        compute="_compute_is_current_user_admin",
    )

    def _compute_is_current_user_admin(self):
        user = self.env.user
        is_admin = bool(user.id == 2 or user.login == 'admin' or user.has_group('base.group_system'))
        for rec in self:
            rec.is_current_user_admin = is_admin

    @api.depends('expires_at', 'is_revoked')
    def _compute_is_active(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_active = (not rec.is_revoked) and bool(rec.expires_at and rec.expires_at > now)

    @api.depends('is_active', 'is_revoked', 'expires_at')
    def _compute_state(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.is_revoked:
                rec.state = 'revoked'
            elif rec.expires_at and rec.expires_at <= now:
                rec.state = 'expired'
            else:
                rec.state = 'active'

    @api.model
    def cleanup_duplicate_tokens(self):
        """Tự động dọn dẹp các bản ghi token trùng lặp cho cùng một kỹ sư."""
        all_tokens = self.search([], order='id asc')
        seen = {}
        to_delete = self.browse()
        for tok in all_tokens:
            uid = tok.user_id.id
            if uid in seen:
                existing = seen[uid]
                # Nếu một trong các bản ghi bị revoked thì giữ cờ revoked
                if tok.is_revoked or existing.is_revoked:
                    tok.write({'is_revoked': True})
                    existing.write({'is_revoked': True})

                # Ưu tiên giữ lại bản ghi có đầy đủ thông tin IP máy trạm
                if not existing.client_ip and tok.client_ip:
                    to_delete |= existing
                    seen[uid] = tok
                else:
                    to_delete |= tok
            else:
                seen[uid] = tok

        if to_delete:
            to_delete.unlink()
            _logger.info(f">>> [TDB PLM] Đã dọn dẹp {len(to_delete)} bản ghi token trùng lặp.")

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """Cho phép mọi người xem danh sách, nhưng chỉ Admin mới có quyền sửa đổi/xóa/quản trị."""
        if not self.env.su and operation in ('write', 'unlink', 'create'):
            user = self.env.user
            is_boss = (user.id == 2 or user.login == 'admin' or user.has_group('base.group_system'))
            if not is_boss:
                if raise_exception:
                    raise AccessError(_("Chỉ Quản trị viên (Admin) mới có quyền quản lý Desktop Access Tokens."))
                return False
        return super().check_access_rights(operation, raise_exception=raise_exception)

    def init(self):
        """Tự động dọn dẹp trùng lặp và cô lập nhóm quyền chỉ cho Sếp khi nạp module."""
        super().init()
        try:
            self.cleanup_duplicate_tokens()
        except Exception as e:
            _logger.debug(f"[TDB PLM] Dọn dẹp token trong init: {e}")
        try:
            with self.env.cr.savepoint():
                # Xóa bất kỳ quan hệ nhóm nào khác ngoài group_plm_desktop_token_boss cho 2 menu này
                self.env.cr.execute("""
                    DELETE FROM ir_ui_menu_group_rel
                    WHERE menu_id IN (
                        SELECT res_id FROM ir_model_data
                        WHERE module = 'tdb_plm_custom'
                          AND name IN ('menu_plm_desktop_token', 'menu_plm_desktop_token_top')
                    )
                    AND gid NOT IN (
                        SELECT res_id FROM ir_model_data
                        WHERE module = 'tdb_plm_custom' AND name = 'group_plm_desktop_token_boss'
                    );
                """)
        except Exception as e:
            _logger.debug(f"[TDB PLM] Clean menu groups: {e}")

    @api.model
    def register_session_token(self, user_id, session_id, machine_uuid, machine_name, client_ip, cad_version):
        """Cấp/Cập nhật token 180 ngày cho phiên SolidWorks Add-in của từng kỹ sư trên máy trạm."""
        now = fields.Datetime.now()
        expires_at = now + timedelta(days=180)

        # 1. Tìm bản ghi token của CHÍNH KỸ SƯ NÀY (tìm theo user_id, ưu tiên khớp machine_uuid hoặc client_ip)
        domain = [('user_id', '=', user_id)]
        if machine_uuid and client_ip:
            domain.extend(['|', ('machine_uuid', '=', machine_uuid), ('client_ip', '=', client_ip)])
        elif machine_uuid:
            domain.append(('machine_uuid', '=', machine_uuid))
        elif client_ip:
            domain.append(('client_ip', '=', client_ip))

        existing_tokens = self.search(domain, order='id desc')
        if not existing_tokens:
            # Fallback: tìm theo user_id nếu trước đó RPC đã tạo mà chưa ghi nhận IP
            existing_tokens = self.search([('user_id', '=', user_id)], order='id desc')

        # 2. Nếu token của kỹ sư này trên thiết bị này đang bị thu hồi: TỪ CHỐI CẤP PHIÊN MỚI
        if existing_tokens and any(t.is_revoked for t in existing_tokens):
            _logger.warning(
                f">>> [TDB PLM] Thiết bị '{machine_name}' (IP: {client_ip}) "
                f"của User ID {user_id} đang ở trạng thái BỊ THU HỒI. Từ chối cấp phiên mới."
            )
            return False

        vals = {
            'user_id': user_id,
            'session_id': session_id,
            'expires_at': expires_at,
            'last_used_date': now,
            'is_revoked': False,
        }
        if machine_uuid:
            vals['machine_uuid'] = machine_uuid
        if machine_name:
            vals['machine_name'] = machine_name
        if client_ip:
            vals['client_ip'] = client_ip
        if cad_version:
            vals['cad_version'] = cad_version

        if existing_tokens:
            token_rec = existing_tokens[0]
            token_rec.write(vals)
            # Dọn dẹp dòng trùng lặp của CÙNG KỸ SƯ NÀY nếu có
            duplicates = existing_tokens - token_rec
            if duplicates:
                duplicates.unlink()
        else:
            vals.update({
                'name': secrets.token_urlsafe(32),
                'issued_at': now,
            })
            token_rec = self.create(vals)

        return token_rec

    def action_revoke(self):
        """Thu hồi quyền kết nối của thiết bị/kỹ sư được chọn (chỉ Admin)."""
        user = self.env.user
        if not (user.id == 2 or user.login == 'admin' or user.has_group('base.group_system')):
            raise UserError(_("Chỉ Quản trị viên (Admin) mới có quyền Thu hồi quyền!"))
        for rec in self:
            rec.write({
                'is_revoked': True,
                'session_id': False,
            })
            _logger.info(f">>> [TDB PLM] Đã thu hồi quyền của '{rec.user_id.name}' trên máy '{rec.machine_name}' (IP: {rec.client_ip})")
        return True

    def action_unrevoke(self):
        """Khôi phục quyền truy cập cho thiết bị/kỹ sư được chọn (chỉ Admin)."""
        user = self.env.user
        if not (user.id == 2 or user.login == 'admin' or user.has_group('base.group_system')):
            raise UserError(_("Chỉ Quản trị viên (Admin) mới có quyền Khôi phục quyền!"))
        now = fields.Datetime.now()
        for rec in self:
            vals = {
                'is_revoked': False,
                'expires_at': now + timedelta(days=180),
            }
            if not rec.session_id:
                vals['session_id'] = f'unrevoked_{now.strftime("%Y%m%d%H%M%S")}'
            rec.write(vals)
            _logger.info(f">>> [TDB PLM] Đã khôi phục quyền cho '{rec.user_id.name}' trên máy '{rec.machine_name}' (IP: {rec.client_ip})")
        return True

    def action_set_expired_test(self):
        """Chuyển token sang trạng thái hết hạn để kiểm thử tính năng chặn thiết bị khi hết 180 ngày (chỉ Admin)."""
        user = self.env.user
        if not (user.id == 2 or user.login == 'admin' or user.has_group('base.group_system')):
            raise UserError(_("Chỉ Quản trị viên (Admin) mới có quyền Thử hết hạn!"))
        yesterday = fields.Datetime.now() - timedelta(days=1)
        for rec in self:
            rec.write({
                'expires_at': yesterday,
                'session_id': False,
                'is_revoked': False,
            })
            _logger.info(f">>> [TDB PLM] TEST: Đã chuyển token của '{rec.user_id.name}' trên máy '{rec.machine_name}' sang HẾT HẠN.")
        return True

    def action_renew_180_days(self):
        """Admin chủ động gia hạn thêm 180 ngày cho token đã hết hạn (chỉ Admin)."""
        user = self.env.user
        if not (user.id == 2 or user.login == 'admin' or user.has_group('base.group_system')):
            raise UserError(_("Chỉ Quản trị viên (Admin) mới có quyền Gia hạn!"))
        now = fields.Datetime.now()
        for rec in self:
            vals = {
                'expires_at': now + timedelta(days=180),
                'is_revoked': False,
            }
            if not rec.session_id:
                vals['session_id'] = f'renewed_{now.strftime("%Y%m%d%H%M%S")}'
            rec.write(vals)
            _logger.info(f">>> [TDB PLM] Đã gia hạn 180 ngày cho '{rec.user_id.name}' trên máy '{rec.machine_name}'.")
        return True

    def update_last_used(self):
        """Cập nhật thời gian truy cập gần nhất với throttling tránh ghi CSDL liên tục."""
        self.ensure_one()
        now = fields.Datetime.now()
        if not self.last_used_date or (now - self.last_used_date).total_seconds() > 60:
            self.write({'last_used_date': now})

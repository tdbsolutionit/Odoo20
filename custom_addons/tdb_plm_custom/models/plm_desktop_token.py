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
        """Tự động dọn dẹp các bản ghi token trùng lặp cho cùng một kỹ sư và máy trạm."""
        all_tokens = self.search([], order='id asc')
        seen = {}
        to_delete = self.browse()
        for tok in all_tokens:
            key = (tok.user_id.id, tok.client_ip or tok.machine_name)
            if key in seen:
                # Nếu bản ghi trùng là revoked, giữ cờ revoked cho bản ghi đại diện
                if tok.is_revoked:
                    seen[key].write({'is_revoked': True})
                to_delete |= tok
            else:
                seen[key] = tok
        if to_delete:
            to_delete.unlink()
            _logger.info(f">>> [TDB PLM] Đã dọn dẹp {len(to_delete)} bản ghi token trùng lặp.")

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """Chỉ cho phép tài khoản Administrator (id: 2 hoặc login: admin) truy cập model này."""
        if not self.env.su:
            user = self.env.user
            if user.id != 2 and user.login != 'admin':
                if raise_exception:
                    raise AccessError(_("Chỉ tài khoản Administrator mới có quyền xem và quản lý Desktop Access Tokens."))
                return False
        return super().check_access_rights(operation, raise_exception=raise_exception)

    @api.model
    def web_search_read(self, *args, **kwargs):
        """Chặn triệt để giao diện Web Client (list/form view) đối với mọi tài khoản không phải Admin."""
        if not self.env.su:
            user = self.env.user
            if user.id != 2 and user.login != 'admin':
                raise AccessError(_("Chỉ tài khoản Administrator mới có quyền truy cập Desktop Access Tokens."))
        return super().web_search_read(*args, **kwargs)

    @api.model
    def search_read(self, *args, **kwargs):
        """Chặn triệt để đọc bản ghi đối với mọi tài khoản không phải Admin."""
        if not self.env.su:
            user = self.env.user
            if user.id != 2 and user.login != 'admin':
                raise AccessError(_("Chỉ tài khoản Administrator mới có quyền truy cập Desktop Access Tokens."))
        return super().search_read(*args, **kwargs)

    @api.model
    def _register_hook(self):
        """Chạy tự động mỗi khi máy chủ Odoo khởi động hoặc nạp Registry: Quét sạch menu top bar khỏi CSDL."""
        super()._register_hook()
        try:
            self.env.cr.execute("""
                DELETE FROM ir_ui_menu_group_rel
                WHERE menu_id IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top'
                );
                DELETE FROM ir_ui_menu
                WHERE id IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top'
                );
                DELETE FROM ir_model_data
                WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top';

                -- Xóa mọi menu mồ côi trên thanh top bar trỏ tới action token
                DELETE FROM ir_ui_menu
                WHERE parent_id = (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu')
                  AND (name ILIKE '%desktop%token%' OR name ILIKE '%quản lý thiết bị%');

                -- Thu hồi quyền base.group_system khỏi mọi tài khoản kỹ sư
                DELETE FROM res_groups_users_rel
                WHERE gid IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'base' AND name IN ('group_system', 'group_erp_manager')
                )
                AND uid NOT IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'base' AND name = 'user_admin'
                )
                AND uid != 2
                AND uid IN (
                    SELECT id FROM res_users
                    WHERE login != 'admin'
                      AND (
                          login ILIKE '%kysu%'
                          OR login ILIKE '%ky_su%'
                          OR name ILIKE '%ky su%'
                          OR name ILIKE '%kỹ sư%'
                          OR name ILIKE '%engineer%'
                      )
                );
            """)
            self.env.cr.commit()
        except Exception as e:
            _logger.warning(f"[TDB PLM] Không thể quét menu trong _register_hook: {e}")

    def init(self):
        """Tự động dọn dẹp trùng lặp, xóa menu top bar và giới hạn nghiêm ngặt quyền chỉ cho Admin."""
        super().init()
        try:
            self.cleanup_duplicate_tokens()
        except Exception as e:
            _logger.debug(f"[TDB PLM] Dọn dẹp token trong init: {e}")
        try:
            # 1. Xóa hoàn toàn menu Desktop Access Tokens khỏi thanh Top Bar (ir_ui_menu và ir_model_data)
            self.env.cr.execute("""
                DELETE FROM ir_ui_menu_group_rel
                WHERE menu_id IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top'
                );
                DELETE FROM ir_ui_menu
                WHERE id IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top'
                );
                DELETE FROM ir_model_data
                WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top';
            """)

            # 2. Thu hồi quyền truy cập model khỏi bất kỳ nhóm nào không phải base.group_system
            self.env.cr.execute("""
                DELETE FROM ir_model_access
                WHERE model_id = (SELECT id FROM ir_model WHERE model = 'plm.desktop.token')
                  AND group_id != (SELECT res_id FROM ir_model_data WHERE module = 'base' AND name = 'group_system');

                -- 3. Đảm bảo menu Desktop Access Tokens trong Cấu hình chỉ liên kết với base.group_system
                DELETE FROM ir_ui_menu_group_rel
                WHERE menu_id IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token'
                );

                INSERT INTO ir_ui_menu_group_rel (menu_id, gid)
                SELECT m.res_id, g.res_id
                FROM ir_model_data m
                CROSS JOIN ir_model_data g
                WHERE m.module = 'tdb_plm_custom'
                  AND m.name = 'menu_plm_desktop_token'
                  AND g.module = 'base'
                  AND g.name = 'group_system'
                ON CONFLICT DO NOTHING;

                -- 4. Đảm bảo action_plm_desktop_token chỉ liên kết với duy nhất base.group_system
                DELETE FROM ir_act_window_group_rel
                WHERE act_id IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'tdb_plm_custom' AND name = 'action_plm_desktop_token'
                );

                INSERT INTO ir_act_window_group_rel (act_id, gid)
                SELECT a.res_id, g.res_id
                FROM ir_model_data a
                CROSS JOIN ir_model_data g
                WHERE a.module = 'tdb_plm_custom' AND a.name = 'action_plm_desktop_token'
                  AND g.module = 'base' AND g.name = 'group_system'
                ON CONFLICT DO NOTHING;

                -- 5. Thu hồi quyền base.group_system và base.group_erp_manager khỏi toàn bộ tài khoản kỹ sư
                DELETE FROM res_groups_users_rel
                WHERE gid IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'base' AND name IN ('group_system', 'group_erp_manager')
                )
                AND uid NOT IN (
                    SELECT res_id FROM ir_model_data
                    WHERE module = 'base' AND name = 'user_admin'
                )
                AND uid != 2
                AND uid IN (
                    SELECT id FROM res_users
                    WHERE login != 'admin'
                      AND (
                          login ILIKE '%kysu%'
                          OR login ILIKE '%ky_su%'
                          OR name ILIKE '%ky su%'
                          OR name ILIKE '%kỹ sư%'
                          OR name ILIKE '%engineer%'
                      )
                );
            """)
        except Exception as e:
            _logger.warning(f"[TDB PLM] Cập nhật phân quyền desktop token trong init: {e}")

    @api.model
    def register_session_token(self, user_id, session_id, machine_uuid, machine_name, client_ip, cad_version):
        """Cấp/Cập nhật token 180 ngày cho phiên SolidWorks Add-in, gộp bản ghi trùng lặp."""
        now = fields.Datetime.now()
        expires_at = now + timedelta(days=180)

        # 1. Tìm toàn bộ bản ghi token hiện có của cùng user
        existing_tokens = self.search([
            '|',
            ('user_id', '=', user_id),
            ('machine_uuid', '=', machine_uuid),
        ], order='id desc')

        # 2. Nếu bất kỳ bản ghi nào của thiết bị này đang bị thu hồi: TỪ CHỐI CẤP PHIÊN MỚI
        if existing_tokens and any(t.is_revoked for t in existing_tokens):
            _logger.warning(
                f">>> [TDB PLM] Thiết bị '{machine_name}' (IP: {client_ip}) "
                f"của User ID {user_id} đang ở trạng thái BỊ THU HỒI. Từ chối cấp phiên mới."
            )
            return False

        vals = {
            'session_id': session_id,
            'machine_uuid': machine_uuid,
            'machine_name': machine_name,
            'client_ip': client_ip,
            'cad_version': cad_version,
            'expires_at': expires_at,
            'last_used_date': now,
            'is_revoked': False,
        }

        if existing_tokens:
            token_rec = existing_tokens[0]
            token_rec.write(vals)
            # Dọn dẹp các dòng dư thừa nếu có
            duplicates = existing_tokens - token_rec
            if duplicates:
                duplicates.unlink()
        else:
            vals.update({
                'name': secrets.token_urlsafe(32),
                'user_id': user_id,
                'issued_at': now,
            })
            token_rec = self.create(vals)

        return token_rec

    def action_revoke(self):
        """Thu hồi quyền kết nối của thiết bị (chặn đứng mọi thao tác kể cả đăng nhập lại)."""
        for rec in self:
            tokens = self.search([
                '|',
                ('user_id', '=', rec.user_id.id),
                ('machine_uuid', '=', rec.machine_uuid),
            ]) | rec
            tokens.write({
                'is_revoked': True,
                'session_id': False,
            })
            _logger.info(f">>> [TDB PLM] Đã thu hồi quyền máy trạm '{rec.machine_name}' (IP: {rec.client_ip})")

            # Gộp các dòng trùng lặp thành 1 dòng duy nhất cho sạch giao diện
            if len(tokens) > 1:
                (tokens - rec).unlink()

        return True

    def action_unrevoke(self):
        """Khôi phục quyền truy cập cho thiết bị (cho phép sử dụng tiếp ngay lập tức, không cần đăng nhập lại)."""
        now = fields.Datetime.now()
        for rec in self:
            tokens = self.search([
                '|',
                ('user_id', '=', rec.user_id.id),
                ('machine_uuid', '=', rec.machine_uuid),
            ]) | rec
            for tok in tokens:
                vals = {
                    'is_revoked': False,
                    'expires_at': now + timedelta(days=180),
                }
                if not tok.session_id:
                    vals['session_id'] = f'unrevoked_{now.strftime("%Y%m%d%H%M%S")}'
                tok.write(vals)
                _logger.info(f">>> [TDB PLM] Đã khôi phục quyền cho máy trạm '{tok.machine_name}' (IP: {tok.client_ip}), cho phép dùng tiếp không cần đăng nhập lại.")

            # Gộp các dòng trùng lặp thành 1 dòng duy nhất
            if len(tokens) > 1:
                (tokens - rec).unlink()

        return True

    def action_set_expired_test(self):
        """Chuyển token sang trạng thái hết hạn để kiểm thử tính năng chặn thiết bị khi hết 180 ngày."""
        yesterday = fields.Datetime.now() - timedelta(days=1)
        for rec in self:
            tokens = self.search([
                '|',
                ('user_id', '=', rec.user_id.id),
                ('machine_uuid', '=', rec.machine_uuid),
            ]) | rec
            for tok in tokens:
                tok.write({
                    'expires_at': yesterday,
                    'session_id': False,
                    'is_revoked': False,
                })
                _logger.info(f">>> [TDB PLM] TEST: Đã chuyển token máy trạm '{tok.machine_name}' sang trạng thái HẾT HẠN.")

            if len(tokens) > 1:
                (tokens - rec).unlink()

        return True

    def action_renew_180_days(self):
        """Admin chủ động gia hạn thêm 180 ngày cho token đã hết hạn."""
        now = fields.Datetime.now()
        for rec in self:
            tokens = self.search([
                '|',
                ('user_id', '=', rec.user_id.id),
                ('machine_uuid', '=', rec.machine_uuid),
            ]) | rec
            for tok in tokens:
                vals = {
                    'expires_at': now + timedelta(days=180),
                    'is_revoked': False,
                }
                if not tok.session_id:
                    vals['session_id'] = f'renewed_{now.strftime("%Y%m%d%H%M%S")}'
                tok.write(vals)
                _logger.info(f">>> [TDB PLM] Đã gia hạn 180 ngày cho máy trạm '{tok.machine_name}'.")

            if len(tokens) > 1:
                (tokens - rec).unlink()

        return True

    def update_last_used(self):
        """Cập nhật thời gian truy cập gần nhất với throttling tránh ghi CSDL liên tục."""
        self.ensure_one()
        now = fields.Datetime.now()
        if not self.last_used_date or (now - self.last_used_date).total_seconds() > 60:
            self.write({'last_used_date': now})

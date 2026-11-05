# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Model Quản lý Access Token & Phiên làm việc Đa thiết bị 180 ngày cho Add-in CAD (SolidWorks 2022).
================================================================================================
- Mỗi máy trạm CAD đăng nhập sẽ được cấp/cập nhật một bản ghi token độc lập.
- Không tự ý hủy phiên của các thiết bị khác thuộc cùng User.
- Cho phép Quản trị viên (Admin) thu hồi quyền từ xa bất kỳ lúc nào.
"""
import logging
import secrets
from datetime import timedelta
from odoo import api, fields, models, _

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
    )
    is_active = fields.Boolean(
        string='Còn hiệu lực',
        compute='_compute_is_active',
        store=True,
        index=True,
    )

    @api.depends('expires_at', 'is_revoked')
    def _compute_is_active(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_active = (not rec.is_revoked) and bool(rec.expires_at and rec.expires_at > now)

    @api.model
    def register_session_token(self, user_id, session_id, machine_uuid, machine_name, client_ip, cad_version):
        """Cấp/Cập nhật token 180 ngày cho phiên SolidWorks Add-in."""
        now = fields.Datetime.now()
        expires_at = now + timedelta(days=180)

        # Tìm token của cùng thiết bị (theo user_id và machine_uuid)
        token_rec = self.search([
            ('user_id', '=', user_id),
            ('machine_uuid', '=', machine_uuid),
            ('is_revoked', '=', False),
        ], limit=1)

        vals = {
            'session_id': session_id,
            'machine_name': machine_name,
            'client_ip': client_ip,
            'cad_version': cad_version,
            'expires_at': expires_at,
            'last_used_date': now,
            'is_revoked': False,
        }

        if token_rec:
            token_rec.write(vals)
        else:
            vals.update({
                'name': secrets.token_urlsafe(32),
                'user_id': user_id,
                'machine_uuid': machine_uuid,
                'issued_at': now,
            })
            token_rec = self.create(vals)

        return token_rec

    def action_revoke(self):
        """Thu hồi quyền kết nối của thiết bị và xóa phiên làm việc tức thì."""
        for rec in self:
            rec.write({'is_revoked': True})
            # Xóa session khỏi bộ lưu trữ Odoo Session Store nếu có session_id
            if rec.session_id:
                try:
                    from odoo.http.session import session_store
                    store = session_store()
                    sess = store.get(rec.session_id)
                    if sess:
                        store.delete(sess)
                        _logger.info(f">>> [TDB PLM] Đã hủy thành công Odoo session: {rec.session_id}")
                except Exception as e:
                    _logger.warning(f"[TDB PLM] Không thể xóa Odoo session: {e}")

    def action_unrevoke(self):
        """Khôi phục hiệu lực cho token nếu còn trong hạn 180 ngày."""
        now = fields.Datetime.now()
        for rec in self:
            if rec.expires_at and rec.expires_at > now:
                rec.write({'is_revoked': False})
            else:
                rec.write({
                    'is_revoked': False,
                    'expires_at': now + timedelta(days=180),
                })

    def update_last_used(self):
        """Cập nhật thời gian truy cập gần nhất với throttling tránh ghi CSDL liên tục."""
        self.ensure_one()
        now = fields.Datetime.now()
        if not self.last_used_date or (now - self.last_used_date).total_seconds() > 60:
            self.write({'last_used_date': now})

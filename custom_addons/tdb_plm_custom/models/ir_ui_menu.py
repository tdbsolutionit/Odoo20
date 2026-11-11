# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Ghi đè bảo mật hiển thị menu hệ thống (ir.ui.menu).
Duy nhất tài khoản Administrator gốc (id=2 hoặc login='admin') mới được nhìn thấy
và thao tác trên các menu Desktop Access Tokens của SolidWorks CAD.
Mọi tài khoản Kỹ sư khác (Kỹ sư A,...) bị ẩn triệt để toàn bộ menu và popup liên quan.
"""
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def _filter_visible_menus(self):
        """Ẩn toàn bộ menu Desktop Access Tokens đối với mọi tài khoản không phải Administrator."""
        menus = super()._filter_visible_menus()
        user = self.env.user
        if not self.env.su and user.id != 2 and user.login != 'admin':
            menus = menus.filtered(lambda m: not (
                (m.action and 'plm.desktop.token' in getattr(m.action, 'res_model', '')) or
                'desktop access token' in (m.name or '').lower() or
                'quản lý thiết bị cad' in (m.name or '').lower() or
                'desktop_token' in (m.xmlid or '').lower()
            ))
        return menus

    @api.model
    def load_menus(self, debug):
        """Bảo vệ hai lớp: Loại bỏ triệt để các menu Desktop Tokens khỏi payload JSON trả về cho trình duyệt."""
        res = super().load_menus(debug)
        user = self.env.user
        if not self.env.su and user.id != 2 and user.login != 'admin':
            to_remove = set()
            for menu_id, menu in list(res.items()):
                if isinstance(menu, dict):
                    name = (menu.get('name') or '').lower()
                    xmlid = (menu.get('xmlid') or '').lower()
                    action = str(menu.get('action') or '').lower()
                    if (
                        'desktop access token' in name or
                        'quản lý thiết bị cad' in name or
                        'desktop_token' in xmlid or
                        'plm.desktop.token' in action
                    ):
                        to_remove.add(menu_id)

            for menu_id in to_remove:
                menu = res.pop(menu_id, None)
                if menu:
                    parent_id = menu.get('parent_id')
                    if isinstance(parent_id, (list, tuple)) and parent_id:
                        pid = parent_id[0]
                        if pid in res and 'children' in res[pid] and menu_id in res[pid]['children']:
                            res[pid]['children'].remove(menu_id)

        return res

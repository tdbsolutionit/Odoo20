# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
from odoo import http
from odoo.http import request


class TdbLanguageController(http.Controller):

    @http.route('/web/session/switch_language', type='jsonrpc', auth='public', readonly=False)
    def switch_language(self, lang):
        """
        Chuyển đổi ngôn ngữ hiển thị của người dùng (en_US <-> vi_VN)
        Cập nhật trực tiếp vào res.users, session context và cookie để áp dụng toàn bộ hệ thống Odoo.
        """
        valid_langs = ['vi_VN', 'en_US']
        if lang not in valid_langs:
            return {'status': 'error', 'message': f'Ngôn ngữ không được hỗ trợ: {lang}'}

        # 1. Đảm bảo ngôn ngữ mục tiêu đã được kích hoạt trong res.lang
        Lang = request.env['res.lang'].sudo()
        target_lang = Lang.search([('code', '=', lang)], limit=1)
        if target_lang and not target_lang.active:
            target_lang.active = True
        elif not target_lang:
            try:
                Lang._activate_lang(lang)
            except Exception:
                pass

        # 2. Cập nhật ngôn ngữ cho người dùng hiện tại
        if request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)
            if user.exists():
                user.write({'lang': lang})
                if user.partner_id:
                    user.partner_id.write({'lang': lang})

        # 3. Cập nhật session context và context hiện tại
        request.session['lang'] = lang
        if hasattr(request.session, 'context') and isinstance(request.session.context, dict):
            request.session.context['lang'] = lang

        # 4. Thiết lập cookie frontend_lang cho các trang website / portal
        if hasattr(request, 'future_response'):
            request.future_response.set_cookie('frontend_lang', lang, max_age=365 * 24 * 3600)

        return {'status': 'ok', 'lang': lang}

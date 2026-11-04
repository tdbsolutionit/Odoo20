# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
from odoo import http
from odoo.http import request


class TdbLanguageController(http.Controller):

    @http.route('/web/session/switch_language', type='jsonrpc', auth='public', readonly=False)
    def switch_language(self, lang):
        """
        Chuyển đổi ngôn ngữ hiển thị của người dùng (en_US <-> vi_VN) qua JSON-RPC.
        """
        return self._do_switch_language(lang)

    @http.route('/web/session/switch_language_http', type='http', auth='public', readonly=False)
    def switch_language_http(self, lang=None, redirect=None, **kw):
        """
        Chuyển đổi ngôn ngữ hiển thị qua HTTP GET/POST và chuyển hướng trang.
        """
        self._do_switch_language(lang or 'vi_VN')
        return request.redirect(redirect or '/odoo')

    def _do_switch_language(self, lang):
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
                try:
                    Lang.create({
                        'code': lang,
                        'name': 'Vietnamese / Tiếng Việt' if lang == 'vi_VN' else 'English (US)',
                        'active': True,
                    })
                except Exception:
                    pass

        # 2. Cập nhật ngôn ngữ cho người dùng hiện tại (nếu đã đăng nhập)
        uid = request.session.uid
        if uid:
            user = request.env['res.users'].sudo().browse(uid)
            if user.exists():
                user.write({'lang': lang})
                if user.partner_id:
                    user.partner_id.write({'lang': lang})

        # 3. Cập nhật session context và session lang
        request.session['lang'] = lang
        ctx = dict(request.session.context or {})
        ctx['lang'] = lang
        request.session.context = ctx

        # 4. Thiết lập cookie frontend_lang cho các trang website / portal
        if hasattr(request, 'future_response') and request.future_response:
            request.future_response.set_cookie('frontend_lang', lang, max_age=365 * 24 * 3600)

        # 5. Flush và commit vào CSDL
        try:
            request.env.cr.commit()
        except Exception:
            pass

        return {'status': 'ok', 'lang': lang}

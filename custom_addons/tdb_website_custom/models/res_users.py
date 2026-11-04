# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import logging
from odoo import models
from ..controllers.main import decrypt_tdb_password

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _login(self, credential, user_agent_env=None):
        """
        Tự động giải mã mật khẩu TDB_ENC: tại tầng ORM cốt lõi của Odoo.
        Bảo đảm hoạt động 100% trên mọi controller (Home, Website, OAuth, Signup...).
        """
        if credential and isinstance(credential, dict) and credential.get('type') == 'password':
            pwd = credential.get('password')
            if pwd and isinstance(pwd, str) and pwd.startswith('TDB_ENC:'):
                decrypted = decrypt_tdb_password(pwd)
                credential['password'] = decrypted
                _logger.info("[TDB SECURITY] Đã giải mã mật khẩu an toàn trong _login cho tài khoản: %s", credential.get('login'))
        return super()._login(credential, user_agent_env=user_agent_env)

    def _check_credentials(self, credential, env):
        """
        Tự động giải mã mật khẩu TDB_ENC: trước khi kiểm tra hash mật khẩu trong DB.
        """
        if credential and isinstance(credential, dict) and credential.get('type') == 'password':
            pwd = credential.get('password')
            if pwd and isinstance(pwd, str) and pwd.startswith('TDB_ENC:'):
                credential['password'] = decrypt_tdb_password(pwd)
                _logger.info("[TDB SECURITY] Đã giải mã mật khẩu an toàn trong _check_credentials cho tài khoản: %s", credential.get('login'))
        return super()._check_credentials(credential, env)

    def authenticate(self, credential, user_agent_env=None):
        """
        Tự động giải mã mật khẩu TDB_ENC: khi gọi authenticate trực tiếp.
        """
        if credential and isinstance(credential, dict) and credential.get('type') == 'password':
            pwd = credential.get('password')
            if pwd and isinstance(pwd, str) and pwd.startswith('TDB_ENC:'):
                credential['password'] = decrypt_tdb_password(pwd)
                _logger.info("[TDB SECURITY] Đã giải mã mật khẩu an toàn trong authenticate cho tài khoản: %s", credential.get('login'))
        return super().authenticate(credential, user_agent_env=user_agent_env)

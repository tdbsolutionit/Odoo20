# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(">>> [TDB PLM MIGRATION 20.0.1.3.0] Áp dụng phân quyền hiển thị Desktop Access Tokens cho Sếp...")

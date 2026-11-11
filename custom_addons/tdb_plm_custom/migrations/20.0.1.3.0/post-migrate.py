# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(">>> [TDB PLM MIGRATION 20.0.1.3.0] Xóa triệt để menu Desktop Access Tokens trên Top Bar...")
    try:
        cr.execute("""
            DELETE FROM ir_ui_menu_group_rel
            WHERE menu_id IN (
                SELECT id FROM ir_ui_menu
                WHERE (name::text ILIKE '%desktop%token%' OR name::text ILIKE '%quản lý thiết bị%')
                  AND parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu')
            );

            DELETE FROM ir_ui_menu
            WHERE (name::text ILIKE '%desktop%token%' OR name::text ILIKE '%quản lý thiết bị%')
              AND parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu');

            DELETE FROM ir_model_data
            WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top';
        """)
        _logger.info(">>> [TDB PLM MIGRATION 20.0.1.3.0] Đã xóa thành công menu Top Bar!")
    except Exception as e:
        _logger.warning(f">>> [TDB PLM MIGRATION 20.0.1.3.0] Bỏ qua lỗi xóa menu: {e}")

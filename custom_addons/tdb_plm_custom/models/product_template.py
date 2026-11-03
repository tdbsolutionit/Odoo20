# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model product.template cho phân hệ PLM.
Tuân thủ Layer 2: Quản lý schema dữ liệu và business logic cốt lõi.
"""
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """
    Kế thừa product.template để hỗ trợ phân hệ PLM và đồng bộ nhãn song ngữ.
    """
    _inherit = "product.template"

    # === Ghi chú & Logic nghiệp vụ ===
    # Các trường đặc thù PLM đã được khai báo qua plm_mixin / product_template của plm.
    # Model này sẵn sàng nhận mở rộng nghiệp vụ kỹ thuật tương lai mà không sửa core.


# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model product.product cho phân hệ Engineering Parts (PLM).
Tuân thủ Layer 2: Quản lý schema dữ liệu và business logic cốt lõi.
"""
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """
    Kế thừa product.product để quản lý thông tin linh kiện kỹ thuật (Engineering Parts).
    Chuẩn hóa nhãn chuỗi gốc tiếng Anh (Revision, CAD Raw Material, CAD Surface Finishing).
    """
    _inherit = "product.product"

    engineering_revision = fields.Integer(string="Revision")
    engineering_material = fields.Char(string="CAD Raw Material")
    engineering_surface = fields.Char(string="CAD Surface Finishing")

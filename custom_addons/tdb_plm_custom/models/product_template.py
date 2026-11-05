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
    Chuẩn hóa nhãn chuỗi gốc tiếng Anh (Revision, CAD Raw Material, CAD Surface Finishing).
    """
    _inherit = "product.template"

    engineering_revision = fields.Integer(string="Revision")
    engineering_material = fields.Char(string="CAD Raw Material")
    engineering_surface = fields.Char(string="CAD Surface Finishing")

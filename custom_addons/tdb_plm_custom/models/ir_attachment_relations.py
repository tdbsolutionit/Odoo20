# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Mở rộng model ir.attachment.relation cho OdooPLM:
1. Ràng buộc toàn vẹn dữ liệu: Ngăn chặn tự tham chiếu chính mình (parent_id != child_id).
2. Bổ sung các trường related hiển thị trạng thái khóa, người giữ Key, mã kỹ thuật.
3. Cung cấp navigation method mở nhanh tài liệu con hoặc Assembly cha từ dòng quan hệ.
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PlmDocumentRelations(models.Model):
    _inherit = "ir.attachment.relation"

    # =========================================================================
    # 1. TRƯỜNG THÔNG TIN LIÊN KẾT BỔ SUNG CHO TÀI LIỆU CON
    # =========================================================================
    child_engineering_code = fields.Char(
        related="child_id.engineering_code",
        string="Mã kỹ thuật con",
        store=False,
        readonly=True
    )
    child_lock_state = fields.Selection(
        related="child_id.lock_state",
        string="Trạng thái khóa con",
        store=False,
        readonly=True
    )
    child_key_holder_id = fields.Many2one(
        related="child_id.key_holder_id",
        string="Người giữ Key con",
        store=False,
        readonly=True
    )

    # =========================================================================
    # 2. TRƯỜNG THÔNG TIN LIÊN KẾT BỔ SUNG CHO TÀI LIỆU CHA (WHERE USED)
    # =========================================================================
    parent_engineering_code = fields.Char(
        related="parent_id.engineering_code",
        string="Mã kỹ thuật cha",
        store=False,
        readonly=True
    )
    parent_lock_state = fields.Selection(
        related="parent_id.lock_state",
        string="Trạng thái khóa cha",
        store=False,
        readonly=True
    )
    parent_key_holder_id = fields.Many2one(
        related="parent_id.key_holder_id",
        string="Người giữ Key cha",
        store=False,
        readonly=True
    )

    # =========================================================================
    # 3. CHUẨN HÓA HIỂN THỊ CẤU HÌNH CAD (LOẠI BỎ DẤU GẠCH MẶC ĐỊNH '-')
    # =========================================================================
    cad_configuration = fields.Char(
        string="Cấu hình CAD",
        compute="_compute_cad_configuration",
        inverse="_inverse_cad_configuration",
        store=False,
        help="Cấu hình CAD sạch sẽ, không hiển thị dấu gạch ngang mặc định từ SolidWorks"
    )

    @api.depends("configuration")
    def _compute_cad_configuration(self):
        """Nếu cấu hình CAD là dấu gạch ngang '-' hoặc rỗng từ CAD Add-in thì để trống."""
        for rec in self:
            cfg = rec.configuration
            if not cfg or str(cfg).strip() in ("-", "None", "false", "False", ""):
                rec.cad_configuration = False
            else:
                rec.cad_configuration = str(cfg).strip()

    def _inverse_cad_configuration(self):
        """Ghi ngược lại trường configuration gốc để đồng bộ với CAD client."""
        for rec in self:
            rec.configuration = rec.cad_configuration or "-"

    # =========================================================================
    # 3. RÀNG BUỘC TOÀN VẸN DỮ LIỆU
    # =========================================================================
    @api.constrains('parent_id', 'child_id')
    def _check_parent_child_different(self):
        """Đảm bảo tài liệu không thể tự tham chiếu chính mình."""
        for rel in self:
            if rel.parent_id and rel.child_id and rel.parent_id.id == rel.child_id.id:
                raise ValidationError(_(
                    "Tài liệu không thể tự tham chiếu chính mình làm file con! "
                    "(Tài liệu: %s)"
                ) % (rel.parent_id.name or rel.parent_id.engineering_code or rel.parent_id.id))

    # =========================================================================
    # 4. ACTION HELPERS ĐIỀU HƯỚNG NHANH TỪ BẢNG QUAN HỆ
    # =========================================================================
    def action_open_child_document(self):
        """Mở chi tiết Form view của tài liệu con."""
        self.ensure_one()
        if not self.child_id:
            return False
        return {
            'name': self.child_id.name or self.child_id.engineering_code or _("Tài liệu con"),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': self.child_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_parent_document(self):
        """Mở chi tiết Form view của Assembly cha."""
        self.ensure_one()
        if not self.parent_id:
            return False
        return {
            'name': self.parent_id.name or self.parent_id.engineering_code or _("Assembly cha"),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': self.parent_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


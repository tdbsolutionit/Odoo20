# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.osv import expression


class DmsDirectory(models.Model):
    _inherit = "dms.directory"

    is_recycle_bin = fields.Boolean(
        string="Là Thùng Rác (Recycle Bin)",
        default=False,
        index=True,
        help="Thư mục đặc biệt lưu trữ các tệp tin đã bị xóa, chỉ dành cho Sếp/Admin quản lý và khôi phục.",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "is_root_directory" in fields_list and "is_root_directory" not in res and not res.get("parent_id"):
            res["is_root_directory"] = True
        if "storage_id" in fields_list and not res.get("storage_id"):
            storage = self.env["dms.storage"].sudo().search([], limit=1)
            if not storage:
                storage = self.env["dms.storage"].sudo().create({
                    "name": "Documents Storage",
                    "save_type": "database",
                })
            res["storage_id"] = storage.id
        return res

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        """Ẩn hoàn toàn thư mục Thùng Rác đối với người dùng không phải Quản trị viên/Sếp."""
        if not self.env.su:
            user = self.env.user
            is_admin = user._is_superuser() or user.has_group("base.group_system")
            if not is_admin:
                domain = expression.AND([domain, [("is_recycle_bin", "=", False)]])
        return super()._search(domain, offset=offset, limit=limit, order=order, **kwargs)

    def write(self, vals):
        if not self.env.su:
            user = self.env.user
            is_admin = user._is_superuser() or user.has_group("base.group_system")
            if "is_recycle_bin" in vals and not is_admin:
                raise AccessError(_("Chỉ Quản trị viên (Sếp/Admin) mới có quyền cấu hình Thùng Rác!"))
            for record in self:
                if record.is_recycle_bin and not is_admin:
                    raise AccessError(_("Chỉ Quản trị viên (Sếp/Admin) mới có quyền chỉnh sửa Thùng Rác!"))
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            user = self.env.user
            is_admin = user._is_superuser() or user.has_group("base.group_system")
            for record in self:
                if record.is_recycle_bin and not is_admin:
                    raise AccessError(_("Không thể xóa thư mục Thùng Rác của hệ thống!"))
        return super().unlink()

    def action_open_create_subfolder_wizard(self):
        """Mở wizard tạo thư mục con bên trong thư mục / phòng ban hiện tại."""
        self.ensure_one()
        return {
            "name": _("Tạo thư mục con trong %s") % self.name,
            "type": "ir.actions.act_window",
            "res_model": "dms.create.subfolder.wizard",
            "views": [[False, "form"]],
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_parent_id": self.id,
                "default_default_allow_download": self.default_allow_download,
            },
        }

    @api.model
    def get_recycle_bin(self):
        """Lấy bản ghi Thùng Rác duy nhất của hệ thống, tự động tạo nếu chưa có."""
        recycle = self.sudo().search([("is_recycle_bin", "=", True)], limit=1)
        if not recycle:
            storage = self.env["dms.storage"].sudo().search([], limit=1)
            if not storage:
                storage = self.env["dms.storage"].sudo().create({
                    "name": "Documents Storage",
                    "save_type": "database",
                })
            recycle = self.sudo().create({
                "name": "00. Thùng Rác (Recycle Bin)",
                "is_root_directory": True,
                "is_recycle_bin": True,
                "default_allow_download": False,
                "storage_id": storage.id,
            })
        elif not recycle.storage_id:
            storage = self.env["dms.storage"].sudo().search([], limit=1)
            if not storage:
                storage = self.env["dms.storage"].sudo().create({
                    "name": "Documents Storage",
                    "save_type": "database",
                })
            recycle.sudo().write({"storage_id": storage.id})
        return recycle

    @api.model
    def _init_recycle_bin(self):
        """Khởi tạo phòng ban Thùng Rác nếu chưa tồn tại."""
        self.get_recycle_bin()

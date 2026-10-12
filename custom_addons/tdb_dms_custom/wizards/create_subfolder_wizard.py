# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class DmsCreateSubfolderWizard(models.TransientModel):
    _name = "dms.create.subfolder.wizard"
    _description = "Wizard tạo thư mục con trong phòng ban"

    name = fields.Char(string="Tên thư mục mới", required=True)
    parent_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Phòng ban / Thư mục cha",
        required=True,
        domain="[('is_recycle_bin', '=', False)]",
    )
    can_manage_download_setting = fields.Boolean(
        string="Có quyền cấu hình tải về",
        compute="_compute_can_manage_download_setting",
    )
    default_allow_download = fields.Boolean(
        string="Mặc định cho phép tải về",
        default=True,
        help="Nếu bật: mọi tệp tin tải lên thư mục này sẽ mặc định cho phép tải về máy. Nếu tắt: tệp tin tải lên sẽ bị khóa tải về (chỉ xem trước).",
    )

    @api.depends("parent_id")
    def _compute_can_manage_download_setting(self):
        user = self.env.user
        is_admin = user._is_superuser() or user.has_group("base.group_system")
        for record in self:
            if is_admin:
                record.can_manage_download_setting = True
            elif record.parent_id:
                record.can_manage_download_setting = bool(record.parent_id._is_user_leader(user))
            else:
                record.can_manage_download_setting = False

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        if self.parent_id:
            self.default_allow_download = self.parent_id.default_allow_download

    def action_create_subfolder(self):
        self.ensure_one()
        parent = self.parent_id
        user = self.env.user
        is_admin = user._is_superuser() or user.has_group("base.group_system")

        if not is_admin and not parent.permission_create:
            raise AccessError(_("Bạn không có quyền tạo thư mục con trong phòng ban '%s'!") % parent.name)

        # Nếu không có quyền quản lý cấu hình tải về thì kế thừa nguyên vẹn từ thư mục cha
        allow_dl = self.default_allow_download if self.can_manage_download_setting else parent.default_allow_download

        new_dir = self.env["dms.directory"].create({
            "name": self.name.strip(),
            "parent_id": parent.id,
            "storage_id": parent.storage_id.id,
            "default_allow_download": allow_dl,
            "is_root_directory": False,
        })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Tạo thư mục thành công"),
                "message": _("Đã tạo thư mục '%s' trong '%s'.") % (new_dir.name, parent.name),
                "type": "success",
                "sticky": False,
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }


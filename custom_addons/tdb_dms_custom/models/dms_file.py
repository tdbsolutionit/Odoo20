# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.osv import expression


class DmsFile(models.Model):
    _inherit = "dms.file"

    is_deleted = fields.Boolean(
        string="Đã chuyển vào Thùng Rác",
        default=False,
        index=True,
        tracking=True,
    )
    uploader_name = fields.Char(
        string="Tên người đăng tải",
        related="create_uid.name",
        store=True,
        readonly=True,
    )
    deleted_uid = fields.Many2one(
        comodel_name="res.users",
        string="Người đã xóa",
        readonly=True,
        tracking=True,
        index=True,
    )
    deleted_user_name = fields.Char(
        string="Tên người xóa",
        related="deleted_uid.name",
        store=True,
        readonly=True,
    )
    deleted_date = fields.Datetime(
        string="Thời gian xóa",
        readonly=True,
        tracking=True,
    )
    original_directory_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Thư mục ban đầu",
        readonly=True,
        index=True,
    )
    is_in_recycle_bin = fields.Boolean(
        string="Nằm trong Thùng Rác",
        compute="_compute_is_in_recycle_bin",
        store=True,
        index=True,
    )

    @api.depends("directory_id", "directory_id.is_recycle_bin", "is_deleted")
    def _compute_is_in_recycle_bin(self):
        for record in self:
            record.is_in_recycle_bin = bool(
                record.is_deleted or (record.directory_id and record.directory_id.is_recycle_bin)
            )

    def _update_content_vals(self, vals, binary):
        new_vals = vals.copy()
        new_vals.update(
            {
                "checksum": self._get_checksum(binary),
                "size": binary and len(binary) or 0,
            }
        )
        if self.storage_id.save_type in ["file", "attachment"]:
            new_vals["content_file"] = self.content
        else:
            if not binary:
                new_vals["content_binary"] = False
            elif isinstance(self.content, str) and self.content:
                new_vals["content_binary"] = self.content
            else:
                import base64
                new_vals["content_binary"] = base64.b64encode(binary).decode("ascii")
        return new_vals

    @api.depends("content_binary", "content_file", "attachment_id")
    def _compute_content(self):
        bin_size = self.env.context.get("bin_size", False)
        for record in self:
            if record.content_file:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(**context).content_file
            elif record.content_binary:
                record.content = record.content_binary
            elif record.attachment_id:
                context = {"human_size": True} if bin_size else {"base64": True}
                record.content = record.with_context(**context).attachment_id.datas

    @api.model
    def _get_binary_max_size(self):
        icp = self.env["ir.config_parameter"].sudo()
        if hasattr(icp, "get_int"):
            return icp.get_int("dms.binary_max_size", default=500)
        getter = getattr(icp, "get_str", getattr(icp, "get_param", lambda k, default: 500))
        return int(getter("dms.binary_max_size", default=500))

    def action_preview_file(self):
        self.ensure_one()
        try:
            action = self.env["ir.actions.actions"]._for_xml_id("dms.action_dms_file")
        except Exception:
            action = {
                "name": _("Files"),
                "type": "ir.actions.act_window",
                "res_model": "dms.file",
            }
        view_id = self.env.ref("dms.view_dms_file_preview_modal", raise_if_not_found=False)
        action["name"] = _("Xem trước: %s") % self.name
        action["views"] = [(view_id.id if view_id else False, "form")]
        action["res_id"] = self.id
        action["target"] = "new"
        action["context"] = {"dialog_size": "extra-large"}
        return action

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        """Người dùng thông thường không bao giờ nhìn thấy các file trong Thùng Rác hoặc đã bị xóa."""
        if not self.env.su:
            user = self.env.user
            is_admin = user._is_superuser() or user.has_group("base.group_system")
            if not is_admin:
                domain = expression.AND([
                    domain,
                    [("is_deleted", "=", False), ("directory_id.is_recycle_bin", "!=", True)]
                ])
        return super()._search(domain, offset=offset, limit=limit, order=order, **kwargs)

    def unlink(self):
        """Cơ chế Thùng Rác (Soft Delete):
        - Khi xóa file ở bất kỳ phòng ban nào, file được chuyển vào Thùng Rác, lưu người xóa và thời gian xóa.
        - Chỉ khi file đã nằm trong Thùng Rác và do Sếp/Admin xóa thì mới xóa vĩnh viễn khỏi CSDL.
        """
        user = self.env.user
        is_admin = self.env.su or user._is_superuser() or user.has_group("base.group_system")

        recycle_bin_dir = self.env["dms.directory"].get_recycle_bin()

        files_to_hard_delete = self.env["dms.file"]
        for record in self:
            # Nếu file đã nằm trong Thùng rác
            if record.directory_id.id == recycle_bin_dir.id or record.is_deleted:
                if is_admin:
                    files_to_hard_delete |= record
                else:
                    raise AccessError(_("Chỉ Quản trị viên (Sếp/Admin) mới có quyền xóa vĩnh viễn tệp tin trong Thùng Rác!"))
            else:
                # Kiểm tra quyền xóa thông thường trên file
                record.check_access("unlink")
                # Chuyển vào Thùng Rác (Soft Delete)
                record.sudo().write({
                    "original_directory_id": record.directory_id.id,
                    "deleted_uid": user.id,
                    "deleted_date": fields.Datetime.now(),
                    "is_deleted": True,
                    "directory_id": recycle_bin_dir.id,
                })
                record.sudo().message_post(
                    body=_("Tệp tin đã được chuyển vào Thùng Rác bởi người dùng <b>%s</b>.") % user.name,
                    subtype_xmlid="mail.mt_note",
                )

        if files_to_hard_delete:
            return super(DmsFile, files_to_hard_delete).unlink()
        return True

    def action_restore_file(self):
        """Khôi phục tệp tin từ Thùng Rác về lại thư mục ban đầu."""
        user = self.env.user
        is_admin = self.env.su or user._is_superuser() or user.has_group("base.group_system")
        if not is_admin:
            raise AccessError(_("Chỉ Quản trị viên (Sếp/Admin) mới có quyền khôi phục tệp tin từ Thùng Rác!"))

        restored_count = 0
        for record in self:
            target_dir = record.original_directory_id
            if not target_dir or not target_dir.exists():
                target_dir = self.env["dms.directory"].sudo().search(
                    [("is_sharing", "=", True)], limit=1
                )
                if not target_dir:
                    target_dir = self.env["dms.directory"].sudo().search(
                        [("is_root_directory", "=", True), ("is_recycle_bin", "=", False)], limit=1
                    )

            if target_dir:
                record.sudo().write({
                    "directory_id": target_dir.id,
                    "is_deleted": False,
                    "deleted_uid": False,
                    "deleted_date": False,
                })
                record.sudo().message_post(
                    body=_("Tệp tin đã được khôi phục về thư mục <b>%s</b> bởi <b>%s</b>.") % (target_dir.name, user.name),
                    subtype_xmlid="mail.mt_note",
                )
                restored_count += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Khôi phục thành công"),
                "message": _("Đã khôi phục %s tệp tin về thư mục ban đầu.") % restored_count,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def action_permanent_delete(self):
        """Xóa vĩnh viễn tệp tin khỏi CSDL dành cho Sếp/Admin."""
        user = self.env.user
        is_admin = self.env.su or user._is_superuser() or user.has_group("base.group_system")
        if not is_admin:
            raise AccessError(_("Chỉ Quản trị viên (Sếp/Admin) mới có quyền xóa vĩnh viễn!"))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("directory_id") and "is_downloadable" not in vals:
                directory = self.env["dms.directory"].browse(vals["directory_id"])
                if directory.exists():
                    vals["is_downloadable"] = directory.default_allow_download
        return super().create(vals_list)


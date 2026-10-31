# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
import pytz
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DmsFileDateFilterWizard(models.TransientModel):
    _name = "dms.file.date.filter.wizard"
    _description = "Bộ lọc tệp tin theo khoảng thời gian"

    filter_target = fields.Selection(
        selection=[
            ("create_date", "Thời gian đăng tải"),
            ("deleted_date", "Thời gian xóa"),
        ],
        string="Lọc theo",
        required=True,
        default="create_date",
        help="Chọn trường thời gian bạn muốn lọc (thời điểm tải file lên hoặc thời điểm file bị xóa).",
    )
    quick_range = fields.Selection(
        selection=[
            ("custom", "Tự chọn khoảng ngày"),
            ("today", "Hôm nay"),
            ("yesterday", "Hôm qua"),
            ("7_days", "7 ngày gần đây"),
            ("30_days", "30 ngày gần đây"),
            ("this_month", "Tháng này"),
            ("last_month", "Tháng trước"),
            ("this_year", "Năm nay"),
        ],
        string="Chọn nhanh mốc thời gian",
        default="custom",
    )
    date_from = fields.Date(
        string="Từ ngày",
        help="Ngày bắt đầu (định dạng Ngày/Tháng/Năm).",
    )
    date_to = fields.Date(
        string="Đến ngày",
        help="Ngày kết thúc (định dạng Ngày/Tháng/Năm).",
    )
    directory_id = fields.Many2one(
        comodel_name="dms.directory",
        string="Trong thư mục / phòng ban",
        help="Để trống nếu muốn tìm kiếm trong toàn bộ hệ thống.",
    )
    include_subdirectories = fields.Boolean(
        string="Bao gồm cả thư mục con",
        default=True,
    )

    @api.onchange("quick_range")
    def _onchange_quick_range(self):
        if not self.quick_range or self.quick_range == "custom":
            return

        today = fields.Date.context_today(self)
        if self.quick_range == "today":
            self.date_from = today
            self.date_to = today
        elif self.quick_range == "yesterday":
            yest = today - timedelta(days=1)
            self.date_from = yest
            self.date_to = yest
        elif self.quick_range == "7_days":
            self.date_from = today - timedelta(days=7)
            self.date_to = today
        elif self.quick_range == "30_days":
            self.date_from = today - timedelta(days=30)
            self.date_to = today
        elif self.quick_range == "this_month":
            self.date_from = today.replace(day=1)
            # Ngày cuối cùng của tháng này
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            self.date_to = next_month - timedelta(days=1)
        elif self.quick_range == "last_month":
            first_this_month = today.replace(day=1)
            last_prev_month = first_this_month - timedelta(days=1)
            self.date_from = last_prev_month.replace(day=1)
            self.date_to = last_prev_month
        elif self.quick_range == "this_year":
            self.date_from = today.replace(month=1, day=1)
            self.date_to = today.replace(month=12, day=31)

    def _to_utc_str(self, date_val, is_end_of_day=False):
        """Chuyển đổi Date theo múi giờ người dùng sang UTC string cho Datetime query."""
        if not date_val:
            return False
        user_tz_name = self.env.user.tz or "UTC"
        try:
            user_tz = pytz.timezone(user_tz_name)
        except Exception:
            user_tz = pytz.UTC
        t = time.max.replace(microsecond=0) if is_end_of_day else time.min
        dt = datetime.combine(date_val, t)
        dt_localized = user_tz.localize(dt)
        dt_utc = dt_localized.astimezone(pytz.UTC)
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S")

    def action_apply_filter(self):
        self.ensure_one()
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise UserError(_("'Từ ngày' (%s) không thể lớn hơn 'Đến ngày' (%s)! Vui lòng kiểm tra lại.") % (
                self.date_from.strftime("%d/%m/%Y"),
                self.date_to.strftime("%d/%m/%Y"),
            ))

        if not self.date_from and not self.date_to and not self.directory_id:
            raise UserError(_("Vui lòng nhập 'Từ ngày' hoặc 'Đến ngày' để thực hiện lọc!"))

        domain = [("is_hidden", "=", False)]

        # Phân biệt tệp đã xóa và tệp đang hoạt động
        if self.filter_target == "deleted_date":
            domain.append(("is_deleted", "=", True))
        else:
            domain.append(("is_deleted", "=", False))

        # Phạm vi thư mục
        if self.directory_id:
            if self.include_subdirectories:
                domain.append(("directory_id", "child_of", self.directory_id.id))
            else:
                domain.append(("directory_id", "=", self.directory_id.id))

        # Khoảng thời gian
        if self.date_from:
            dt_from_utc = self._to_utc_str(self.date_from, is_end_of_day=False)
            domain.append((self.filter_target, ">=", dt_from_utc))
        if self.date_to:
            dt_to_utc = self._to_utc_str(self.date_to, is_end_of_day=True)
            domain.append((self.filter_target, "<=", dt_to_utc))

        target_label = "Đăng tải" if self.filter_target == "create_date" else "Đã xóa"
        date_label_parts = []
        if self.date_from and self.date_to:
            if self.date_from == self.date_to:
                date_label_parts.append(_("Ngày %s") % self.date_from.strftime("%d/%m/%Y"))
            else:
                date_label_parts.append("%s - %s" % (
                    self.date_from.strftime("%d/%m/%Y"),
                    self.date_to.strftime("%d/%m/%Y"),
                ))
        elif self.date_from:
            date_label_parts.append(_("Từ %s") % self.date_from.strftime("%d/%m/%Y"))
        elif self.date_to:
            date_label_parts.append(_("Đến %s") % self.date_to.strftime("%d/%m/%Y"))

        dir_label = " [%s]" % self.directory_id.name if self.directory_id else ""
        date_str = (" (" + ", ".join(date_label_parts) + ")") if date_label_parts else ""
        title = _("Tệp tin: %s%s%s") % (target_label, date_str, dir_label)

        return {
            "name": title,
            "type": "ir.actions.act_window",
            "res_model": "dms.file",
            "view_mode": "kanban,list,form",
            "views": [
                [False, "kanban"],
                [False, "list"],
                [False, "form"],
            ],
            "domain": domain,
            "target": "current",
            "context": dict(
                self.env.context,
                default_directory_id=self.directory_id.id if self.directory_id else False,
            ),
        }

    def action_clear_filter(self):
        """Xóa toàn bộ bộ lọc ngày tháng và quay về danh sách tệp đầy đủ ban đầu."""
        return {
            "name": _("Files"),
            "type": "ir.actions.act_window",
            "res_model": "dms.file",
            "view_mode": "kanban,list,form",
            "views": [
                [False, "kanban"],
                [False, "list"],
                [False, "form"],
            ],
            "domain": [("is_hidden", "=", False)],
            "target": "current",
            "context": dict(self.env.context),
        }

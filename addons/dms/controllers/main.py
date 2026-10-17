import base64
import csv
import html
import json
import logging
import mimetypes
import os
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from io import BytesIO

from werkzeug.exceptions import Forbidden
from werkzeug.utils import send_file

from odoo import _, http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import Response, request

from odoo.addons.web.controllers.binary import clean

try:
    from odoo.http.stream import content_disposition
except ImportError:
    try:
        from odoo.http import content_disposition
    except ImportError:
        import urllib.parse
        def content_disposition(filename, disposition_type="attachment"):
            return f"{disposition_type}; filename*=UTF-8''{urllib.parse.quote(filename, safe='')}"

_logger = logging.getLogger(__name__)


class OnboardingController(http.Controller):
    @http.route("/config/dms.forbidden_extensions", type="jsonrpc", auth="user")
    def forbidden_extensions(self, **_kwargs):
        params = request.env["ir.config_parameter"].sudo()
        getter = getattr(
            params, "get_str", getattr(params, "get_param", lambda k, default="": "")
        )
        return {
            "forbidden_extensions": getter("dms.forbidden_extensions", default="")
        }

    def _check_upload_permission(self, directory_id):
        """Check if current user is allowed to upload files into directory_id."""
        user = request.env.user
        if (
            request.env.su
            or request.env.is_superuser()
            or user._is_superuser()
            or user._is_admin()
            or user.has_group("base.group_system")
            or user.has_group("dms.group_dms_manager")
        ):
            return True
        directory = request.env["dms.directory"].browse(directory_id)
        if not directory.exists():
            return False
        if hasattr(directory, "_is_user_leader") and directory._is_user_leader(user):
            return True
        if directory.permission_create:
            return True
        # Check if user has perm_inclusive_create in access groups for this directory
        cr = request.env.cr
        cr.execute(
            """
            SELECT 1
            FROM dms_directory_complete_groups_rel AS dir_group_rel
            INNER JOIN dms_access_group AS dag ON dir_group_rel.gid = dag.id
            INNER JOIN dms_access_group_users_rel AS users ON users.gid = dag.id
            WHERE users.uid = %s AND dag.perm_inclusive_create = True AND dir_group_rel.aid = %s
            LIMIT 1
            """,
            (request.env.uid, directory.id),
        )
        return bool(cr.fetchone())

    @http.route("/web/binary/upload_dms_file", type="http", auth="user")
    def upload_dms_file(self, ufile, directory_id, callback=None):
        """Similar to the web upload_attachment() method, but customized to
        directly create dms.file records.
        """
        try:
            directory_id = int(directory_id)
        except (ValueError, TypeError):
            return request.make_response(
                json.dumps([{"error": str(_("Thư mục không hợp lệ."))}]),
                headers=[("Content-Type", "application/json; charset=utf-8")],
            )

        # Permission check: verify if the user has create/push access on this directory
        if not self._check_upload_permission(directory_id):
            return request.make_response(
                json.dumps(
                    [{"error": str(_("Bạn không có đủ quyền hạn để tải tài liệu lên thư mục này."))}]
                ),
                headers=[("Content-Type", "application/json; charset=utf-8")],
            )

        files = request.httprequest.files.getlist("ufile")
        Model = request.env["dms.file"]
        out = """<script language="javascript" type="text/javascript">
                    var win = window.top.window;
                    win.jQuery(win).trigger(%s, %s);
                </script>"""
        args = []
        for ufile in files:
            filename = ufile.filename
            if request.httprequest.user_agent.browser == "safari":
                filename = unicodedata.normalize("NFD", ufile.filename)
            try:
                content_base64 = base64.b64encode(ufile.read()).decode("ascii")
                dms_file = Model.create(
                    {
                        "directory_id": directory_id,
                        "name": filename,
                        "content": content_base64,
                    }
                )
            except AccessError:
                args.append(
                    {"error": str(_("Bạn không có đủ quyền hạn để tải tài liệu lên thư mục này."))}
                )
            except ValidationError as e:
                args.append({"error": str(e.args[0] if e.args else e)})
            except Exception as e:
                _logger.exception("Fail to upload dms file %s", filename)
                args.append({"error": str(e)})
            else:
                args.append(
                    {
                        "filename": clean(filename),
                        "mimetype": dms_file.mimetype,
                        "id": dms_file.id,
                        "size": dms_file.size,
                    }
                )
        if callback:
            return out % (json.dumps(clean(callback)), json.dumps(args))
        return request.make_response(
            json.dumps(args),
            headers=[("Content-Type", "application/json; charset=utf-8")],
        )

    def _render_preview_error_response(self, dms_file):
        ext = (dms_file.extension or "").lower()
        is_office = ext in ["pptx", "ppt", "docx", "doc", "odt", "odp", "rtf"]
        hint = (
            "<p>Đối với định dạng Office (.pptx, .docx), máy chủ cần được cài đặt <b>LibreOffice</b> để tự động chuyển đổi slide sang PDF xem trước.</p>"
            if is_office
            else "<p>Tệp có thể bị hỏng, có mật khẩu bảo vệ hoặc không đúng cấu trúc chuẩn.</p>"
        )
        download_btn = (
            f'<a href="/dms/file/{dms_file.id}/download">Tải tệp về máy</a>'
            if dms_file.can_download
            else '<p style="color:#dc3545;font-weight:500;margin-top:15px;"><i class="fa fa-lock"></i> Tệp này hiện đang bị khóa tải về.</p>'
        )
        html_error = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:90vh;margin:0;background:#f8f9fa;color:#495057;text-align:center;}}.box{{padding:30px;background:#fff;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.08);max-width:520px;}}a{{display:inline-block;margin-top:15px;padding:10px 20px;background:#017e84;color:#fff;text-decoration:none;border-radius:4px;}}</style></head>
<body>
<div class="box">
    <h3>Không thể tạo bản xem trước cho tài liệu này</h3>
    {hint}
    {download_btn}
</div>
</body>
</html>"""
        return Response(
            html_error,
            content_type="text/html; charset=utf-8",
            headers=[
                (
                    "Content-Disposition",
                    content_disposition(
                        f"{clean(dms_file.name)}.html", disposition_type="inline"
                    ),
                ),
            ],
        )

    def _render_excel_spreadsheet_html(self, dms_file):
        """Render interactive Microsoft Excel style spreadsheet viewer HTML."""
        raw_content = dms_file._get_raw_content()
        if not raw_content:
            return None

        ext = (dms_file.extension or "").lower()
        sheets_data = []

        try:
            if ext in ("xlsx", "xlsm", "xltx", "xlt"):
                import openpyxl

                wb = openpyxl.load_workbook(BytesIO(raw_content), data_only=True)
                for sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    rows_data = []
                    max_cols = 0
                    for row in ws.iter_rows(values_only=True):
                        row_vals = []
                        for cell in row:
                            if cell is None:
                                row_vals.append("")
                            elif isinstance(cell, float) and cell.is_integer():
                                row_vals.append(f"{int(cell):,}")
                            elif isinstance(cell, (int, float)):
                                row_vals.append(f"{cell:,}")
                            elif hasattr(cell, "strftime"):
                                row_vals.append(
                                    cell.strftime(
                                        "%d/%m/%Y %H:%M"
                                        if hasattr(cell, "hour") and cell.hour
                                        else "%d/%m/%Y"
                                    )
                                )
                            else:
                                row_vals.append(str(cell))
                        while row_vals and row_vals[-1] == "":
                            row_vals.pop()
                        if row_vals:
                            max_cols = max(max_cols, len(row_vals))
                        rows_data.append(row_vals)
                    while rows_data and not any(rows_data[-1]):
                        rows_data.pop()
                    if rows_data:
                        sheets_data.append(
                            {
                                "name": sheet_name,
                                "rows": rows_data[:1500],
                                "total_rows": len(rows_data),
                                "cols": max_cols,
                            }
                        )
            elif ext == "xls":
                import xlrd

                wb = xlrd.open_workbook(file_contents=raw_content)
                for sheet_idx in range(wb.nsheets):
                    sheet = wb.sheet_by_index(sheet_idx)
                    rows_data = []
                    max_cols = 0
                    for r_idx in range(sheet.nrows):
                        row_vals = []
                        for c_idx in range(sheet.ncols):
                            val = sheet.cell_value(r_idx, c_idx)
                            if val == "" or val is None:
                                row_vals.append("")
                            elif isinstance(val, float) and val.is_integer():
                                row_vals.append(f"{int(val):,}")
                            elif isinstance(val, (int, float)):
                                row_vals.append(f"{val:,}")
                            else:
                                row_vals.append(str(val))
                        while row_vals and row_vals[-1] == "":
                            row_vals.pop()
                        if row_vals:
                            max_cols = max(max_cols, len(row_vals))
                        rows_data.append(row_vals)
                    while rows_data and not any(rows_data[-1]):
                        rows_data.pop()
                    if rows_data:
                        sheets_data.append(
                            {
                                "name": sheet.name,
                                "rows": rows_data[:1500],
                                "total_rows": len(rows_data),
                                "cols": max_cols,
                            }
                        )
            elif ext in ("csv", "tsv", "ods"):
                text_content = ""
                for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
                    try:
                        text_content = raw_content.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                if text_content:
                    lines = text_content.splitlines()
                    first_line = lines[0] if lines else ""
                    delimiter = (
                        "\t"
                        if ext == "tsv" or "\t" in first_line
                        else (
                            ";"
                            if first_line.count(";") > first_line.count(",")
                            else ","
                        )
                    )
                    reader = csv.reader(lines, delimiter=delimiter)
                    rows_data = []
                    max_cols = 0
                    for row in reader:
                        row_vals = [str(c).strip() for c in row]
                        while row_vals and row_vals[-1] == "":
                            row_vals.pop()
                        if row_vals:
                            max_cols = max(max_cols, len(row_vals))
                        rows_data.append(row_vals)
                    while rows_data and not any(rows_data[-1]):
                        rows_data.pop()
                    if rows_data:
                        sheets_data.append(
                            {
                                "name": "Dữ liệu",
                                "rows": rows_data[:1500],
                                "total_rows": len(rows_data),
                                "cols": max_cols,
                            }
                        )
        except Exception as e:
            _logger.exception(
                "Error parsing spreadsheet for file %s: %s", dms_file.name, e
            )
            return None

        if not sheets_data:
            return None

        def col_letter(col_idx):
            res = []
            n = col_idx + 1
            while n > 0:
                n, rem = divmod(n - 1, 26)
                res.append(chr(65 + rem))
            return "".join(reversed(res))

        sheets_html = []
        tabs_html = []
        for s_idx, s in enumerate(sheets_data):
            is_active = s_idx == 0
            active_cls = "active" if is_active else ""
            sheet_name_esc = html.escape(s["name"])

            tabs_html.append(
                f'<button class="sheet-tab {active_cls}" onclick="switchSheet({s_idx})" title="{sheet_name_esc}">'
                f'{sheet_name_esc}'
                f'</button>'
            )

            cols_count = max(s["cols"], 12)
            rows_data = s["rows"]
            rows_count = max(len(rows_data), 35)

            table_rows = []
            header_th = ['<th class="corner-cell"></th>']
            for c_idx in range(cols_count):
                header_th.append(
                    f'<th class="col-header" data-col="{c_idx}">{col_letter(c_idx)}</th>'
                )
            table_rows.append('<thead><tr>' + "".join(header_th) + "</tr></thead><tbody>")

            for r_idx in range(rows_count):
                row_vals = rows_data[r_idx] if r_idx < len(rows_data) else []
                row_cells = [f'<th class="row-header" data-row="{r_idx}">{r_idx + 1}</th>']
                for c_idx in range(cols_count):
                    val = row_vals[c_idx] if c_idx < len(row_vals) else ""
                    val_str = str(val)
                    val_esc = html.escape(val_str)
                    coord = f"{col_letter(c_idx)}{r_idx + 1}"
                    is_num = (
                        val_str
                        and val_str.replace(",", "")
                        .replace(".", "")
                        .replace("-", "")
                        .isdigit()
                    )
                    num_cls = " num" if is_num else ""
                    row_cells.append(
                        f'<td class="cell{num_cls}" data-row="{r_idx}" data-col="{c_idx}" '
                        f'data-coord="{coord}" data-val="{val_esc}" title="{val_esc}">'
                        f'{val_esc}</td>'
                    )
                table_rows.append("<tr>" + "".join(row_cells) + "</tr>")

            table_rows.append("</tbody>")
            table_html = f'<table class="excel-table">{"".join(table_rows)}</table>'

            sheets_html.append(
                f'<div class="sheet-pane {active_cls}" data-sheet-index="{s_idx}" data-rows="{s["total_rows"]}" data-cols="{s["cols"]}">'
                f'{table_html}'
                f'</div>'
            )

        filename_esc = html.escape(dms_file.name or f"file_{dms_file.id}")
        file_size_str = dms_file.human_size or ""
        total_sheets = len(sheets_data)
        sheet_badge = f"{total_sheets} sheet" if total_sheets == 1 else f"{total_sheets} sheets"
        first_sheet = sheets_data[0]

        template = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__DOC_TITLE__ - Bảng tính Excel</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #f3f4f6;
    color: #1f2937;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .excel-header {
    background-color: #107c41;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 7px 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    z-index: 30;
    flex-shrink: 0;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }
  .excel-icon {
    width: 28px;
    height: 28px;
    background: #ffffff;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 15px;
    color: #107c41;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    flex-shrink: 0;
    user-select: none;
  }
  .doc-info {
    display: flex;
    align-items: center;
    min-width: 0;
  }
  .doc-title {
    font-size: 14px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 320px;
  }
  .doc-badge {
    font-size: 11px;
    background: rgba(255,255,255,0.22);
    padding: 2px 8px;
    border-radius: 12px;
    margin-left: 8px;
    white-space: nowrap;
  }
  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }
  .search-box {
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    padding: 3px 10px;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
  }
  .search-input {
    border: none;
    background: transparent;
    outline: none;
    font-size: 12px;
    width: 130px;
    color: #1f2937;
    transition: width 0.2s;
  }
  .search-input:focus {
    width: 180px;
  }
  .search-stats {
    font-size: 11px;
    color: #4b5563;
    margin-left: 4px;
    white-space: nowrap;
    font-weight: 500;
  }
  .search-nav-btn {
    border: none;
    background: none;
    cursor: pointer;
    font-size: 11px;
    color: #374151;
    padding: 1px 4px;
    border-radius: 3px;
  }
  .search-nav-btn:hover {
    background: #e5e7eb;
  }
  .btn-action {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.15);
    color: #ffffff;
    text-decoration: none;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    transition: background 0.15s;
    border: 1px solid rgba(255,255,255,0.3);
    cursor: pointer;
    white-space: nowrap;
  }
  .btn-action:hover {
    background: rgba(255,255,255,0.28);
    color: #ffffff;
  }
  .btn-download {
    background: #ffffff;
    color: #107c41;
    font-weight: 600;
    border: 1px solid #ffffff;
  }
  .btn-download:hover {
    background: #f0fdf4;
    color: #0b5c2f;
  }
  .formula-bar {
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    padding: 4px 12px;
    gap: 8px;
    font-size: 13px;
    flex-shrink: 0;
    z-index: 25;
  }
  .name-box {
    width: 70px;
    height: 25px;
    border: 1px solid #d1d5db;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
    color: #374151;
    background: #f9fafb;
    user-select: none;
  }
  .fx-label {
    font-style: italic;
    font-weight: bold;
    color: #6b7280;
    font-family: serif;
    font-size: 14px;
    user-select: none;
  }
  .formula-content {
    flex: 1;
    height: 25px;
    border: 1px solid #e5e7eb;
    border-radius: 3px;
    padding: 2px 8px;
    background: #ffffff;
    outline: none;
    font-size: 12px;
    color: #111827;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: flex;
    align-items: center;
  }
  .grid-container {
    flex: 1;
    overflow: auto;
    position: relative;
    background: #ffffff;
  }
  .sheet-pane {
    display: none;
    min-width: 100%;
    width: max-content;
  }
  .sheet-pane.active {
    display: block;
  }
  table.excel-table {
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 12px;
    color: #000000;
  }
  th.corner-cell {
    position: sticky;
    top: 0;
    left: 0;
    z-index: 20;
    width: 44px;
    min-width: 44px;
    height: 24px;
    background: #f3f2f1;
    border: 1px solid #d1d5db;
  }
  th.col-header {
    position: sticky;
    top: 0;
    z-index: 10;
    height: 24px;
    min-width: 90px;
    background: #f3f2f1;
    color: #595959;
    font-weight: 600;
    text-align: center;
    border: 1px solid #d1d5db;
    user-select: none;
    padding: 0 4px;
  }
  th.col-header.highlight {
    background: #dcfce7;
    color: #15803d;
    border-bottom: 2px solid #107c41;
  }
  th.row-header {
    position: sticky;
    left: 0;
    z-index: 10;
    width: 44px;
    min-width: 44px;
    height: 24px;
    background: #f3f2f1;
    color: #595959;
    font-weight: 600;
    text-align: center;
    border: 1px solid #d1d5db;
    user-select: none;
    padding: 0 4px;
  }
  th.row-header.highlight {
    background: #dcfce7;
    color: #15803d;
    border-right: 2px solid #107c41;
  }
  td.cell {
    height: 24px;
    border: 1px solid #e5e7eb;
    padding: 2px 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 90px;
    max-width: 320px;
    cursor: cell;
    background: #ffffff;
    user-select: text;
  }
  td.cell.num {
    text-align: right;
  }
  td.cell:hover {
    background-color: #f8fafc;
  }
  td.cell.active {
    outline: none;
    box-shadow: inset 0 0 0 2px #107c41 !important;
    background-color: #f0fdf4 !important;
  }
  td.cell.search-match {
    background-color: #fef08a !important;
  }
  td.cell.search-current {
    background-color: #fde047 !important;
    box-shadow: inset 0 0 0 2px #ca8a04 !important;
  }
  .excel-footer {
    height: 36px;
    background: #f3f2f1;
    border-top: 1px solid #d1d5db;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 12px;
    flex-shrink: 0;
    z-index: 30;
  }
  .sheet-tabs {
    display: flex;
    align-items: center;
    gap: 2px;
    overflow-x: auto;
    height: 100%;
  }
  .sheet-tab {
    padding: 0 16px;
    height: 30px;
    display: flex;
    align-items: center;
    font-size: 12px;
    font-weight: 500;
    color: #4b5563;
    background: transparent;
    border: none;
    border-top: 2px solid transparent;
    cursor: pointer;
    border-radius: 4px 4px 0 0;
    transition: all 0.15s;
    user-select: none;
  }
  .sheet-tab:hover {
    background: #e5e7eb;
    color: #1f2937;
  }
  .sheet-tab.active {
    background: #ffffff;
    color: #107c41;
    font-weight: 600;
    border-top: 2px solid #107c41;
    border-left: 1px solid #d1d5db;
    border-right: 1px solid #d1d5db;
    box-shadow: 0 -2px 5px rgba(0,0,0,0.03);
  }
  .status-info {
    font-size: 11px;
    color: #6b7280;
    display: flex;
    align-items: center;
    gap: 16px;
    user-select: none;
  }
</style>
</head>
<body>

<header class="excel-header">
  <div class="header-left">
    <div class="excel-icon" title="Microsoft Excel">X</div>
    <div class="doc-info">
      <span class="doc-title" title="__DOC_TITLE__">__DOC_TITLE__</span>
      <span class="doc-badge">__DOC_SIZE__</span>
      <span class="doc-badge">__SHEET_BADGE__</span>
    </div>
  </div>
  <div class="header-right">
    <div class="search-box">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
      <input type="text" id="searchInput" class="search-input" placeholder="Tìm kiếm ô..." oninput="performSearch()" onkeydown="handleSearchKey(event)">
      <span id="searchStats" class="search-stats"></span>
      <button class="search-nav-btn" onclick="prevSearch()" title="Kết quả trước">▲</button>
      <button class="search-nav-btn" onclick="nextSearch()" title="Kết quả tiếp">▼</button>
    </div>
    <a href="/dms/file/__DOC_ID__/preview?as_pdf=1" class="btn-action" title="Xem dạng bản in PDF (A4)">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
      Xem bản in PDF
    </a>
    __DOWNLOAD_BTN__
  </div>
</header>

<div class="formula-bar">
  <div id="nameBox" class="name-box">A1</div>
  <div class="fx-label">fx</div>
  <div id="formulaContent" class="formula-content"></div>
</div>

<main class="grid-container">
  __SHEETS_HTML__
</main>

<footer class="excel-footer">
  <div class="sheet-tabs">
    __TABS_HTML__
  </div>
  <div class="status-info">
    <span>🟢 Sẵn sàng</span>
    <span id="statusDim">Số hàng: __FIRST_SHEET_ROWS__ | Số cột: __FIRST_SHEET_COLS__</span>
  </div>
</footer>

<script>
let activeCell = null;
let currentSheetIndex = 0;
let searchMatches = [];
let currentSearchIdx = -1;

function selectCell(cell) {
  if (activeCell) {
    activeCell.classList.remove('active');
    const oldRow = activeCell.dataset.row;
    const oldCol = activeCell.dataset.col;
    document.querySelectorAll('.sheet-pane.active .row-header[data-row="' + oldRow + '"]').forEach(el => el.classList.remove('highlight'));
    document.querySelectorAll('.sheet-pane.active .col-header[data-col="' + oldCol + '"]').forEach(el => el.classList.remove('highlight'));
  }
  activeCell = cell;
  if (cell) {
    cell.classList.add('active');
    const row = cell.dataset.row;
    const col = cell.dataset.col;
    const coord = cell.dataset.coord;
    const val = cell.dataset.val || '';

    document.querySelectorAll('.sheet-pane.active .row-header[data-row="' + row + '"]').forEach(el => el.classList.add('highlight'));
    document.querySelectorAll('.sheet-pane.active .col-header[data-col="' + col + '"]').forEach(el => el.classList.add('highlight'));

    document.getElementById('nameBox').textContent = coord;
    document.getElementById('formulaContent').textContent = val;
  }
}

function switchSheet(index) {
  document.querySelectorAll('.sheet-tab').forEach((tab, i) => {
    tab.classList.toggle('active', i === index);
  });
  document.querySelectorAll('.sheet-pane').forEach((pane, i) => {
    pane.classList.toggle('active', i === index);
    if (i === index) {
      const rows = pane.dataset.rows || '0';
      const cols = pane.dataset.cols || '0';
      document.getElementById('statusDim').textContent = 'Số hàng: ' + rows + ' | Số cột: ' + cols;
    }
  });
  currentSheetIndex = index;
  const firstCell = document.querySelector('.sheet-pane.active td.cell');
  if (firstCell) selectCell(firstCell);
  if (document.getElementById('searchInput').value.trim()) {
    performSearch();
  }
}

function performSearch() {
  const query = document.getElementById('searchInput').value.trim().toLowerCase();
  document.querySelectorAll('td.cell.search-match, td.cell.search-current').forEach(c => {
    c.classList.remove('search-match', 'search-current');
  });
  searchMatches = [];
  currentSearchIdx = -1;

  if (!query) {
    document.getElementById('searchStats').textContent = '';
    return;
  }

  const activePane = document.querySelector('.sheet-pane.active');
  if (!activePane) return;
  activePane.querySelectorAll('td.cell').forEach(cell => {
    const text = (cell.dataset.val || '').toLowerCase();
    if (text && text.includes(query)) {
      cell.classList.add('search-match');
      searchMatches.push(cell);
    }
  });

  if (searchMatches.length > 0) {
    currentSearchIdx = 0;
    highlightCurrentMatch();
  } else {
    document.getElementById('searchStats').textContent = '0 kết quả';
  }
}

function highlightCurrentMatch() {
  if (currentSearchIdx < 0 || currentSearchIdx >= searchMatches.length) return;
  searchMatches.forEach(m => m.classList.remove('search-current'));
  const target = searchMatches[currentSearchIdx];
  target.classList.add('search-current');
  selectCell(target);
  target.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
  document.getElementById('searchStats').textContent = (currentSearchIdx + 1) + '/' + searchMatches.length;
}

function nextSearch() {
  if (searchMatches.length === 0) return;
  currentSearchIdx = (currentSearchIdx + 1) % searchMatches.length;
  highlightCurrentMatch();
}

function prevSearch() {
  if (searchMatches.length === 0) return;
  currentSearchIdx = (currentSearchIdx - 1 + searchMatches.length) % searchMatches.length;
  highlightCurrentMatch();
}

function handleSearchKey(e) {
  if (e.key === 'Enter') {
    e.preventDefault();
    if (e.shiftKey) {
      prevSearch();
    } else {
      nextSearch();
    }
  }
}

document.querySelector('.grid-container').addEventListener('click', function(e) {
  const cell = e.target.closest('td.cell');
  if (cell) selectCell(cell);
});

document.addEventListener('keydown', function(e) {
  if (!activeCell || document.activeElement === document.getElementById('searchInput')) return;
  const row = parseInt(activeCell.dataset.row);
  const col = parseInt(activeCell.dataset.col);
  let nextCell = null;
  const activePane = document.querySelector('.sheet-pane.active');
  if (!activePane) return;

  if (e.key === 'ArrowRight' || e.key === 'Tab') {
    e.preventDefault();
    nextCell = activePane.querySelector('td.cell[data-row="' + row + '"][data-col="' + (col + 1) + '"]');
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault();
    nextCell = activePane.querySelector('td.cell[data-row="' + row + '"][data-col="' + (col - 1) + '"]');
  } else if (e.key === 'ArrowDown' || e.key === 'Enter') {
    e.preventDefault();
    nextCell = activePane.querySelector('td.cell[data-row="' + (row + 1) + '"][data-col="' + col + '"]');
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    nextCell = activePane.querySelector('td.cell[data-row="' + (row - 1) + '"][data-col="' + col + '"]');
  }

  if (nextCell) {
    selectCell(nextCell);
    nextCell.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
  }
});

window.addEventListener('DOMContentLoaded', function() {
  const first = document.querySelector('.sheet-pane.active td.cell');
  if (first) selectCell(first);
});
</script>
</body>
</html>"""

        download_btn_html = ""
        if dms_file.can_download:
            download_btn_html = f"""<a href="/dms/file/{dms_file.id}/download" class="btn-action btn-download" title="Tải tệp Excel về máy">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
      Tải file Excel
    </a>"""

        rendered_html = (
            template.replace("__DOC_TITLE__", filename_esc)
            .replace("__DOC_ID__", str(dms_file.id))
            .replace("__DOWNLOAD_BTN__", download_btn_html)
            .replace("__DOC_SIZE__", file_size_str)
            .replace("__SHEET_BADGE__", sheet_badge)
            .replace("__FIRST_SHEET_ROWS__", str(first_sheet["total_rows"]))
            .replace("__FIRST_SHEET_COLS__", str(first_sheet["cols"]))
            .replace("__TABS_HTML__", "".join(tabs_html))
            .replace("__SHEETS_HTML__", "".join(sheets_html))
        )

        return Response(
            rendered_html,
            content_type="text/html; charset=utf-8",
            headers=[
                (
                    "Content-Disposition",
                    content_disposition(
                        f"{clean(dms_file.name)}.html", disposition_type="inline"
                    ),
                ),
            ],
        )

    def _extract_pptx_slides(self, raw_bytes):
        slides = []
        try:
            with zipfile.ZipFile(BytesIO(raw_bytes)) as z:
                media = {}
                for fname in z.namelist():
                    if fname.startswith("ppt/media/"):
                        bname = os.path.basename(fname)
                        data = z.read(fname)
                        mime = "image/png"
                        if bname.lower().endswith((".jpg", ".jpeg")):
                            mime = "image/jpeg"
                        elif bname.lower().endswith(".gif"):
                            mime = "image/gif"
                        elif bname.lower().endswith(".svg"):
                            mime = "image/svg+xml"
                        media[bname] = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"

                slide_files = [f for f in z.namelist() if f.startswith("ppt/slides/slide") and f.endswith(".xml")]
                slide_files.sort(key=lambda x: int("".join(filter(str.isdigit, os.path.basename(x))) or 0))

                for idx, s_path in enumerate(slide_files, start=1):
                    try:
                        root = ET.fromstring(z.read(s_path))
                        title = ""
                        paragraphs = []
                        tables = []
                        images = []

                        rel_path = f"ppt/slides/_rels/{os.path.basename(s_path)}.rels"
                        r_map = {}
                        if rel_path in z.namelist():
                            try:
                                rel_root = ET.fromstring(z.read(rel_path))
                                for r in rel_root.iter():
                                    if r.tag.endswith("}Relationship"):
                                        r_id = r.get("Id")
                                        target = r.get("Target", "")
                                        img_name = os.path.basename(target)
                                        if img_name in media:
                                            r_map[r_id] = media[img_name]
                            except Exception:
                                pass

                        for elem in root.iter():
                            if elem.tag.endswith("}pic"):
                                for blip in elem.iter():
                                    if blip.tag.endswith("}blip"):
                                        embed_id = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                                        if embed_id and embed_id in r_map:
                                            images.append(r_map[embed_id])
                            elif elem.tag.endswith("}sp"):
                                is_title = False
                                for ph in elem.iter():
                                    if ph.tag.endswith("}ph"):
                                        ptype = ph.get("type", "")
                                        if ptype in ("title", "ctrTitle", "subTitle"):
                                            is_title = True
                                            break
                                lines = []
                                for p in elem.iter():
                                    if p.tag.endswith("}p"):
                                        line = "".join(p.itertext()).strip()
                                        if line:
                                            lines.append(line)
                                if lines:
                                    if is_title and not title:
                                        title = " ".join(lines)
                                    else:
                                        paragraphs.extend(lines)
                            elif elem.tag.endswith("}tbl"):
                                tbl_rows = []
                                for tr in elem.iter():
                                    if tr.tag.endswith("}tr"):
                                        row_cells = []
                                        for tc in tr.iter():
                                            if tc.tag.endswith("}tc"):
                                                row_cells.append("".join(tc.itertext()).strip())
                                        if any(row_cells):
                                            tbl_rows.append(row_cells)
                                if tbl_rows:
                                    tables.append(tbl_rows)

                        if not title and paragraphs:
                            title = paragraphs[0]
                            paragraphs = paragraphs[1:]

                        slides.append({
                            "index": idx,
                            "title": title or f"Slide {idx}",
                            "paragraphs": paragraphs,
                            "tables": tables,
                            "images": images,
                        })
                    except Exception as ex:
                        slides.append({
                            "index": idx,
                            "title": f"Slide {idx}",
                            "paragraphs": [f"Nội dung slide {idx}"],
                            "tables": [],
                            "images": [],
                        })
        except Exception as e:
            _logger.warning("Failed to extract PPTX slides: %s", e)
        return slides

    def _render_powerpoint_presentation_html(self, dms_file):
        """Render interactive PowerPoint slide presentation player HTML."""
        raw_content = dms_file._get_raw_content()
        if not raw_content:
            return None

        ext = (dms_file.extension or "").lower()
        slides = []
        if ext in ("pptx", "ppsx"):
            slides = self._extract_pptx_slides(raw_content)

        filename_esc = html.escape(dms_file.name or "Slide Presentation")
        total_slides = len(slides)

        download_btn_html = ""
        if dms_file.can_download:
            download_btn_html = f"""<a href="/dms/file/{dms_file.id}/download" class="btn-top" title="Tải tệp PowerPoint về máy">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                Tải file PPTX
            </a>"""

        if not slides:
            html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{filename_esc}</title>
<style>
body{{margin:0;padding:40px;background:#1a1d20;color:#fff;font-family:'Segoe UI',system-ui,sans-serif;display:flex;align-items:center;justify-content:center;height:85vh;}}
.card{{background:#22262a;padding:40px;border-radius:12px;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.5);max-width:500px;border:1px solid #343a40;}}
.icon{{width:64px;height:64px;background:#d24726;border-radius:12px;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;font-size:28px;font-weight:bold;color:#fff;}}
h2{{margin:0 0 10px;font-size:20px;font-weight:600;}}
p{{color:#adb5bd;font-size:14px;line-height:1.6;margin:0 0 25px;}}
a{{display:inline-block;padding:10px 24px;background:#d24726;color:#fff;text-decoration:none;border-radius:6px;font-weight:500;}}
</style>
</head>
<body>
<div class="card">
    <div class="icon">P</div>
    <h2>{filename_esc}</h2>
    <p>Tệp trình chiếu PowerPoint ({ext.upper()}) dung lượng {dms_file.human_size or ''}.<br/>Để chuyển đổi tự động sang PDF xem trước, máy chủ cần có LibreOffice.</p>
    {download_btn_html}
</div>
</body>
</html>"""
            return Response(html_content, content_type="text/html; charset=utf-8")

        nav_items_html = []
        slide_views_html = []

        for s in slides:
            s_idx = s["index"]
            s_title_esc = html.escape(s["title"])
            is_first = (s_idx == 1)
            active_cls = "active" if is_first else ""
            display_style = "display:flex;" if is_first else "display:none;"

            nav_items_html.append(
                f'<div class="thumb-item {active_cls}" onclick="goToSlide({s_idx})" id="thumb-{s_idx}">'
                f'<span class="thumb-num">{s_idx}</span>'
                f'<span class="thumb-title">{s_title_esc}</span>'
                f'</div>'
            )

            body_parts = []
            if s.get("paragraphs"):
                body_parts.append('<div class="slide-paragraphs">')
                for p in s["paragraphs"]:
                    body_parts.append(f'<p class="slide-text">• {html.escape(p)}</p>')
                body_parts.append('</div>')

            if s.get("tables"):
                for tbl in s["tables"]:
                    body_parts.append('<table class="slide-table">')
                    for r_idx, row in enumerate(tbl):
                        body_parts.append('<tr>')
                        tag = 'th' if r_idx == 0 else 'td'
                        for cell in row:
                            body_parts.append(f'<{tag}>{html.escape(cell)}</{tag}>')
                        body_parts.append('</tr>')
                    body_parts.append('</table>')

            if s.get("images"):
                body_parts.append('<div class="slide-images">')
                for img_data in s["images"]:
                    body_parts.append(f'<img src="{img_data}" class="slide-img" alt="Slide image" />')
                body_parts.append('</div>')

            slide_views_html.append(
                f'<div class="slide-card" id="slide-{s_idx}" style="{display_style}">'
                f'<div class="slide-header">'
                f'<span class="slide-badge">SLIDE {s_idx}</span>'
                f'<h2 class="slide-title">{s_title_esc}</h2>'
                f'</div>'
                f'<div class="slide-content">{"".join(body_parts)}</div>'
                f'<div class="slide-footer"><span class="brand">PowerPoint Presentation</span><span>{s_idx} / {total_slides}</span></div>'
                f'</div>'
            )

        html_template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{filename_esc}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#14171a;color:#e1e8ed;height:100vh;overflow:hidden;display:flex;flex-direction:column;}}
.topbar{{height:48px;background:#1e2328;border-bottom:1px solid #2d333b;display:flex;align-items:center;justify-content:space-between;padding:0 16px;user-select:none;}}
.topbar-left{{display:flex;align-items:center;gap:12px;}}
.ppt-logo{{width:26px;height:26px;background:#d24726;color:#fff;border-radius:4px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:14px;}}
.doc-name{{font-weight:600;font-size:14px;color:#fff;max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.slide-counter{{font-size:13px;color:#8b949e;background:#2d333b;padding:3px 10px;border-radius:12px;font-weight:500;}}
.topbar-controls{{display:flex;align-items:center;gap:8px;}}
.btn-nav{{background:#2d333b;color:#fff;border:none;padding:6px 14px;border-radius:4px;font-size:13px;cursor:pointer;font-weight:500;transition:background 0.15s;}}
.btn-nav:hover{{background:#38414a;}}
.btn-top{{background:#d24726;color:#fff;text-decoration:none;padding:6px 14px;border-radius:4px;font-size:13px;font-weight:500;display:inline-flex;align-items:center;gap:6px;}}
.btn-top:hover{{background:#b83a1b;}}
.main-stage{{flex:1;display:flex;overflow:hidden;}}
.sidebar{{width:260px;background:#1a1e23;border-right:1px solid #2d333b;overflow-y:auto;padding:12px 8px;display:flex;flex-direction:column;gap:6px;}}
.thumb-item{{padding:10px 12px;border-radius:6px;cursor:pointer;background:#22272e;border:1px solid transparent;display:flex;align-items:center;gap:10px;transition:all 0.15s;}}
.thumb-item:hover{{background:#2d333b;}}
.thumb-item.active{{background:#2d333b;border-color:#d24726;box-shadow:0 0 0 1px #d24726;}}
.thumb-num{{font-size:11px;font-weight:bold;background:#38414a;color:#adb5bd;padding:2px 6px;border-radius:4px;min-width:22px;text-align:center;}}
.thumb-title{{font-size:12px;font-weight:500;color:#c9d1d9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.stage{{flex:1;display:flex;align-items:center;justify-content:center;padding:24px;overflow:auto;background:#0d1117;}}
.slide-card{{width:100%;max-width:960px;min-height:540px;aspect-ratio:16/9;background:#ffffff;color:#212529;border-radius:8px;box-shadow:0 8px 36px rgba(0,0,0,0.6);display:flex;flex-direction:column;padding:36px 44px;position:relative;animation:fadeIn 0.2s ease;}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(4px);}}to{{opacity:1;transform:translateY(0);}}}}
.slide-header{{border-bottom:2px solid #ea580c;padding-bottom:14px;margin-bottom:20px;}}
.slide-badge{{font-size:11px;font-weight:700;color:#ea580c;letter-spacing:1px;text-transform:uppercase;}}
.slide-title{{font-size:24px;font-weight:700;color:#1e293b;margin-top:4px;line-height:1.3;}}
.slide-content{{flex:1;overflow-y:auto;padding-right:8px;display:flex;flex-direction:column;gap:16px;}}
.slide-paragraphs{{display:flex;flex-direction:column;gap:10px;}}
.slide-text{{font-size:16px;line-height:1.6;color:#334155;}}
.slide-table{{width:100%;border-collapse:collapse;margin:10px 0;font-size:14px;}}
.slide-table th,.slide-table td{{border:1px solid #cbd5e1;padding:8px 12px;text-align:left;}}
.slide-table th{{background:#f1f5f9;font-weight:600;color:#0f172a;}}
.slide-images{{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-top:12px;}}
.slide-img{{max-width:100%;max-height:220px;border-radius:6px;object-fit:contain;border:1px solid #e2e8f0;}}
.slide-footer{{margin-top:auto;padding-top:14px;border-top:1px solid #f1f5f9;display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;font-weight:500;}}
.slide-footer .brand{{color:#ea580c;font-weight:600;}}
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-left">
    <div class="ppt-logo">P</div>
    <span class="doc-name">{filename_esc}</span>
    <span class="slide-counter"><span id="cur-slide">1</span> / {total_slides} Slides</span>
  </div>
  <div class="topbar-controls">
    <button class="btn-nav" onclick="prevSlide()" title="Phím mũi tên trái (Left)">&#9664; Trước</button>
    <button class="btn-nav" onclick="nextSlide()" title="Phím mũi tên phải (Right)">Sau &#9654;</button>
    <button class="btn-nav" onclick="toggleFullScreen()" title="Toàn màn hình">&#x26F6; Phóng to</button>
    {download_btn_html}
  </div>
</div>
<div class="main-stage">
  <div class="sidebar">{"".join(nav_items_html)}</div>
  <div class="stage">{"".join(slide_views_html)}</div>
</div>
<script>
let current = 1;
const total = {total_slides};
function goToSlide(idx) {{
  if (idx < 1 || idx > total) return;
  document.getElementById('slide-' + current).style.display = 'none';
  document.getElementById('thumb-' + current).classList.remove('active');
  current = idx;
  document.getElementById('slide-' + current).style.display = 'flex';
  const thumb = document.getElementById('thumb-' + current);
  thumb.classList.add('active');
  thumb.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
  document.getElementById('cur-slide').innerText = current;
}}
function nextSlide() {{ if (current < total) goToSlide(current + 1); }}
function prevSlide() {{ if (current > 1) goToSlide(current - 1); }}
document.addEventListener('keydown', (e) => {{
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{ nextSlide(); }}
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{ prevSlide(); }}
}});
function toggleFullScreen() {{
  if (!document.fullscreenElement) {{
    document.documentElement.requestFullscreen().catch(() => {{}});
  }} else {{
    document.exitFullscreen().catch(() => {{}});
  }}
}}
</script>
</body>
</html>"""
        return Response(html_template, content_type="text/html; charset=utf-8")

    def _extract_docx_document(self, raw_bytes):
        elements = []
        try:
            with zipfile.ZipFile(BytesIO(raw_bytes)) as z:
                media = {}
                for fname in z.namelist():
                    if fname.startswith("word/media/"):
                        bname = os.path.basename(fname)
                        data = z.read(fname)
                        mime = "image/png"
                        if bname.lower().endswith((".jpg", ".jpeg")):
                            mime = "image/jpeg"
                        elif bname.lower().endswith(".gif"):
                            mime = "image/gif"
                        elif bname.lower().endswith(".svg"):
                            mime = "image/svg+xml"
                        media[bname] = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"

                r_map = {}
                rels_path = "word/_rels/document.xml.rels"
                if rels_path in z.namelist():
                    try:
                        rel_root = ET.fromstring(z.read(rels_path))
                        for r in rel_root.iter():
                            if r.tag.endswith("}Relationship"):
                                r_id = r.get("Id")
                                target = r.get("Target", "")
                                img_name = os.path.basename(target)
                                if img_name in media:
                                    r_map[r_id] = media[img_name]
                    except Exception:
                        pass

                doc_xml = z.read("word/document.xml")
                root = ET.fromstring(doc_xml)

                body = None
                for child in root:
                    if child.tag.endswith("}body"):
                        body = child
                        break
                if body is None:
                    body = root

                for node in body:
                    tag = node.tag
                    if tag.endswith("}p"):
                        is_h1 = False
                        is_h2 = False
                        for pPr in node.iter():
                            if pPr.tag.endswith("}pStyle"):
                                val = pPr.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "")
                                if "1" in val or "Title" in val or "Heading1" in val:
                                    is_h1 = True
                                elif "2" in val or "Heading2" in val:
                                    is_h2 = True

                        p_images = []
                        for blip in node.iter():
                            if blip.tag.endswith("}blip"):
                                embed_id = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                                if embed_id and embed_id in r_map:
                                    p_images.append(r_map[embed_id])

                        runs = []
                        for r in node.iter():
                            if r.tag.endswith("}r"):
                                is_bold = any(sub.tag.endswith("}b") for sub in r)
                                is_italic = any(sub.tag.endswith("}i") for sub in r)
                                t = "".join(sub.text for sub in r if sub.tag.endswith("}t") and sub.text)
                                if t:
                                    runs.append({"text": t, "bold": is_bold, "italic": is_italic})

                        text_all = "".join(r["text"] for r in runs).strip()
                        if text_all or p_images:
                            if is_h1:
                                elements.append(("h1", text_all, p_images))
                            elif is_h2:
                                elements.append(("h2", text_all, p_images))
                            else:
                                elements.append(("p", runs, p_images))

                    elif tag.endswith("}tbl"):
                        tbl_rows = []
                        for tr in node:
                            if tr.tag.endswith("}tr"):
                                row_cells = []
                                for tc in tr:
                                    if tc.tag.endswith("}tc"):
                                        tc_text = "".join(tc.itertext()).strip()
                                        row_cells.append(tc_text)
                                if any(row_cells):
                                    tbl_rows.append(row_cells)
                        if tbl_rows:
                            elements.append(("tbl", tbl_rows))
        except Exception as e:
            _logger.warning("Failed to extract DOCX document: %s", e)
        return elements

    def _render_word_document_html(self, dms_file):
        """Render Word document viewer HTML."""
        raw_content = dms_file._get_raw_content()
        if not raw_content:
            return None

        ext = (dms_file.extension or "").lower()
        elements = []
        if ext == "docx":
            elements = self._extract_docx_document(raw_content)

        filename_esc = html.escape(dms_file.name or "Word Document")

        download_btn_html = ""
        if dms_file.can_download:
            download_btn_html = f"""<a href="/dms/file/{dms_file.id}/download" class="btn-top" title="Tải tệp Word về máy">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                Tải file Word
            </a>"""

        body_html = []
        for item in elements:
            itype = item[0]
            if itype == "h1":
                body_html.append(f'<h1 class="doc-h1">{html.escape(item[1])}</h1>')
            elif itype == "h2":
                body_html.append(f'<h2 class="doc-h2">{html.escape(item[1])}</h2>')
            elif itype == "p":
                runs = item[1]
                p_images = item[2]
                line_parts = []
                for r in runs:
                    t_esc = html.escape(r["text"])
                    if r["bold"] and r["italic"]:
                        line_parts.append(f"<b><i>{t_esc}</i></b>")
                    elif r["bold"]:
                        line_parts.append(f"<b>{t_esc}</b>")
                    elif r["italic"]:
                        line_parts.append(f"<i>{t_esc}</i>")
                    else:
                        line_parts.append(t_esc)
                if line_parts:
                    body_html.append(f'<p class="doc-p">{"".join(line_parts)}</p>')
                if p_images:
                    for img_data in p_images:
                        body_html.append(f'<div class="doc-img-wrap"><img src="{img_data}" class="doc-img" alt="Document image"/></div>')
            elif itype == "tbl":
                body_html.append('<table class="doc-table">')
                for r_idx, row in enumerate(item[1]):
                    body_html.append("<tr>")
                    tag = "th" if r_idx == 0 else "td"
                    for cell in row:
                        body_html.append(f"<{tag}>{html.escape(cell)}</{tag}>")
                    body_html.append("</tr>")
                body_html.append("</table>")

        if not body_html:
            body_html.append(f"""<div style="text-align:center;padding:40px 20px;color:#64748b;">
                <p>Tệp văn bản Word ({ext.upper()}) dung lượng {dms_file.human_size or ''}.</p>
                <p>Để xuất sang định dạng PDF chuẩn, máy chủ cần có LibreOffice.</p>
                {download_btn_html}
            </div>""")

        html_template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{filename_esc}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#e2e8f0;color:#1e293b;min-height:100vh;display:flex;flex-direction:column;}}
.topbar{{height:48px;background:#1e293b;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 20px;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,0.15);}}
.topbar-left{{display:flex;align-items:center;gap:12px;}}
.word-logo{{width:26px;height:26px;background:#185abd;color:#fff;border-radius:4px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:14px;}}
.doc-name{{font-weight:600;font-size:14px;color:#fff;max-width:360px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.topbar-right{{display:flex;align-items:center;gap:10px;}}
.btn-nav{{background:#334155;color:#fff;border:none;padding:6px 12px;border-radius:4px;font-size:13px;cursor:pointer;font-weight:500;}}
.btn-nav:hover{{background:#475569;}}
.btn-top{{background:#185abd;color:#fff;text-decoration:none;padding:6px 14px;border-radius:4px;font-size:13px;font-weight:500;display:inline-flex;align-items:center;gap:6px;}}
.btn-top:hover{{background:#104796;}}
.page-container{{padding:30px 16px;flex:1;display:flex;justify-content:center;overflow-y:auto;}}
.paper{{background:#ffffff;width:100%;max-width:850px;min-height:90vh;padding:56px 64px;box-shadow:0 4px 20px rgba(0,0,0,0.08);border-radius:4px;font-size:15px;line-height:1.7;color:#334155;}}
.doc-h1{{font-size:26px;font-weight:700;color:#0f172a;margin:24px 0 14px;line-height:1.3;border-bottom:2px solid #e2e8f0;padding-bottom:8px;}}
.doc-h2{{font-size:20px;font-weight:600;color:#1e293b;margin:20px 0 10px;line-height:1.3;}}
.doc-p{{margin-bottom:12px;text-align:justify;}}
.doc-table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;}}
.doc-table th,.doc-table td{{border:1px solid #cbd5e1;padding:10px 14px;text-align:left;}}
.doc-table th{{background:#f8fafc;font-weight:600;color:#0f172a;}}
.doc-img-wrap{{text-align:center;margin:16px 0;}}
.doc-img{{max-width:100%;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.08);}}
#docx-canvas{{width:100%;}}
</style>
<script src="https://unpkg.com/jszip/dist/jszip.min.js"></script>
<script src="https://unpkg.com/docx-preview/dist/docx-preview.min.js"></script>
</head>
<body>
<div class="topbar">
  <div class="topbar-left">
    <div class="word-logo">W</div>
    <span class="doc-name">{filename_esc}</span>
  </div>
  <div class="topbar-right">
    <button class="btn-nav" onclick="zoomDoc(0.1)" title="Phóng to">A+</button>
    <button class="btn-nav" onclick="zoomDoc(-0.1)" title="Thu nhỏ">A-</button>
    <button class="btn-nav" onclick="window.print()" title="In văn bản">&#128438; In</button>
    {download_btn_html}
  </div>
</div>
<div class="page-container">
  <div class="paper" id="paper-doc">
    <div id="docx-native">{"".join(body_html)}</div>
    <div id="docx-canvas" style="display:none;"></div>
  </div>
</div>
<script>
let curZoom = 1;
function zoomDoc(step) {{
  curZoom = Math.max(0.7, Math.min(1.6, curZoom + step));
  document.getElementById('paper-doc').style.zoom = curZoom;
}}
if (window.docx) {{
  fetch('/dms/file/{dms_file.id}/download')
    .then(r => r.blob())
    .then(blob => {{
      const canvasEl = document.getElementById('docx-canvas');
      docx.renderAsync(blob, canvasEl, null, {{ inWrapper: false }})
        .then(() => {{
          document.getElementById('docx-native').style.display = 'none';
          canvasEl.style.display = 'block';
        }})
        .catch(err => console.log('Using native docx renderer'));
    }})
    .catch(err => console.log('Using native docx renderer'));
}}
</script>
</body>
</html>"""
        return Response(html_template, content_type="text/html; charset=utf-8")

    @http.route(
        ["/dms/file/<int:dms_file_id>/preview", "/dms/file/<int:dms_file_id>/content"],
        type="http",
        auth="user",
    )
    def dms_file_preview(self, dms_file_id, as_pdf=False, **kw):
        dms_file = request.env["dms.file"].browse(dms_file_id)
        if not dms_file.exists():
            return request.not_found()
        try:
            dms_file.check_access("read")
        except AccessError:
            return request.not_found()

        # 1. If explicit PDF conversion requested (?as_pdf=1)
        if as_pdf:
            pdf_data = dms_file._convert_to_pdf()
            if pdf_data:
                name_base = (dms_file.name or f"file_{dms_file_id}").rsplit(".", 1)[0]
                pdf_filename = f"{clean(name_base)}.pdf"
                return send_file(
                    BytesIO(pdf_data),
                    environ=request.httprequest.environ,
                    mimetype="application/pdf",
                    download_name=pdf_filename,
                    as_attachment=False,
                    conditional=True,
                )
            # If LibreOffice is not installed, fall through to native HTML renderers!

        # 2. If it is an Excel / tabular spreadsheet, render interactive spreadsheet grid!
        if dms_file._is_excel_spreadsheet():
            spreadsheet_resp = self._render_excel_spreadsheet_html(dms_file)
            if spreadsheet_resp:
                return spreadsheet_resp

        # 3. PowerPoint (.pptx, .ppt, .ppsx, .odp)
        ext = (dms_file.extension or "").lower()
        if ext in ("pptx", "ppt", "ppsx", "odp"):
            pdf_data = dms_file._convert_to_pdf()
            if pdf_data:
                name_base = (dms_file.name or f"file_{dms_file_id}").rsplit(".", 1)[0]
                pdf_filename = f"{clean(name_base)}.pdf"
                return send_file(
                    BytesIO(pdf_data),
                    environ=request.httprequest.environ,
                    mimetype="application/pdf",
                    download_name=pdf_filename,
                    as_attachment=False,
                    conditional=True,
                )
            pptx_resp = self._render_powerpoint_presentation_html(dms_file)
            if pptx_resp:
                return pptx_resp

        # 4. Word (.docx, .doc, .odt, .rtf)
        if ext in ("docx", "doc", "odt", "rtf"):
            pdf_data = dms_file._convert_to_pdf()
            if pdf_data:
                name_base = (dms_file.name or f"file_{dms_file_id}").rsplit(".", 1)[0]
                pdf_filename = f"{clean(name_base)}.pdf"
                return send_file(
                    BytesIO(pdf_data),
                    environ=request.httprequest.environ,
                    mimetype="application/pdf",
                    download_name=pdf_filename,
                    as_attachment=False,
                    conditional=True,
                )
            docx_resp = self._render_word_document_html(dms_file)
            if docx_resp:
                return docx_resp

        # 5. Other Office documents -> Preview via converted PDF
        if dms_file._is_office_document():
            pdf_data = dms_file._convert_to_pdf()
            if pdf_data:
                name_base = (dms_file.name or f"file_{dms_file_id}").rsplit(".", 1)[0]
                pdf_filename = f"{clean(name_base)}.pdf"
                return send_file(
                    BytesIO(pdf_data),
                    environ=request.httprequest.environ,
                    mimetype="application/pdf",
                    download_name=pdf_filename,
                    as_attachment=False,
                    conditional=True,
                )
            else:
                return self._render_preview_error_response(dms_file)

        raw_content = dms_file._get_raw_content()
        filename = clean(dms_file.name) or f"file_{dms_file_id}"
        ext = (dms_file.extension or "").lower()

        # Resolve accurate mimetype for browser playback/viewing
        mimetype = dms_file.mimetype or ""
        if not mimetype or mimetype in ("application/octet-stream", "binary/octet-stream"):
            guessed, _ = mimetypes.guess_type(filename)
            mimetype = guessed or ""

        if ext in ("mp4", "m4v"):
            mimetype = "video/mp4"
        elif ext == "mov":
            mimetype = "video/mp4"
        elif ext == "webm":
            mimetype = "video/webm"
        elif ext == "ogg":
            mimetype = "video/ogg"
        elif ext == "mp3":
            mimetype = "audio/mpeg"
        elif ext == "wav":
            mimetype = "audio/wav"
        elif ext == "pdf":
            mimetype = "application/pdf"
        elif not mimetype:
            mimetype = "application/octet-stream"

        # Handle text charset so Vietnamese and special chars display correctly
        if mimetype.startswith("text/") or ext in ["txt", "log", "json", "xml", "csv", "md", "py", "sql", "html"]:
            if "charset" not in mimetype:
                mimetype = f"{mimetype}; charset=utf-8" if mimetype.startswith("text/") else "text/plain; charset=utf-8"

        resp = send_file(
            BytesIO(raw_content),
            environ=request.httprequest.environ,
            mimetype=mimetype,
            download_name=filename,
            as_attachment=False,
            conditional=True,
        )
        resp.headers["Accept-Ranges"] = "bytes"
        return resp

    @http.route(
        ["/dms/file/<int:dms_file_id>/download"],
        type="http",
        auth="user",
    )
    def dms_file_download(self, dms_file_id, **kw):
        dms_file = request.env["dms.file"].browse(dms_file_id)
        if not dms_file.exists():
            return request.not_found()
        try:
            dms_file.check_access("read")
        except AccessError:
            return request.not_found()

        # BẢO MẬT: Kiểm tra quyền tải về của người dùng hiện tại
        if not dms_file.can_download:
            raise Forbidden("Bạn không có quyền tải tệp này về máy. Vui lòng liên hệ quản lý!")

        raw_content = dms_file._get_raw_content()
        filename = clean(dms_file.name) or f"file_{dms_file_id}"
        ext = (dms_file.extension or "").lower()

        mimetype = dms_file.mimetype or ""
        if not mimetype or mimetype in ("application/octet-stream", "binary/octet-stream"):
            guessed, _ = mimetypes.guess_type(filename)
            mimetype = guessed or "application/octet-stream"

        return send_file(
            BytesIO(raw_content),
            environ=request.httprequest.environ,
            mimetype=mimetype,
            download_name=filename,
            as_attachment=True,
            conditional=True,
        )


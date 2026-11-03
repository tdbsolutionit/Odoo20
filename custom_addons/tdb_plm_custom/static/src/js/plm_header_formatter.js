/** @odoo-module **/
/**
 * =============================================================================
 * TDB SOLUTION - PLM COLUMN HEADER FORMATTER (SONG NGỮ ANH - VIỆT 2 DÒNG)
 * Tách biệt và hiển thị tiêu đề cột thành 2 dòng chuẩn:
 * Dòng 1: Tiếng Anh (Chữ đậm, rõ nét)
 * Dòng 2: (Tiếng Việt) (Trong ngoặc đơn, căn giữa ngay phía dưới)
 * =============================================================================
 */

(function () {
    'use strict';

    var HEADER_REGEX = /^(.*?)(?:\r?\n|\s+)(\(.*?\))\s*$/;

    function formatPlmHeaders() {
        var tables = document.querySelectorAll('table.tdb_plm_list_view, .tdb_plm_list_view table, table.o_list_table');
        if (!tables.length) return;

        tables.forEach(function (table) {
            // Chỉ áp dụng cho các bảng thuộc phân hệ PLM hoặc có class tdb_plm_list_view
            var isPlm = table.classList.contains('tdb_plm_list_view') ||
                (table.closest && table.closest('.tdb_plm_list_view')) ||
                table.querySelector('th[data-name="engineering_code"]');

            if (!isPlm) return;

            var thElements = table.querySelectorAll('thead th[data-name]');
            thElements.forEach(function (th) {
                if (th.getAttribute('data-tdb-formatted') === '1') return;

                // Tìm thẻ chứa text của tiêu đề (thường là span hoặc .text-truncate)
                var labelNode = th.querySelector('.text-truncate, .o_column_title, span');
                if (!labelNode) return;

                var text = (labelNode.textContent || '').trim();
                var match = text.match(HEADER_REGEX);

                if (match) {
                    var enText = match[1].trim();
                    var viText = match[2].trim();

                    labelNode.innerHTML =
                        '<span class="tdb_plm_title_en">' + enText + '</span>' +
                        '<span class="tdb_plm_title_vi">' + viText + '</span>';

                    th.setAttribute('data-tdb-formatted', '1');
                }
            });
        });
    }

    // Khởi chạy khi DOM sẵn sàng
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', formatPlmHeaders);
    } else {
        formatPlmHeaders();
    }

    // Quan sát thay đổi DOM bằng MutationObserver để định dạng lại khi OWL re-render danh sách
    var scheduled = false;
    var observer = new MutationObserver(function () {
        if (!scheduled) {
            scheduled = true;
            window.requestAnimationFrame(function () {
                formatPlmHeaders();
                scheduled = false;
            });
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });
})();

/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { SlideArchive } from "@website_slides/interactions/slide_archive";

function formatSize(bytes) {
    if (!bytes) return "0 B";
    const mb = bytes / (1024 * 1024);
    if (mb >= 1024) {
        return (mb / 1024).toFixed(2) + " GB";
    }
    return mb.toFixed(1) + " MB";
}

function cleanTitle(filename) {
    const lastDot = filename.lastIndexOf(".");
    const base = lastDot > 0 ? filename.substring(0, lastDot) : filename;
    return base
        .replace(/[_\-]+/g, " ")
        .trim()
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

class WebsiteDiskVideoManager {
    constructor(channelId, channelName, folderPath, folderDisplay, categoryId = null) {
        this.channelId = parseInt(channelId, 10);
        this.channelName = channelName || "Khóa học";
        this.folderPath = folderPath || "";
        this.folderDisplay = folderDisplay || (folderPath ? "C:\\Work\\odoo20-docker\\videos\\" + folderPath : "Chưa chọn thư mục");
        this.categoryId = categoryId ? parseInt(categoryId, 10) : null;
        this.categories = [];
        this.videos = [];
        this.isUploading = false;
        this.modalEl = null;

        this.initModal();
    }

    initModal() {
        const existing = document.getElementById("tdb_disk_video_modal");
        if (existing) {
            existing.remove();
        }

        const modalHtml = `
        <div class="modal fade show" id="tdb_disk_video_modal" tabindex="-1" style="display: block; background: rgba(0,0,0,0.5); z-index: 1055;" aria-modal="true" role="dialog">
            <div class="modal-dialog modal-xl modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-light">
                        <div>
                            <h5 class="modal-title fw-bold text-dark mb-1">Thêm Video từ Thư mục Ổ đĩa vào Khóa học</h5>
                            <div class="text-secondary small">
                                Khóa học: <strong class="text-dark me-3">${this.escapeHtml(this.channelName)}</strong>
                                Ổ đĩa / Thư mục lưu trữ: <strong class="text-primary font-monospace" id="tdb_modal_folder_display">${this.escapeHtml(this.folderDisplay)}</strong>
                            </div>
                        </div>
                        <button type="button" class="btn-close" id="tdb_modal_btn_close" aria-label="Close"></button>
                    </div>
                    <div class="modal-body p-4">
                        <!-- Toolbar các nút chức năng -->
                        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3 p-3 bg-light rounded border">
                            <div>
                                <span class="fw-bold text-dark">Thao tác chọn video</span>
                                <div class="text-muted small">Quét các video đang có sẵn trong thư mục máy tính hoặc chọn qua File Explorer</div>
                            </div>
                            <div class="d-flex gap-2">
                                <button type="button" class="btn btn-success btn-sm fw-bold" id="tdb_btn_scan_folder">
                                    Quét video có sẵn trong thư mục máy tính
                                </button>
                                <button type="button" class="btn btn-outline-primary btn-sm" id="tdb_btn_select_folder">
                                    Chọn thư mục từ máy tính (File Explorer)
                                </button>
                                <button type="button" class="btn btn-outline-secondary btn-sm" id="tdb_btn_select_files">
                                    Chọn file video từ máy tính
                                </button>
                            </div>
                        </div>

                        <!-- Thông báo / Tiến trình tải lên -->
                        <div id="tdb_modal_alert" class="alert alert-info py-2 small d-none"></div>

                        <div id="tdb_modal_progress_container" class="my-3 p-3 bg-light rounded border d-none">
                            <div class="d-flex justify-content-between small text-muted mb-1">
                                <span id="tdb_modal_progress_text">Đang xử lý tải lên...</span>
                                <span class="fw-bold text-primary" id="tdb_modal_progress_percent">0%</span>
                            </div>
                            <div class="progress" style="height: 10px;">
                                <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" id="tdb_modal_progress_bar" style="width: 0%;"></div>
                            </div>
                        </div>

                        <!-- Bảng danh sách các video -->
                        <div class="d-flex align-items-center justify-content-between mb-2">
                            <span class="text-muted small" id="tdb_modal_count_summary">Chưa quét được video nào</span>
                            <button type="button" class="btn btn-outline-secondary btn-sm py-0" id="tdb_btn_toggle_all">Chọn tất cả</button>
                        </div>
                        <div class="table-responsive bg-white rounded border" style="max-height: 340px; overflow-y: auto;">
                            <table class="table table-sm table-hover mb-0 align-middle">
                                <thead class="table-light sticky-top">
                                    <tr>
                                        <th style="width: 40px;" class="text-center">
                                            <input type="checkbox" class="form-check-input" id="tdb_modal_master_check"/>
                                        </th>
                                        <th>Tên file video</th>
                                        <th style="width: 100px;">Dung lượng</th>
                                        <th>Ổ đĩa / Thư mục lưu trữ trên máy tính</th>
                                        <th>Tiêu đề bài học trên Odoo</th>
                                        <th style="width: 100px;" class="text-center">Thiết lập</th>
                                        <th style="width: 150px;" class="text-center">Trạng thái</th>
                                    </tr>
                                </thead>
                                <tbody id="tdb_modal_video_tbody">
                                    <tr>
                                        <td colspan="7" class="text-center text-muted py-4">
                                            Đang tải danh sách video có sẵn trên ổ đĩa...
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" id="tdb_modal_btn_cancel">Đóng</button>
                        <button type="button" class="btn btn-primary btn-sm fw-bold" id="tdb_modal_btn_submit" disabled="true">
                            Thêm vào khóa học
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML("beforeend", modalHtml);
        this.modalEl = document.getElementById("tdb_disk_video_modal");

        this.bindEvents();

        // Tự động quét các video đã nằm sẵn trong thư mục máy tính
        this.scanDiskFolder();
    }

    bindEvents() {
        const closeBtn = document.getElementById("tdb_modal_btn_close");
        const cancelBtn = document.getElementById("tdb_modal_btn_cancel");
        if (closeBtn) closeBtn.onclick = () => this.close();
        if (cancelBtn) cancelBtn.onclick = () => this.close();

        const scanBtn = document.getElementById("tdb_btn_scan_folder");
        if (scanBtn) scanBtn.onclick = () => this.scanDiskFolder();

        const selectFolderBtn = document.getElementById("tdb_btn_select_folder");
        if (selectFolderBtn) selectFolderBtn.onclick = () => this.triggerSelectFolder();

        const selectFilesBtn = document.getElementById("tdb_btn_select_files");
        if (selectFilesBtn) selectFilesBtn.onclick = () => this.triggerSelectFiles();

        const toggleAllBtn = document.getElementById("tdb_btn_toggle_all");
        if (toggleAllBtn) toggleAllBtn.onclick = () => this.toggleAll();

        const masterCheck = document.getElementById("tdb_modal_master_check");
        if (masterCheck) masterCheck.onchange = (e) => this.setAllSelected(e.target.checked);

        const submitBtn = document.getElementById("tdb_modal_btn_submit");
        if (submitBtn) submitBtn.onclick = () => this.submitSelected();
    }

    close() {
        if (this.modalEl) {
            this.modalEl.remove();
            this.modalEl = null;
        }
    }

    escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    async scanDiskFolder() {
        this.showAlert("Đang quét thư mục trên máy tính...", "info");
        try {
            const data = await rpc("/slides/get_channel_disk_videos", {
                channel_id: this.channelId,
            });

            if (data.error) {
                this.showAlert(data.error, "danger");
                return;
            }

            if (data.folder_display) {
                this.folderDisplay = data.folder_display;
                const dispEl = document.getElementById("tdb_modal_folder_display");
                if (dispEl) dispEl.innerText = this.folderDisplay;
            }

            if (data.categories) {
                this.categories = data.categories;
            }

            const rawVideos = data.videos || [];
            if (!rawVideos.length) {
                this.videos = [];
                this.renderTable();
                this.showAlert("Không tìm thấy video nào trong thư mục ổ đĩa của khóa học. Bạn có thể bấm 'Chọn thư mục từ máy tính' để chọn thư mục khác.", "warning");
                return;
            }

            this.videos = rawVideos.map((v, idx) => ({
                id: idx + 1,
                slideId: v.slide_id || 0,
                isExistingOnDisk: true,
                filename: v.filename,
                title: v.title,
                sizeStr: v.size_str,
                diskPath: v.disk_path,
                alreadyInCourse: v.already_in_course,
                selected: !v.already_in_course,
                categoryId: v.category_id || this.categoryId || 0,
                categoryName: v.category_name || "",
                durationMinutes: v.duration_minutes || 15,
                description: v.description || "",
                resourceFile: null,
                showDetails: false,
                isSaving: false,
                status: v.already_in_course ? "already" : "ready",
            }));

            this.renderTable();
            const newCount = this.videos.filter((v) => !v.alreadyInCourse).length;
            this.showAlert(`Đã quét xong thư mục: Tìm thấy ${this.videos.length} video (${newCount} video mới sẵn sàng đưa vào khóa học).`, "success");
        } catch (err) {
            this.showAlert("Lỗi khi kết nối đến máy chủ: " + err.message, "danger");
        }
    }

    triggerSelectFolder() {
        const input = document.createElement("input");
        input.type = "file";
        input.webkitdirectory = true;
        input.directory = true;
        input.multiple = true;
        input.onchange = (e) => this.onFolderSelected(e);
        input.click();
    }

    triggerSelectFiles() {
        const input = document.createElement("input");
        input.type = "file";
        input.multiple = true;
        input.accept = "video/*,.mp4,.mkv,.avi,.mov,.webm,.flv,.m4v";
        input.onchange = (e) => this.onFilesSelected(e);
        input.click();
    }

    onFolderSelected(e) {
        const files = Array.from(e.target.files || []);
        if (!files.length) return;

        const videoExts = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v"];
        const videoFiles = files.filter((f) => {
            const ext = f.name.substring(f.name.lastIndexOf(".")).toLowerCase();
            return videoExts.includes(ext);
        });

        if (!videoFiles.length) {
            this.showAlert("Không tìm thấy file video nào trong thư mục đã chọn!", "warning");
            return;
        }

        let folderName = "";
        if (videoFiles[0].webkitRelativePath) {
            folderName = videoFiles[0].webkitRelativePath.split("/")[0];
        }
        if (!folderName) folderName = "Thư mục máy tính";

        this.folderPath = folderName;
        this.folderDisplay = "C:\\Work\\odoo20-docker\\videos\\" + folderName;
        const dispEl = document.getElementById("tdb_modal_folder_display");
        if (dispEl) dispEl.innerText = this.folderDisplay;

        this.populateFromLocalFiles(videoFiles);
    }

    onFilesSelected(e) {
        const files = Array.from(e.target.files || []);
        if (!files.length) return;

        const videoExts = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v"];
        const videoFiles = files.filter((f) => {
            const ext = f.name.substring(f.name.lastIndexOf(".")).toLowerCase();
            return videoExts.includes(ext);
        });

        if (!videoFiles.length) {
            this.showAlert("Vui lòng chọn ít nhất một file video hợp lệ!", "warning");
            return;
        }

        this.populateFromLocalFiles(videoFiles);
    }

    populateFromLocalFiles(files) {
        files.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: "base" }));

        this.videos = files.map((file, idx) => {
            const item = {
                id: idx + 1,
                file: file,
                isExistingOnDisk: false,
                filename: file.name,
                title: cleanTitle(file.name),
                sizeStr: formatSize(file.size),
                diskPath: this.folderDisplay + "\\" + file.name,
                alreadyInCourse: false,
                selected: true,
                categoryId: this.categoryId || 0,
                categoryName: "",
                durationMinutes: 15,
                description: "",
                resourceFile: null,
                showDetails: false,
                status: "ready",
                progress: 0,
            };

            // Tự động nhận diện thời lượng thật của video từ file metadata
            try {
                const tempVideo = document.createElement("video");
                tempVideo.preload = "metadata";
                tempVideo.onloadedmetadata = () => {
                    if (tempVideo.duration && !isNaN(tempVideo.duration) && tempVideo.duration > 0) {
                        item.durationMinutes = Math.max(1, Math.round(tempVideo.duration / 60));
                    }
                    URL.revokeObjectURL(tempVideo.src);
                };
                tempVideo.src = URL.createObjectURL(file);
            } catch (e) {}

            return item;
        });

        this.renderTable();
        this.showAlert(`Đã chọn ${this.videos.length} video từ File Explorer sẵn sàng đưa vào khóa học.`, "info");
    }

    renderTable() {
        const tbody = document.getElementById("tdb_modal_video_tbody");
        const countSummary = document.getElementById("tdb_modal_count_summary");
        const submitBtn = document.getElementById("tdb_modal_btn_submit");
        if (!tbody) return;

        if (!this.videos.length) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">Chưa có video nào. Bạn hãy bấm nút quét hoặc chọn thư mục từ máy tính.</td></tr>`;
            if (countSummary) countSummary.innerText = "0 video";
            if (submitBtn) submitBtn.disabled = true;
            return;
        }

        const selectedCount = this.videos.filter((v) => v.selected && v.status !== "already").length;
        if (countSummary) {
            countSummary.innerHTML = `Tìm thấy <strong>${this.videos.length}</strong> video | Đã chọn: <strong class="text-success">${selectedCount}</strong> video`;
        }
        if (submitBtn) {
            submitBtn.disabled = selectedCount === 0 || this.isUploading;
        }

        let html = "";
        this.videos.forEach((item) => {
            const isAlready = item.alreadyInCourse || item.status === "already";
            let statusBadge = `<span class="badge bg-secondary">Sẵn sàng</span>`;
            if (isAlready) {
                statusBadge = `<span class="badge bg-success-subtle text-success border border-success-subtle">Đã có trong khóa học</span>`;
            } else if (item.status === "uploading") {
                statusBadge = `<span class="badge bg-primary">Đang tải ${item.progress || 0}%</span>`;
            } else if (item.status === "done") {
                statusBadge = `<span class="badge bg-success">Đã hoàn thành</span>`;
            } else if (item.status === "error") {
                statusBadge = `<span class="badge bg-danger">Lỗi</span>`;
            }

            // Options for categories
            let catOptions = `<option value="0">-- Mặc định (Không chọn chương) --</option>`;
            if (this.categories && this.categories.length) {
                this.categories.forEach((cat) => {
                    const sel = String(item.categoryId) === String(cat.id) ? "selected" : "";
                    catOptions += `<option value="${cat.id}" ${sel}>${this.escapeHtml(cat.name)}</option>`;
                });
            }
            const isNewCat = item.categoryId === "new";
            catOptions += `<option value="new" ${isNewCat ? "selected" : ""}>+ Tạo chương mới...</option>`;

            html += `
            <tr class="${item.selected && !isAlready ? "" : "text-muted opacity-75"} align-middle">
                <td class="text-center">
                    <input type="checkbox" class="form-check-input tdb-item-check" data-id="${item.id}"
                           ${item.selected && !isAlready ? "checked" : ""}
                           ${isAlready || this.isUploading ? "disabled" : ""}/>
                </td>
                <td class="font-monospace small fw-bold text-dark">${this.escapeHtml(item.filename)}</td>
                <td class="small text-muted">${item.sizeStr}</td>
                <td class="font-monospace small text-primary">${this.escapeHtml(item.diskPath)}</td>
                <td>
                    <input type="text" class="form-control form-control-sm tdb-item-title" data-id="${item.id}"
                           value="${this.escapeHtml(item.title)}"
                           placeholder="Nhập tiêu đề bài học"
                           ${this.isUploading ? "disabled" : ""}/>
                </td>
                <td class="text-center">
                    <button type="button" class="btn btn-outline-secondary btn-sm py-0 tdb-item-toggle-details" data-id="${item.id}"
                            ${this.isUploading ? "disabled" : ""}>
                        ${item.showDetails ? "Thu gọn" : "Thiết lập"}
                    </button>
                    ${item.resourceFile ? `<span class="badge bg-info ms-1" title="Có tài liệu đính kèm">1 file</span>` : ""}
                </td>
                <td class="text-center">${statusBadge}</td>
            </tr>
            `;

            if (item.showDetails) {
                html += `
                <tr class="bg-light border-bottom">
                    <td></td>
                    <td colspan="6" class="p-3">
                        <div class="row g-3 align-items-start">
                            <div class="col-md-4">
                                <label class="form-label small fw-bold mb-1">Chương / Phần học:</label>
                                <select class="form-select form-select-sm tdb-item-cat" data-id="${item.id}">
                                    ${catOptions}
                                </select>
                                ${isNewCat ? `
                                <input type="text" class="form-control form-control-sm mt-1 tdb-item-newcat" data-id="${item.id}"
                                       value="${this.escapeHtml(item.categoryName || '')}"
                                       placeholder="Nhập tên chương mới..."/>
                                ` : ''}
                            </div>
                            <div class="col-md-4">
                                <label class="form-label small fw-bold mb-1">Mô tả bài học:</label>
                                <input type="text" class="form-control form-control-sm tdb-item-desc" data-id="${item.id}"
                                       value="${this.escapeHtml(item.description || '')}"
                                       placeholder="Tóm tắt ngắn gọn nội dung bài học..."/>
                                <div class="small text-muted mt-1">
                                    Thời lượng: <em>Tự động nhận diện từ video</em>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label small fw-bold mb-1">Tài liệu đính kèm (tùy chọn):</label>
                                <div class="d-flex align-items-center gap-1">
                                    <input type="file" class="form-control form-control-sm tdb-item-resource" data-id="${item.id}"/>
                                    ${item.resourceFile ? `
                                    <button type="button" class="btn btn-outline-danger btn-sm py-0 px-2 tdb-item-clear-res text-nowrap" data-id="${item.id}">
                                        Xóa
                                    </button>
                                    ` : ''}
                                </div>
                                ${item.resourceFile ? `
                                <div class="small text-success mt-1 text-truncate">
                                    Đã chọn: <strong>${this.escapeHtml(item.resourceFile.name)}</strong>
                                </div>
                                ` : `
                                <div class="small text-muted mt-1">
                                    Đính kèm PDF, slide, bài tập liên quan...
                                </div>
                                `}
                            </div>
                            ${isAlready ? `
                            <div class="col-12 d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
                                <span class="text-secondary small">
                                    Bài học đã có trong khóa học. Bạn có thể chọn chương khác hoặc sửa tên rồi bấm lưu.
                                </span>
                                <button type="button" class="btn btn-warning btn-sm fw-bold px-3 text-dark tdb-item-btn-save" data-id="${item.id}" ${item.isSaving ? "disabled" : ""}>
                                    ${item.isSaving ? "Đang lưu thay đổi..." : "Lưu thay đổi bài học"}
                                </button>
                            </div>
                            ` : ''}
                        </div>
                    </td>
                </tr>
                `;
            }
        });

        tbody.innerHTML = html;

        // Bind check & title inputs
        tbody.querySelectorAll(".tdb-item-check").forEach((chk) => {
            chk.onchange = (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) item.selected = e.target.checked;
                this.updateSelectionSummary();
            };
        });

        tbody.querySelectorAll(".tdb-item-title").forEach((inp) => {
            inp.oninput = (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) item.title = e.target.value;
            };
        });

        tbody.querySelectorAll(".tdb-item-toggle-details").forEach((btn) => {
            btn.onclick = (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) {
                    item.showDetails = !item.showDetails;
                    this.renderTable();
                }
            };
        });

        tbody.querySelectorAll(".tdb-item-cat").forEach((sel) => {
            sel.onchange = (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) {
                    item.categoryId = e.target.value;
                    this.renderTable();
                }
            };
        });

        tbody.querySelectorAll(".tdb-item-newcat").forEach((inp) => {
            inp.oninput = (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) item.categoryName = e.target.value;
            };
        });

        tbody.querySelectorAll(".tdb-item-resource").forEach((inp) => {
            inp.onchange = (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) {
                    item.resourceFile = e.target.files && e.target.files[0] ? e.target.files[0] : null;
                    this.renderTable();
                }
            };
        });

        tbody.querySelectorAll(".tdb-item-clear-res").forEach((btn) => {
            btn.onclick = (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) {
                    item.resourceFile = null;
                    this.renderTable();
                }
            };
        });

        tbody.querySelectorAll(".tdb-item-desc").forEach((inp) => {
            inp.oninput = (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) item.description = e.target.value;
            };
        });

        tbody.querySelectorAll(".tdb-item-btn-save").forEach((btn) => {
            btn.onclick = async (e) => {
                const id = parseInt(e.target.dataset.id, 10);
                const item = this.videos.find((v) => v.id === id);
                if (item) {
                    await this.updateExistingLesson(item);
                }
            };
        });
    }

    async updateExistingLesson(item) {
        if (!item) return;
        item.isSaving = true;
        this.renderTable();
        try {
            const res = await rpc("/slides/update_lesson_details", {
                slide_id: item.slideId || 0,
                filename: item.filename,
                channel_id: this.channelId,
                title: item.title,
                category_id: item.categoryId === "new" ? 0 : (parseInt(item.categoryId, 10) || 0),
                category_name: item.categoryId === "new" ? (item.categoryName || "") : "",
                description: item.description || "",
                duration_minutes: item.durationMinutes || 15,
            });

            if (res.error) throw new Error(res.error);

            if (res.slide_id) item.slideId = res.slide_id;
            if (res.category_id) item.categoryId = res.category_id;
            if (res.category_name) item.categoryName = res.category_name;
            if (res.categories && res.categories.length) this.categories = res.categories;

            if (item.resourceFile && item.slideId) {
                await this.uploadResourceFile(item.slideId, item.resourceFile);
            }

            this.showAlert(`Đã cập nhật bài học "${item.title || item.filename}" thành công! Hãy tải lại trang để thấy vị trí chương mới.`, "success");
        } catch (err) {
            this.showAlert("Lỗi khi cập nhật bài học: " + (err.message || err), "danger");
        } finally {
            item.isSaving = false;
            this.renderTable();
        }
    }

    updateSelectionSummary() {
        const countSummary = document.getElementById("tdb_modal_count_summary");
        const submitBtn = document.getElementById("tdb_modal_btn_submit");
        const selectedCount = this.videos.filter((v) => v.selected && !v.alreadyInCourse && v.status !== "already").length;
        if (countSummary) {
            countSummary.innerHTML = `Tìm thấy <strong>${this.videos.length}</strong> video | Đã chọn: <strong class="text-success">${selectedCount}</strong> video`;
        }
        if (submitBtn) {
            submitBtn.disabled = selectedCount === 0 || this.isUploading;
        }
    }

    setAllSelected(checked) {
        this.videos.forEach((v) => {
            if (!v.alreadyInCourse && v.status !== "already") {
                v.selected = checked;
            }
        });
        this.renderTable();
    }

    toggleAll() {
        const active = this.videos.filter((v) => !v.alreadyInCourse && v.status !== "already");
        const allChecked = active.every((v) => v.selected);
        this.setAllSelected(!allChecked);
    }

    showAlert(msg, type = "info") {
        const alertEl = document.getElementById("tdb_modal_alert");
        if (!alertEl) return;
        alertEl.className = `alert alert-${type} py-2 small`;
        alertEl.innerText = msg;
        alertEl.classList.remove("d-none");
    }

    async submitSelected() {
        const toProcess = this.videos.filter((v) => v.selected && !v.alreadyInCourse && v.status !== "already");
        if (!toProcess.length) {
            this.showAlert("Vui lòng tích chọn ít nhất 1 video!", "warning");
            return;
        }

        this.isUploading = true;
        this.updateSelectionSummary();

        // Kiểm tra xem có video nào cần tải file lên từ trình duyệt không
        const filesToUpload = toProcess.filter((v) => !v.isExistingOnDisk && v.file);
        const existingOnDisk = toProcess.filter((v) => v.isExistingOnDisk);

        try {
            // 1. Thêm các video đã có sẵn trên đĩa
            if (existingOnDisk.length > 0) {
                this.showAlert(`Đang thêm ${existingOnDisk.length} video có sẵn vào khóa học...`, "info");
                const payload = existingOnDisk.map((v) => ({
                    filename: v.filename,
                    title: v.title,
                    category_id: v.categoryId === "new" ? 0 : (parseInt(v.categoryId, 10) || 0),
                    category_name: v.categoryId === "new" ? (v.categoryName || "") : "",
                    duration_minutes: v.durationMinutes || 15,
                    description: v.description || "",
                }));
                const res = await rpc("/slides/add_disk_videos_to_channel", {
                    channel_id: this.channelId,
                    videos: payload,
                    category_id: this.categoryId,
                });
                if (res.error) {
                    throw new Error(res.error);
                }

                // Tự động tải lên tài liệu đính kèm nếu có
                if (res.slide_ids) {
                    for (const v of existingOnDisk) {
                        const sId = res.slide_ids[v.filename];
                        if (v.resourceFile && sId) {
                            await this.uploadResourceFile(sId, v.resourceFile);
                        }
                    }
                }
            }

            // 2. Tải lên các video từ máy tính nếu có
            if (filesToUpload.length > 0) {
                const progContainer = document.getElementById("tdb_modal_progress_container");
                const progText = document.getElementById("tdb_modal_progress_text");
                const progBar = document.getElementById("tdb_modal_progress_bar");
                const progPercent = document.getElementById("tdb_modal_progress_percent");
                if (progContainer) progContainer.classList.remove("d-none");

                const total = filesToUpload.length;
                for (let i = 0; i < total; i++) {
                    const item = filesToUpload[i];
                    item.status = "uploading";
                    this.renderTable();

                    if (progText) progText.innerText = `Đang tải lên file ${i + 1}/${total}: ${item.filename}`;

                    const createdSlideId = await this.uploadSingleChunked(item, (filePercent) => {
                        item.progress = filePercent;
                        const overall = Math.round(((i + filePercent / 100) / total) * 100);
                        if (progBar) progBar.style.width = overall + "%";
                        if (progPercent) progPercent.innerText = overall + "%";
                    });

                    // Tự động tải lên tài liệu đính kèm nếu có
                    if (item.resourceFile && createdSlideId) {
                        await this.uploadResourceFile(createdSlideId, item.resourceFile);
                    }

                    item.status = "done";
                    item.progress = 100;
                    this.renderTable();
                }
            }

            this.showAlert("Đã thêm thành công các bài học video vào khóa học! Đang làm mới trang...", "success");

            setTimeout(() => {
                window.location.reload();
            }, 1200);

        } catch (err) {
            this.isUploading = false;
            this.updateSelectionSummary();
            this.showAlert("Lỗi: " + (err.message || err), "danger");
        }
    }

    async uploadResourceFile(slideId, resourceFile) {
        if (!slideId || !resourceFile) return;
        try {
            const formData = new FormData();
            formData.append("slide_id", slideId);
            formData.append("file", resourceFile, resourceFile.name);
            formData.append("name", resourceFile.name);
            if (window.odoo && window.odoo.csrf_token) {
                formData.append("csrf_token", window.odoo.csrf_token);
            }
            await fetch("/slides/resource/upload", {
                method: "POST",
                body: formData,
            });
        } catch (err) {
            console.warn("Lỗi tải lên tài liệu đính kèm:", err);
        }
    }

    uploadSingleChunked(item, onProgress) {
        return new Promise((resolve, reject) => {
            const file = item.file;
            const CHUNK_SIZE = 5 * 1024 * 1024;
            const totalChunks = Math.ceil(file.size / CHUNK_SIZE) || 1;
            const uploadId = Date.now() + "_" + Math.random().toString(36).substring(2, 8);
            let chunkIdx = 0;
            let finalSlideId = null;

            const sendNext = () => {
                if (chunkIdx >= totalChunks) {
                    onProgress(100);
                    resolve(finalSlideId);
                    return;
                }

                const start = chunkIdx * CHUNK_SIZE;
                const end = Math.min(start + CHUNK_SIZE, file.size);
                const blob = file.slice(start, end);

                const formData = new FormData();
                formData.append("upload_id", uploadId);
                formData.append("channel_id", this.channelId);
                formData.append("chunk_index", chunkIdx);
                formData.append("total_chunks", totalChunks);
                formData.append("filename", item.filename);
                formData.append("lesson_name", item.title || "");
                formData.append("folder_name", this.folderPath || "");
                const catId = item.categoryId === "new" ? 0 : (parseInt(item.categoryId, 10) || parseInt(this.categoryId, 10) || 0);
                if (catId) {
                    formData.append("category_id", catId);
                }
                if (item.categoryId === "new" && item.categoryName) {
                    formData.append("category_name", item.categoryName);
                }
                formData.append("duration_minutes", item.durationMinutes || 15);
                formData.append("description", item.description || "");
                formData.append("chunk", blob, item.filename);
                if (window.odoo && window.odoo.csrf_token) {
                    formData.append("csrf_token", window.odoo.csrf_token);
                }

                const xhr = new XMLHttpRequest();
                xhr.open("POST", "/slides/upload_video_chunk", true);

                xhr.upload.onprogress = (e) => {
                    if (e.lengthComputable) {
                        const chunkProgress = e.loaded / e.total;
                        const overall = Math.min(99, Math.round(((chunkIdx + chunkProgress) / totalChunks) * 100));
                        onProgress(overall);
                    }
                };

                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const res = JSON.parse(xhr.responseText);
                            if (res.error) {
                                reject(new Error(res.error));
                            } else {
                                if (res.slide_id) {
                                    finalSlideId = res.slide_id;
                                }
                                chunkIdx++;
                                sendNext();
                            }
                        } catch {
                            reject(new Error("Lỗi đọc dữ liệu máy chủ"));
                        }
                    } else {
                        try {
                            const errRes = JSON.parse(xhr.responseText);
                            if (errRes && errRes.error) {
                                reject(new Error(errRes.error));
                                return;
                            }
                        } catch {
                            // not json
                        }
                        reject(new Error("Máy chủ phản hồi mã lỗi: " + xhr.status));
                    }
                };

                xhr.onerror = () => reject(new Error("Lỗi mạng khi tải lên"));
                xhr.send(formData);
            };

            sendNext();
        });
    }
}

// Bắt sự kiện click vào nút 'Thêm video từ thư mục ổ đĩa' trên trang website khóa học
document.addEventListener("click", (e) => {
    const btn = e.target.closest(".tdb_btn_open_disk_video_modal");
    if (!btn) return;
    e.preventDefault();

    const channelId = btn.dataset.channelId;
    const channelName = btn.dataset.channelName;
    const folderPath = btn.dataset.folderPath;
    const folderDisplay = btn.dataset.folderDisplay;
    const categoryId = btn.dataset.categoryId || null;

    new WebsiteDiskVideoManager(channelId, channelName, folderPath, folderDisplay, categoryId);
});

// Điều chỉnh lại câu từ hộp thoại khi bấm biểu tượng thùng rác xóa bài học trên website
patch(SlideArchive.prototype, {
    openDialog() {
        const slideId = this.el.dataset.slideId;
        this.services.dialog.add(ConfirmationDialog, {
            title: _t("Xóa bài học"),
            body: _t("Bạn có chắc chắn muốn xóa bài học này khỏi khóa học không?"),
            confirmLabel: _t("Xóa"),
            cancelLabel: _t("Hủy bỏ"),
            confirmClass: "btn-danger",
            confirm: async () => {
                const isArchived = await this.waitFor(
                    rpc("/slides/slide/archive", { slide_id: slideId })
                );
                if (isArchived) {
                    this.el.closest(".o_wslides_slides_list_slide")?.remove();
                    const categories = document.querySelectorAll(".o_wslides_slide_list_category");
                    for (const category of categories) {
                        const categoryHeaderEl = category.querySelector(".o_wslides_slide_list_category_header");
                        const categorySlideEl = category.querySelector(".o_wslides_slides_list_slide:not(.o_not_editable)");
                        const emptyFlagContainerEl = categoryHeaderEl?.querySelector(".o_wslides_slides_list_drag");
                        const emptyFlagEl = emptyFlagContainerEl?.querySelector("small");

                        if (!categorySlideEl && !emptyFlagEl && emptyFlagContainerEl) {
                            const smallEl = document.createElement("small");
                            smallEl.classList.add("ms-1", "text-muted", "fw-bold");
                            smallEl.innerText = _t("(empty)");
                            this.insert(smallEl, emptyFlagContainerEl);
                        }
                    }
                }
            },
            cancel: () => {},
        });
    },
});

// ==================== TẠO BÀI TRẮC NGHIỆM NHANH (QUICK QUIZ NHƯ GOOGLE FORM) ====================
class WebsiteQuickQuizManager {
    constructor(channelId, channelName, categoryId = null) {
        this.channelId = parseInt(channelId, 10);
        this.channelName = channelName || "Khóa học";
        this.categoryId = categoryId ? parseInt(categoryId, 10) : 0;
        this.categories = [];
        this.videos = [];
        this.modalEl = null;
        this.questions = [
            {
                question: "Nội dung câu hỏi số 1...",
                question_type: "single",
                answers: [
                    { text: "Đáp án 1", is_correct: true, comment: "" },
                    { text: "Đáp án 2", is_correct: false, comment: "" },
                    { text: "Đáp án 3", is_correct: false, comment: "" },
                    { text: "Đáp án 4", is_correct: false, comment: "" },
                ],
            },
        ];

        this.init();
    }

    async init() {
        try {
            const data = await rpc("/slides/get_channel_disk_videos", { channel_id: this.channelId });
            if (data) {
                if (data.categories) this.categories = data.categories;
                if (data.videos) this.videos = data.videos;
            }
        } catch (e) {}

        this.initModal();
    }

    initModal() {
        const existing = document.getElementById("tdb_quick_quiz_modal");
        if (existing) existing.remove();

        let catOptions = `<option value="0">-- Mặc định (Tạo ở đầu khóa học) --</option>`;
        this.categories.forEach((c) => {
            const sel = String(c.id) === String(this.categoryId) ? "selected" : "";
            catOptions += `<option value="${c.id}" ${sel}>${this.escapeHtml(c.name)}</option>`;
        });

        let videoOptions = `<option value="0">-- Tự động (Theo video đứng trước bài này) --</option>`;
        this.videos.forEach((v) => {
            if (v.slide_id) {
                videoOptions += `<option value="${v.slide_id}">${this.escapeHtml(v.title || v.filename)}</option>`;
            }
        });

        const modalHtml = `
        <div class="modal fade show" id="tdb_quick_quiz_modal" tabindex="-1" style="display: block; background: rgba(0,0,0,0.5); z-index: 1055;" aria-modal="true" role="dialog">
            <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
                <div class="modal-content border-0 shadow-lg" style="border-radius: 12px; overflow: hidden;">
                    <div class="modal-header bg-light py-3 border-bottom">
                        <div>
                            <h5 class="modal-title fw-bold text-dark mb-1">Tạo Bài Trắc Nghiệm (Quiz)</h5>
                            <div class="text-secondary small">
                                Khóa học: <strong class="text-dark">${this.escapeHtml(this.channelName)}</strong>
                            </div>
                        </div>
                        <button type="button" class="btn-close" id="tdb_quiz_btn_close" aria-label="Close"></button>
                    </div>
                    <div class="modal-body p-4" style="max-height: 70vh;">
                        <div class="row g-3 mb-3">
                            <div class="col-md-6">
                                <label class="form-label small fw-bold text-dark mb-1">Tiêu đề bài kiểm tra:</label>
                                <input type="text" class="form-control form-control-sm" id="tdb_quiz_title" value="Bài kiểm tra trắc nghiệm" placeholder="Nhập tên bài kiểm tra..."/>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label small fw-bold text-dark mb-1">Chương / Phần học:</label>
                                <select class="form-select form-select-sm" id="tdb_quiz_category">
                                    ${catOptions}
                                </select>
                            </div>
                            <div class="col-12">
                                <label class="form-label small fw-bold text-dark mb-1">
                                    Điều kiện tiên quyết mở khóa Quiz:
                                </label>
                                <select class="form-select form-select-sm" id="tdb_quiz_prereq_mode">
                                    <option value="all_chapter" selected>⭐ Bắt buộc hoàn thành TẤT CẢ video trong chương này (Khuyên dùng)</option>
                                    <option value="single">Chỉ bắt buộc một video cụ thể...</option>
                                    <option value="none">Không yêu cầu tiên quyết (Mở tự do cho học viên)</option>
                                </select>
                                <div id="tdb_quiz_prereq_single_wrap" class="mt-2 d-none">
                                    <label class="form-label small text-muted mb-1">Chọn video cụ thể:</label>
                                    <select class="form-select form-select-sm" id="tdb_quiz_prereq_video">
                                        ${videoOptions}
                                    </select>
                                </div>
                                <div id="tdb_quiz_prereq_help" class="form-text small text-primary mt-1 fw-bold">
                                    ⭐ Học viên bắt buộc phải xem xong toàn bộ các video bài học của chương này mới được mở khóa vào làm bài kiểm tra.
                                </div>
                            </div>
                        </div>

                        <div class="d-flex align-items-center justify-content-between mb-3 pb-2 border-bottom">
                            <span class="fw-bold text-dark">Danh sách câu hỏi &amp; Phương án</span>
                            <span class="text-muted small">Tùy biến số lượng phương án và chọn 1 hoặc nhiều đáp án đúng</span>
                        </div>

                        <div id="tdb_quiz_builder_container"></div>

                        <button type="button" class="btn btn-outline-primary btn-sm w-100 my-2 fw-bold py-2 border-dashed" id="tdb_quiz_btn_add_q">
                            + Thêm câu hỏi mới
                        </button>

                        <div id="tdb_quiz_alert" class="alert alert-danger py-2 small d-none mt-2"></div>
                    </div>
                    <div class="modal-footer bg-light py-2">
                        <button type="button" class="btn btn-secondary btn-sm px-3" id="tdb_quiz_btn_cancel">Đóng</button>
                        <button type="button" class="btn btn-primary btn-sm px-4 fw-bold" id="tdb_quiz_btn_submit">
                            Lưu bài trắc nghiệm
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML("beforeend", modalHtml);
        this.modalEl = document.getElementById("tdb_quick_quiz_modal");

        this.bindEvents();
        this.renderQuestions();
    }

    escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    bindEvents() {
        const closeBtn = document.getElementById("tdb_quiz_btn_close");
        const cancelBtn = document.getElementById("tdb_quiz_btn_cancel");
        if (closeBtn) closeBtn.onclick = () => this.close();
        if (cancelBtn) cancelBtn.onclick = () => this.close();

        const addQBtn = document.getElementById("tdb_quiz_btn_add_q");
        if (addQBtn) {
            addQBtn.onclick = () => {
                this.questions.push({
                    question: `Câu hỏi số ${this.questions.length + 1}...`,
                    question_type: "single",
                    answers: [
                        { text: "Đáp án 1", is_correct: true, comment: "" },
                        { text: "Đáp án 2", is_correct: false, comment: "" },
                        { text: "Đáp án 3", is_correct: false, comment: "" },
                        { text: "Đáp án 4", is_correct: false, comment: "" },
                    ],
                });
                this.renderQuestions();
            };
        }

        const submitBtn = document.getElementById("tdb_quiz_btn_submit");
        if (submitBtn) {
            submitBtn.onclick = () => this.submitQuiz();
        }

        const modeSel = document.getElementById("tdb_quiz_prereq_mode");
        const singleWrap = document.getElementById("tdb_quiz_prereq_single_wrap");
        const helpEl = document.getElementById("tdb_quiz_prereq_help");
        const catSel = document.getElementById("tdb_quiz_category");

        const updatePrereqHelp = () => {
            const val = modeSel ? modeSel.value : "all_chapter";
            const selCat = catSel ? catSel.options[catSel.selectedIndex]?.text : "chương này";
            if (singleWrap) singleWrap.classList.toggle("d-none", val !== "single");
            if (helpEl) {
                if (val === "all_chapter") {
                    helpEl.innerText = `⭐ Học viên bắt buộc phải xem xong toàn bộ các video bài học của ${selCat} mới được mở khóa vào làm bài kiểm tra.`;
                    helpEl.className = "form-text small text-primary mt-1 fw-bold";
                } else if (val === "single") {
                    helpEl.innerText = "Học viên chỉ cần xem xong video được chọn bên dưới là sẽ được mở khóa làm bài kiểm tra.";
                    helpEl.className = "form-text small text-muted mt-1";
                } else {
                    helpEl.innerText = "Bài kiểm tra mở tự do, học viên có thể vào làm ngay mà không cần xem trước video.";
                    helpEl.className = "form-text small text-success mt-1";
                }
            }
        };

        if (modeSel) modeSel.onchange = updatePrereqHelp;
        if (catSel) catSel.onchange = updatePrereqHelp;
    }

    close() {
        if (this.modalEl) {
            this.modalEl.remove();
            this.modalEl = null;
        }
    }

    renderQuestions() {
        const container = document.getElementById("tdb_quiz_builder_container");
        if (!container) return;

        let html = "";
        this.questions.forEach((q, qIdx) => {
            const isMulti = q.question_type === "multiple";
            html += `
            <div class="card mb-3 border bg-white shadow-sm" style="border-radius: 8px;" data-qidx="${qIdx}">
                <div class="card-header bg-light py-2 d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-secondary">Câu ${qIdx + 1}</span>
                        <select class="form-select form-select-sm py-0 tdb-q-type" data-qidx="${qIdx}" style="width: auto; font-size: 12px; height: 26px;">
                            <option value="single" ${!isMulti ? "selected" : ""}>Một đáp án đúng (Radio)</option>
                            <option value="multiple" ${isMulti ? "selected" : ""}>Nhiều đáp án đúng (Checkbox)</option>
                        </select>
                    </div>
                    ${this.questions.length > 1 ? `<button type="button" class="btn btn-link text-danger btn-sm p-0 text-decoration-none tdb-del-q" data-qidx="${qIdx}">Xóa câu này</button>` : ""}
                </div>
                <div class="card-body p-3">
                    <div class="mb-2">
                        <label class="form-label small text-muted mb-1">Nội dung câu hỏi:</label>
                        <input type="text" class="form-control form-control-sm tdb-q-title"
                               data-qidx="${qIdx}" value="${this.escapeHtml(q.question)}" placeholder="Nhập câu hỏi..."/>
                    </div>

                    <div class="d-flex align-items-center justify-content-between mb-2">
                        <label class="form-label small text-muted mb-0">
                            Các phương án trả lời (${isMulti ? "tích chọn các ô vuông đáp án đúng" : "chọn 1 nút tròn đáp án đúng"}):
                        </label>
                        <button type="button" class="btn btn-outline-success btn-sm py-0 px-2 tdb-add-ans-btn" data-qidx="${qIdx}" style="font-size: 11px;">
                            + Thêm phương án
                        </button>
                    </div>

                    <div class="row g-2 tdb-ans-container">`;

            q.answers.forEach((ans, aIdx) => {
                const inputType = isMulti ? "checkbox" : "radio";
                const inputName = isMulti ? `modal_ans_multi_${qIdx}_${aIdx}` : `modal_ans_single_${qIdx}`;
                html += `
                <div class="col-12">
                    <div class="input-group input-group-sm">
                        <div class="input-group-text bg-white">
                            <input type="${inputType}" name="${inputName}" class="form-check-input mt-0 tdb-ans-check"
                                   data-qidx="${qIdx}" data-aidx="${aIdx}" ${ans.is_correct ? "checked" : ""}
                                   title="Tích để chọn đây là đáp án đúng"/>
                        </div>
                        <input type="text" class="form-control tdb-ans-text"
                               data-qidx="${qIdx}" data-aidx="${aIdx}" value="${this.escapeHtml(ans.text)}" placeholder="Đáp án ${aIdx + 1}..."/>
                        ${q.answers.length > 2 ? `
                        <button class="btn btn-outline-danger tdb-del-ans-btn" type="button" data-qidx="${qIdx}" data-aidx="${aIdx}" title="Xóa phương án này">
                            &times;
                        </button>` : ""}
                    </div>
                </div>`;
            });

            html += `
                    </div>
                </div>
            </div>`;
        });

        container.innerHTML = html;

        // Binds
        container.querySelectorAll(".tdb-q-title").forEach((inp) => {
            inp.oninput = (e) => {
                this.questions[e.target.dataset.qidx].question = e.target.value;
            };
        });

        container.querySelectorAll(".tdb-q-type").forEach((sel) => {
            sel.onchange = (e) => {
                const qIdx = parseInt(e.target.dataset.qidx, 10);
                const newType = e.target.value;
                this.questions[qIdx].question_type = newType;
                if (newType === "single") {
                    let found = false;
                    this.questions[qIdx].answers.forEach((a) => {
                        if (a.is_correct && !found) {
                            found = true;
                        } else {
                            a.is_correct = false;
                        }
                    });
                    if (!found && this.questions[qIdx].answers.length > 0) {
                        this.questions[qIdx].answers[0].is_correct = true;
                    }
                }
                this.renderQuestions();
            };
        });

        container.querySelectorAll(".tdb-ans-check").forEach((input) => {
            input.onchange = (e) => {
                const qIdx = parseInt(e.target.dataset.qidx, 10);
                const aIdx = parseInt(e.target.dataset.aidx, 10);
                const q = this.questions[qIdx];
                if (q.question_type === "single") {
                    q.answers.forEach((a, i) => {
                        a.is_correct = (i === aIdx);
                    });
                } else {
                    q.answers[aIdx].is_correct = e.target.checked;
                }
            };
        });

        container.querySelectorAll(".tdb-ans-text").forEach((inp) => {
            inp.oninput = (e) => {
                const qIdx = parseInt(e.target.dataset.qidx, 10);
                const aIdx = parseInt(e.target.dataset.aidx, 10);
                this.questions[qIdx].answers[aIdx].text = e.target.value;
            };
        });

        container.querySelectorAll(".tdb-add-ans-btn").forEach((btn) => {
            btn.onclick = (e) => {
                const qIdx = parseInt(e.currentTarget.dataset.qidx, 10);
                const nextLetter = String.fromCharCode(65 + this.questions[qIdx].answers.length);
                this.questions[qIdx].answers.push({
                    text: `Đáp án ${this.questions[qIdx].answers.length + 1}`,
                    is_correct: false,
                    comment: "",
                });
                this.renderQuestions();
            };
        });

        container.querySelectorAll(".tdb-del-ans-btn").forEach((btn) => {
            btn.onclick = (e) => {
                const qIdx = parseInt(e.currentTarget.dataset.qidx, 10);
                const aIdx = parseInt(e.currentTarget.dataset.aidx, 10);
                if (this.questions[qIdx].answers.length > 2) {
                    this.questions[qIdx].answers.splice(aIdx, 1);
                    this.renderQuestions();
                }
            };
        });

        container.querySelectorAll(".tdb-del-q").forEach((btn) => {
            btn.onclick = (e) => {
                const qIdx = parseInt(e.currentTarget.dataset.qidx, 10);
                this.questions.splice(qIdx, 1);
                this.renderQuestions();
            };
        });
    }

    async submitQuiz() {
        const title = (document.getElementById("tdb_quiz_title")?.value || "").trim();
        const categoryId = parseInt(document.getElementById("tdb_quiz_category")?.value || "0", 10);
        const alertEl = document.getElementById("tdb_quiz_alert");
        const submitBtn = document.getElementById("tdb_quiz_btn_submit");

        if (!title) {
            if (alertEl) {
                alertEl.innerText = "Vui lòng nhập tiêu đề bài kiểm tra!";
                alertEl.classList.remove("d-none");
            }
            return;
        }

        // Kiểm tra tính hợp lệ của từng câu hỏi
        for (let i = 0; i < this.questions.length; i++) {
            const q = this.questions[i];
            if (!q.question.trim()) {
                if (alertEl) {
                    alertEl.innerText = `Câu hỏi số ${i + 1} chưa có nội dung!`;
                    alertEl.classList.remove("d-none");
                }
                return;
            }
            const validAnswers = q.answers.filter((a) => a.text.trim());
            if (validAnswers.length < 2) {
                if (alertEl) {
                    alertEl.innerText = `Câu hỏi số ${i + 1} phải có ít nhất 2 phương án trả lời!`;
                    alertEl.classList.remove("d-none");
                }
                return;
            }
            const correctAnswers = q.answers.filter((a) => a.is_correct);
            const incorrectAnswers = q.answers.filter((a) => !a.is_correct);
            if (correctAnswers.length === 0) {
                if (alertEl) {
                    alertEl.innerText = `Câu hỏi số ${i + 1} bắt buộc phải có ít nhất 1 đáp án đúng!`;
                    alertEl.classList.remove("d-none");
                }
                return;
            }
            if (incorrectAnswers.length === 0) {
                if (alertEl) {
                    alertEl.innerText = `Câu hỏi số ${i + 1} bắt buộc phải có ít nhất 1 phương án sai!`;
                    alertEl.classList.remove("d-none");
                }
                return;
            }
        }

        submitBtn.disabled = true;
        if (alertEl) alertEl.classList.add("d-none");

        const prereqMode = document.getElementById("tdb_quiz_prereq_mode")?.value || "all_chapter";
        let prereqVideoId = null;
        if (prereqMode === "single") {
            prereqVideoId = parseInt(document.getElementById("tdb_quiz_prereq_video")?.value || "0", 10) || null;
        } else if (prereqMode === "none") {
            prereqVideoId = "none";
        } else {
            prereqVideoId = "all_chapter";
        }

        try {
            const res = await rpc("/slides/quiz/quick_create", {
                channel_id: this.channelId,
                lesson_title: title,
                category_id: categoryId,
                prerequisite_mode: prereqMode,
                prerequisite_video_id: prereqVideoId,
                questions: this.questions,
            });

            if (res.error) {
                throw new Error(res.error);
            }

            if (alertEl) {
                alertEl.className = "alert alert-success py-2 small";
                alertEl.innerText = `Đã tạo thành công bài trắc nghiệm với ${res.created_questions_count} câu hỏi! Đang làm mới...`;
                alertEl.classList.remove("d-none");
            }

            setTimeout(() => {
                window.location.reload();
            }, 1200);
        } catch (err) {
            submitBtn.disabled = false;
            if (alertEl) {
                alertEl.className = "alert alert-danger py-2 small";
                alertEl.innerText = "Lỗi: " + (err.message || err);
                alertEl.classList.remove("d-none");
            }
        }
    }
}


// Bắt sự kiện click tạo bài Quiz nhanh trên giao diện website
document.addEventListener("click", (e) => {
    const btn = e.target.closest(".tdb_btn_open_quick_quiz_modal");
    if (!btn) return;
    e.preventDefault();

    const channelId = btn.dataset.channelId;
    const channelName = btn.dataset.channelName;
    const categoryId = btn.dataset.categoryId || null;

    new WebsiteQuickQuizManager(channelId, channelName, categoryId);
});

// Lắng nghe sự kiện hoàn thành bài học từ video player (khi xem >= 90%)
window.addEventListener("message", (event) => {
    if (event.data && (event.data.type === "slide_completed" || event.data.type === "tdb_slide_completed")) {
        const slideId = event.data.slideId || event.data.slide_id;
        const completeBtn = document.querySelector(`.o_wslides_button_complete[data-slide-id="${slideId}"]`);
        if (completeBtn && !completeBtn.classList.contains("o_wslides_button_completed")) {
            completeBtn.click();
        }
        // Đánh dấu completed trên sidebar
        const activeItem = document.querySelector(".o_wslides_fs_sidebar_list_item.active");
        if (activeItem) {
            activeItem.classList.add("completed");
        }
    }
});

// ==================== KHÓA PHÍM MŨI TÊN NHẢY CÓC BÀI HỌC (ANTI-SKIP LESSON) ====================
let tdbFsToastTimeout = null;
function showFullscreenAntiSkipToast(message) {
    let toast = document.getElementById("tdb_fs_anti_skip_toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "tdb_fs_anti_skip_toast";
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.96);
            color: #ffffff;
            border: 1px solid rgba(239, 68, 68, 0.7);
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            z-index: 999999;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            display: none;
            transition: opacity 0.2s ease;
            pointer-events: none;
        `;
        document.body.appendChild(toast);
    }
    toast.innerText = message;
    toast.style.display = "block";
    toast.style.opacity = "1";
    if (tdbFsToastTimeout) clearTimeout(tdbFsToastTimeout);
    tdbFsToastTimeout = setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => { toast.style.display = "none"; }, 200);
    }, 2800);
}

// Chặn phím mũi tên tua / nhảy bài học ở tầng capturing cao nhất
window.addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight") {
        const fsMain = document.querySelector(".o_wslides_fs_main");
        if (fsMain) {
            // Kiểm tra xem bài hiện tại có iframe video bài giảng không
            const iframe = document.querySelector("iframe.o_wslides_iframe_viewer") || document.querySelector("iframe[src*='/slides/embed/local_video/']");
            if (iframe) {
                // Kiểm tra xem bài học hiện tại đã hoàn thành hay chưa
                const activeItem = document.querySelector(".o_wslides_fs_sidebar_list_item.active");
                const isCompleted = activeItem && (
                    activeItem.querySelector(".oi-check") ||
                    activeItem.querySelector(".fa-check-circle") ||
                    activeItem.classList.contains("completed") ||
                    activeItem.querySelector(".text-success")
                );

                if (!isCompleted) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    showFullscreenAntiSkipToast("Vui lòng xem tối thiểu 90% video bài học hiện tại để nắm vững kiến thức trước khi chuyển sang bài tiếp theo!");
                    return false;
                }
            }
        }
    }
}, true);


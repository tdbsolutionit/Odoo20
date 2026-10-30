/** @odoo-module **/

import { Component, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

export class SlideVideoFolderUploader extends Component {
    static template = "tdb_slides_custom.SlideVideoFolderUploader";
    props = useProps(standardWidgetProps);

    setup() {
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = proxy({
            folderName: "",
            categories: [],
            videos: [],
            isUploading: false,
            currentUploadIndex: 0,
            currentUploadName: "",
            currentFilePercent: 0,
            overallPercent: 0,
            uploadError: "",
            showList: false,
        });
    }

    get channelId() {
        const record = this.props?.record;
        if (record) {
            if (record.resId) return record.resId;
            if (record.data && record.data.id) return record.data.id;
            if (record.config && record.config.resId) return record.config.resId;
            if (record.evalContext && record.evalContext.id) return record.evalContext.id;
        }
        if (typeof window !== "undefined" && window.location) {
            const pathMatch = window.location.pathname.match(/\/odoo\/e-learning\/(\d+)/);
            if (pathMatch && pathMatch[1]) return parseInt(pathMatch[1], 10);

            const hashMatch = window.location.hash.match(/id=(\d+)/);
            if (hashMatch && hashMatch[1]) return parseInt(hashMatch[1], 10);

            const searchMatch = window.location.search.match(/id=(\d+)/);
            if (searchMatch && searchMatch[1]) return parseInt(searchMatch[1], 10);
        }
        return 0;
    }

    get channelName() {
        const record = this.props?.record;
        return (record && record.data) ? (record.data.name || "") : "";
    }

    get courseFolderPath() {
        const record = this.props?.record;
        return (record && record.data) ? (record.data.video_folder_path || "") : "";
    }

    get courseFolderDiskDisplay() {
        const record = this.props?.record;
        if (record && record.data && record.data.video_folder_disk_display) {
            return record.data.video_folder_disk_display;
        }
        const raw = this.courseFolderPath || this.state.folderName;
        if (!raw) return "";
        if (raw.includes(":") || raw.startsWith("/") || raw.startsWith("\\")) {
            return raw;
        }
        return "C:\\Work\\odoo20-docker\\videos\\" + raw;
    }

    get hasLinkedFolder() {
        return Boolean(this.courseFolderPath || this.state.folderName);
    }

    get currentFolderDisplay() {
        return this.courseFolderDiskDisplay || "";
    }

    get selectedCount() {
        return this.state.videos.filter((v) => v.selected && !v.alreadyInCourse && v.status !== "already").length;
    }

    get allSelected() {
        const active = this.state.videos.filter((v) => !v.alreadyInCourse && v.status !== "already");
        return active.length > 0 && active.every((v) => v.selected);
    }

    isItemChecked(item) {
        return Boolean(item && item.selected && !item.alreadyInCourse);
    }

    onDurationInput(item, ev) {
        const val = parseFloat(ev.target.value);
        item.durationMinutes = isNaN(val) ? 15 : val;
    }

    onResourceFileChange(item, ev) {
        const files = ev.target.files;
        if (files && files.length > 0) {
            item.resourceFile = files[0];
        } else {
            item.resourceFile = null;
        }
    }

    clearResourceFile(item) {
        item.resourceFile = null;
    }

    async uploadAttachedResource(slideId, resourceFile) {
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

    formatSize(bytes) {
        if (!bytes) return "0 B";
        const mb = bytes / (1024 * 1024);
        if (mb >= 1024) {
            return (mb / 1024).toFixed(2) + " GB";
        }
        return mb.toFixed(1) + " MB";
    }

    cleanTitle(filename) {
        const lastDot = filename.lastIndexOf(".");
        const base = lastDot > 0 ? filename.substring(0, lastDot) : filename;
        return base
            .replace(/[_\-]+/g, " ")
            .trim()
            .replace(/\b\w/g, (c) => c.toUpperCase());
    }

    async scanDiskFolder() {
        if (!this.channelId) {
            this.notification.add(_t("Vui lòng lưu khóa học trước khi quét thư mục!"), { type: "warning" });
            return;
        }

        try {
            const data = await rpc("/slides/get_channel_disk_videos", {
                channel_id: this.channelId,
            });

            if (data.error) {
                this.notification.add(data.error, { type: "danger" });
                return;
            }

            this.state.categories = data.categories || [];
            const rawVideos = data.videos || [];
            if (!rawVideos.length) {
                this.notification.add(
                    _t("Không tìm thấy file video nào trong thư mục ổ đĩa của khóa học!"),
                    { type: "warning" }
                );
                return;
            }

            const list = rawVideos.map((v, idx) => ({
                id: idx + 1,
                slideId: v.slide_id || 0,
                isExistingOnDisk: true,
                filename: v.filename,
                title: v.title,
                size: 0,
                sizeStr: v.size_str,
                diskFolderPath: data.folder_display || this.currentFolderDisplay,
                alreadyInCourse: v.already_in_course,
                selected: !v.already_in_course,
                status: v.already_in_course ? "already" : "ready",
                categoryId: v.category_id || 0,
                categoryName: v.category_name || "",
                durationMinutes: v.duration_minutes || 15,
                description: v.description || "",
                resourceFile: null,
                showDetails: false,
                isSaving: false,
                progress: 0,
            }));

            this.state.folderName = data.folder_name || this.state.folderName;
            this.state.videos = list;
            this.state.showList = true;
            this.state.isUploading = false;
            this.state.uploadError = "";

            const newCount = list.filter((v) => !v.alreadyInCourse).length;
            this.notification.add(
                _t("Đã quét xong: Tìm thấy %s video (%s video mới sẵn sàng đưa vào khóa học).")
                    .replace("%s", list.length)
                    .replace("%s", newCount),
                { type: "success" }
            );
        } catch (err) {
            this.notification.add(_t("Lỗi khi quét thư mục: ") + (err.message || err), { type: "danger" });
        }
    }

    async updateExistingLesson(item) {
        if (!item) return;
        item.isSaving = true;
        try {
            const chId = this.channelId;
            const res = await rpc("/slides/update_lesson_details", {
                slide_id: item.slideId || 0,
                filename: item.filename,
                channel_id: chId,
                title: item.title,
                category_id: item.categoryId === "new" ? 0 : (parseInt(item.categoryId, 10) || 0),
                category_name: item.categoryId === "new" ? (item.categoryName || "") : "",
                description: item.description || "",
                duration_minutes: item.durationMinutes || 15,
            });

            if (res.error) {
                throw new Error(res.error);
            }

            if (res.slide_id) {
                item.slideId = res.slide_id;
            }
            if (res.category_id) {
                item.categoryId = res.category_id;
            }
            if (res.category_name) {
                item.categoryName = res.category_name;
            }
            if (res.categories && res.categories.length) {
                this.state.categories = res.categories;
            }

            // Tải lên tài liệu đính kèm nếu có file mới được chọn
            if (item.resourceFile && item.slideId) {
                await this.uploadAttachedResource(item.slideId, item.resourceFile);
            }

            this.notification.add(
                _t("Đã cập nhật bài học '%s' thành công!").replace("%s", item.title || item.filename),
                { type: "success" }
            );

            // Nạp lại form khóa học để cập nhật thứ tự bài học trong danh mục
            try {
                if (this.props.record && typeof this.props.record.load === "function") {
                    await this.props.record.load();
                }
            } catch (e) {}
            try {
                this.action.doAction({ type: "ir.actions.client", tag: "reload" });
            } catch (e) {}
        } catch (err) {
            this.notification.add(
                _t("Lỗi khi cập nhật bài học: ") + (err.message || err),
                { type: "danger" }
            );
        } finally {
            item.isSaving = false;
        }
    }

    triggerSelectFolder() {
        const input = document.createElement("input");
        input.type = "file";
        input.webkitdirectory = true;
        input.directory = true;
        input.multiple = true;
        input.onchange = (ev) => this.onFolderChange(ev);
        input.click();
    }

    triggerSelectFiles() {
        const input = document.createElement("input");
        input.type = "file";
        input.multiple = true;
        input.accept = "video/*,.mp4,.mkv,.avi,.mov,.webm,.flv,.m4v";
        input.onchange = (ev) => this.onFilesChange(ev);
        input.click();
    }

    async onFolderChange(ev) {
        const files = Array.from(ev.target.files || []);
        if (!files.length) return;

        let folderName = "";
        if (files[0].webkitRelativePath) {
            folderName = files[0].webkitRelativePath.split("/")[0];
        }
        if (!folderName) {
            folderName = "Thư mục máy tính";
        }

        this.state.folderName = folderName;

        // Lưu cố định thư mục này vào khóa học trên Odoo ngay lập tức
        if (this.props.record) {
            try {
                await this.props.record.update({ video_folder_path: folderName });
                if (typeof this.props.record.save === "function") {
                    await this.props.record.save();
                }
            } catch (err) {
                console.warn("Lưu thư mục vào khóa học:", err);
            }
        }

        const videoExts = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v"];
        const videoFiles = files.filter((f) => {
            const ext = f.name.substring(f.name.lastIndexOf(".")).toLowerCase();
            return videoExts.includes(ext);
        });

        if (videoFiles.length > 0) {
            this.populateVideos(videoFiles, folderName);
        } else {
            this.state.videos = [];
            this.state.showList = false;
            this.notification.add(
                _t("Đã lưu thư mục '%s' cho khóa học. Thư mục chưa có video, bạn có thể copy video vào thư mục rồi bấm 'Quét video có sẵn' hoặc bấm 'Chọn thêm video tải lên'!").replace("%s", folderName),
                { type: "info" }
            );
        }
    }

    async onFilesChange(ev) {
        const files = Array.from(ev.target.files || []);
        if (!files.length) return;

        const videoExts = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v"];
        const videoFiles = files.filter((f) => {
            const ext = f.name.substring(f.name.lastIndexOf(".")).toLowerCase();
            return videoExts.includes(ext);
        });

        if (!videoFiles.length) {
            this.notification.add(
                _t("Vui lòng chọn ít nhất một file video hợp lệ (.mp4, .mkv, .avi, .mov, .webm)!"),
                { type: "warning" }
            );
            return;
        }

        // Tự động dùng thư mục đã lưu của khóa học (người dùng không cần chọn lại thư mục)
        let folderName = this.courseFolderPath || this.state.folderName;
        if (!folderName) {
            folderName = this.channelName || "VideoKhoaHoc";
            this.state.folderName = folderName;
            if (this.props.record) {
                try {
                    await this.props.record.update({ video_folder_path: folderName });
                    if (typeof this.props.record.save === "function") {
                        await this.props.record.save();
                    }
                } catch (e) {
                    console.warn("Lưu thư mục mặc định:", e);
                }
            }
        }

        this.populateVideos(videoFiles, folderName);
    }

    populateVideos(videoFiles, folderName) {
        videoFiles.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: "base" }));

        // Nếu chưa có categories, tải danh mục từ khóa học
        if (this.channelId && (!this.state.categories || !this.state.categories.length)) {
            rpc("/slides/get_channel_disk_videos", { channel_id: this.channelId }).then((data) => {
                if (data && data.categories) {
                    this.state.categories = data.categories;
                }
            }).catch(() => {});
        }

        const diskFolder = this.currentFolderDisplay;
        const list = videoFiles.map((file, idx) => {
            const item = {
                id: idx + 1,
                file: file,
                isExistingOnDisk: false,
                filename: file.name,
                title: this.cleanTitle(file.name),
                size: file.size,
                sizeStr: this.formatSize(file.size),
                diskFolderPath: diskFolder,
                alreadyInCourse: false,
                selected: true,
                categoryId: 0,
                categoryName: "",
                durationMinutes: 15,
                description: "",
                resourceFile: null,
                showDetails: false,
                status: "ready", // ready, uploading, done, error
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

        this.state.folderName = folderName;
        this.state.videos = list;
        this.state.showList = true;
        this.state.isUploading = false;
        this.state.uploadError = "";
    }

    toggleSelectAll() {
        const active = this.state.videos.filter((v) => !v.alreadyInCourse && v.status !== "already");
        const nextState = !this.allSelected;
        for (const item of active) {
            if (item.status !== "done") {
                item.selected = nextState;
            }
        }
    }

    cancelSelection() {
        this.state.showList = false;
        this.state.videos = [];
        this.state.isUploading = false;
        this.state.uploadError = "";
    }

    async startUpload() {
        const toUpload = this.state.videos.filter(
            (v) => v.selected && !v.alreadyInCourse && v.status !== "done" && v.status !== "already"
        );
        if (!toUpload.length) {
            this.notification.add(_t("Vui lòng tích chọn ít nhất 1 video mới để đưa vào khóa học!"), { type: "warning" });
            return;
        }

        let chId = this.channelId;

        // Lưu khóa học trước khi upload nếu chưa có ID hoặc form đang có thay đổi dở
        if (!chId || (this.props.record && this.props.record.isDirty)) {
            if (this.props.record && typeof this.props.record.save === "function") {
                try {
                    await this.props.record.save();
                    chId = this.channelId;
                } catch (e) {
                    console.warn("Lưu khóa học tự động:", e);
                }
            }
        }

        if (!chId) {
            this.notification.add(
                _t("Vui lòng nhập Tên khóa học và bấm Lưu trước khi tải video!"),
                { type: "warning" }
            );
            return;
        }

        const targetFolderName = this.courseFolderPath || this.state.folderName || "VideoKhoaHoc";
        this.state.isUploading = true;
        this.state.uploadError = "";

        const existingOnDisk = toUpload.filter((v) => v.isExistingOnDisk);
        const filesToUpload = toUpload.filter((v) => !v.isExistingOnDisk && v.file);

        try {
            // 1. Thêm các video đã có sẵn trên đĩa vào khóa học
            if (existingOnDisk.length > 0) {
                const payload = existingOnDisk.map((v) => ({
                    filename: v.filename,
                    title: v.title,
                    category_id: v.categoryId === "new" ? 0 : (parseInt(v.categoryId, 10) || 0),
                    category_name: v.categoryId === "new" ? (v.categoryName || "") : "",
                    duration_minutes: v.durationMinutes || 15,
                    description: v.description || "",
                }));
                const res = await rpc("/slides/add_disk_videos_to_channel", {
                    channel_id: chId,
                    videos: payload,
                });
                if (res.error) {
                    throw new Error(res.error);
                }

                // Tự động tải lên tài liệu đính kèm nếu có
                if (res.slide_ids) {
                    for (const v of existingOnDisk) {
                        const sId = res.slide_ids[v.filename];
                        if (v.resourceFile && sId) {
                            await this.uploadAttachedResource(sId, v.resourceFile);
                        }
                    }
                }

                existingOnDisk.forEach((v) => {
                    v.status = "done";
                    v.progress = 100;
                    v.alreadyInCourse = true;
                });
            }

            // 2. Tải lên các file video mới từ máy tính nếu có
            if (filesToUpload.length > 0) {
                const total = filesToUpload.length;
                for (let i = 0; i < total; i++) {
                    const item = filesToUpload[i];
                    this.state.currentUploadIndex = i + 1;
                    this.state.currentUploadName = item.filename;
                    item.status = "uploading";

                    const createdSlideId = await this.uploadSingleFileChunked(item, chId, targetFolderName, (filePercent) => {
                        item.progress = filePercent;
                        this.state.currentFilePercent = filePercent;
                        this.state.overallPercent = Math.round(((i + filePercent / 100) / total) * 100);
                    });

                    // Tự động tải lên tài liệu đính kèm nếu có
                    if (item.resourceFile && createdSlideId) {
                        await this.uploadAttachedResource(createdSlideId, item.resourceFile);
                    }

                    item.status = "done";
                    item.progress = 100;
                    item.alreadyInCourse = true;
                }
            }

            this.state.isUploading = false;
            this.state.overallPercent = 100;
            this.notification.add(
                _t("Đã đưa thành công %s video vào khóa học!").replace("%s", toUpload.length),
                { type: "success" }
            );

            // Nạp lại form khóa học để cập nhật danh sách bài học và thống kê
            try {
                if (this.props.record && typeof this.props.record.load === "function") {
                    await this.props.record.load();
                }
            } catch (e) {
                console.warn("Reload record error:", e);
            }
            try {
                this.action.doAction({ type: "ir.actions.client", tag: "reload" });
            } catch (e) {
                // fallback
            }
        } catch (err) {
            this.state.uploadError = err.message || _t("Lỗi đưa video vào khóa học");
            this.notification.add(this.state.uploadError, { type: "danger" });
            this.state.isUploading = false;
        }
    }

    uploadSingleFileChunked(item, channelId, folderName, onProgress) {
        return new Promise((resolve, reject) => {
            const file = item.file;
            const CHUNK_SIZE = 5 * 1024 * 1024; // 5 MB
            const totalChunks = Math.ceil(file.size / CHUNK_SIZE) || 1;
            const uploadId = Date.now() + "_" + Math.random().toString(36).substring(2, 8);

            let chunkIdx = 0;
            let finalSlideId = null;

            const sendNextChunk = () => {
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
                formData.append("channel_id", channelId || this.channelId);
                formData.append("chunk_index", chunkIdx);
                formData.append("total_chunks", totalChunks);
                formData.append("filename", item.filename);
                formData.append("lesson_name", item.title || "");
                formData.append("folder_name", folderName || this.courseFolderPath || "");
                const catId = item.categoryId === "new" ? 0 : (parseInt(item.categoryId, 10) || 0);
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
                        const overallFilePercent = Math.min(
                            99,
                            Math.round(((chunkIdx + chunkProgress) / totalChunks) * 100)
                        );
                        onProgress(overallFilePercent);
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
                                sendNextChunk();
                            }
                        } catch {
                            reject(new Error("Lỗi phản hồi máy chủ: Không thể đọc dữ liệu JSON"));
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

                xhr.onerror = () => {
                    reject(new Error("Lỗi kết nối mạng khi tải lên!"));
                };

                xhr.send(formData);
            };

            sendNextChunk();
        });
    }
}

export const slideVideoFolderUploader = {
    component: SlideVideoFolderUploader,
    extractProps: () => ({}),
};

registry.category("view_widgets").add("slide_video_folder_uploader", slideVideoFolderUploader);

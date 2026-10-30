(function () {
    "use strict";

    const wrapper = document.querySelector(".tdb-wrapper");
    if (!wrapper) return;

    const SLIDE_ID = parseInt(wrapper.dataset.slideId || "0", 10);
    const CHANNEL_ID = parseInt(wrapper.dataset.channelId || "0", 10);
    const CATEGORY_ID = parseInt(wrapper.dataset.categoryId || "0", 10);
    const IS_OFFICER = wrapper.dataset.isOfficer === "1";
    const CSRF_TOKEN = wrapper.dataset.csrfToken || "";
                const video = document.getElementById("tdb_video");
                const skipToast = document.getElementById("tdb_skip_toast");
                const progressBar = document.getElementById("tdb_progress_bar");
                const progressLabel = document.getElementById("tdb_progress_label");
                const badgeCompleted = document.getElementById("tdb_badge_completed");
                const resumeBanner = document.getElementById("tdb_resume_banner");
                const resumeTimeStr = document.getElementById("tdb_resume_time_str");

                let maxWatchedTime = 0;
                let hasAutoCompleted = false;
                let skipToastTimeout = null;

                function formatTime(seconds) {
                    if (isNaN(seconds) || seconds < 0) return "00:00";
                    const m = Math.floor(seconds / 60);
                    const s = Math.floor(seconds % 60);
                    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
                }

                function showSkipToast() {
                    if (skipToastTimeout) clearTimeout(skipToastTimeout);
                    skipToast.style.display = "block";
                    skipToastTimeout = setTimeout(() => {
                        skipToast.style.display = "none";
                    }, 2800);
                }

                // ==================== KHÓA TẢI VỀ VIDEO (BẢO VỆ BẢN QUYỀN) ====================
                video.addEventListener("contextmenu", (e) => e.preventDefault());
                document.addEventListener("contextmenu", (e) => {
                    if (e.target.closest(".tdb-video-box") || e.target.tagName === "VIDEO") {
                        e.preventDefault();
                    }
                });
                // ==================== KHÓA PHÍM VÀ CHẶN TUA BÀI HỌC QUA BÀN PHÍM ====================
                window.addEventListener("keydown", (e) => {
                    // Chặn phím lưu trang, xem nguồn trang
                    if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S" || e.key === "u" || e.key === "U")) {
                        e.preventDefault();
                        return;
                    }

                    // Chặn các phím tua nhanh: Mũi tên phải, Mũi tên lên, PageDown, phím L
                    if (e.key === "ArrowRight" || e.key === "ArrowUp" || e.key === "PageDown" || e.key === "l" || e.key === "L") {
                        if (video.currentTime + 1.0 >= maxWatchedTime) {
                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation();
                            video.currentTime = maxWatchedTime;
                            showSkipToast();
                            return false;
                        }
                    }
                }, true);

                // ==================== TỰ ĐỘNG ĐỒNG BỘ THỜI LƯỢNG THỰC TẾ ====================
                let hasSyncedDuration = false;
                function checkAndSyncDuration() {
                    if (!hasSyncedDuration && video.duration > 0) {
                        hasSyncedDuration = true;
                        fetch("/slides/video/sync_duration", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                jsonrpc: "2.0",
                                method: "call",
                                params: {
                                    slide_id: SLIDE_ID,
                                    duration_seconds: video.duration,
                                }
                            })
                        }).catch(() => {});
                    }
                }
                function updateVideoAspectRatio() {
                    if (video.videoWidth > 0 && video.videoHeight > 0) {
                        const container = document.getElementById("tdb_video_container");
                        if (container) {
                            container.style.aspectRatio = `${video.videoWidth} / ${video.videoHeight}`;
                        }
                    }
                }
                video.addEventListener("loadedmetadata", () => {
                    checkAndSyncDuration();
                    updateVideoAspectRatio();
                });
                video.addEventListener("durationchange", checkAndSyncDuration);

                // ==================== KHỐI 2.1: KHÔNG ĐƯỢC SKIP (ANTI-SKIP) ====================
                video.addEventListener("timeupdate", () => {
                    checkAndSyncDuration();

                    if (!video.seeking) {
                        if (video.currentTime > maxWatchedTime) {
                            // Chỉ cho phép tăng maxWatchedTime khi video chạy tự nhiên (tối đa +1.5s mỗi nhịp)
                            if (video.currentTime - maxWatchedTime <= 1.5) {
                                maxWatchedTime = video.currentTime;
                            } else {
                                // Bị nhảy vọt bất thường -> Kéo ngược lại maxWatchedTime ngay
                                video.currentTime = maxWatchedTime;
                                showSkipToast();
                                return;
                            }
                        }
                    }

                    // Lưu vị trí xem để tiếp tục xem sau
                    if (video.currentTime > 5 && !video.ended) {
                        try {
                            localStorage.setItem("odoo_slide_resume_" + SLIDE_ID, Math.floor(video.currentTime));
                        } catch (e) {}
                    }

                    // ==================== KHỐI 2.2: PHẦN TRĂM HOÀN THÀNH RÕ RÀNG ====================
                    if (video.duration > 0) {
                        const percent = Math.min(100, Math.round((maxWatchedTime / video.duration) * 100));
                        progressBar.style.width = percent + "%";
                        progressLabel.innerText = percent + "%";

                        // Khi xem đạt >= 90% -> Tự động đánh dấu hoàn thành bài học
                        if (percent >= 90 && !hasAutoCompleted) {
                            hasAutoCompleted = true;
                            badgeCompleted.classList.remove("tdb-d-none");
                            markLessonCompleted();
                        }
                    }

                    // Cập nhật nhãn thời gian hiện tại trên nút thêm ghi chú
                    const noteAtTime = document.getElementById("tdb_note_at_time");
                    if (noteAtTime) {
                        noteAtTime.innerText = formatTime(video.currentTime);
                    }
                });

                // Ngăn chặn hành vi tua vượt (seeking ahead of maxWatchedTime)
                video.addEventListener("seeking", () => {
                    if (video.currentTime > maxWatchedTime + 0.5) {
                        video.currentTime = maxWatchedTime;
                        showSkipToast();
                    }
                });

                // Tự động đánh dấu hoàn thành bài học qua RPC
                async function markLessonCompleted() {
                    try {
                        await fetch("/slides/slide/mark_completed", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                jsonrpc: "2.0",
                                method: "call",
                                params: { slide_id: SLIDE_ID }
                            })
                        });
                        if (window.parent && window.parent !== window) {
                            window.parent.postMessage({ type: "tdb_slide_completed", slide_id: SLIDE_ID }, "*");
                        }
                    } catch (err) {
                        console.warn("Lỗi đồng bộ hoàn thành:", err);
                    }
                }

                // ==================== KHỐI 2.3: RESUME PLAYBACK (TIẾP TỤC XEM) ====================
                try {
                    const savedTime = parseInt(localStorage.getItem("odoo_slide_resume_" + SLIDE_ID) || "0", 10);
                    if (savedTime > 8) {
                        resumeTimeStr.innerText = formatTime(savedTime);
                        resumeBanner.classList.remove("tdb-d-none");

                        document.getElementById("tdb_btn_accept_resume").onclick = () => {
                            video.currentTime = savedTime;
                            maxWatchedTime = savedTime;
                            resumeBanner.classList.add("tdb-d-none");
                            video.play();
                        };
                        document.getElementById("tdb_btn_dismiss_resume").onclick = () => {
                            localStorage.removeItem("odoo_slide_resume_" + SLIDE_ID);
                            resumeBanner.classList.add("tdb-d-none");
                        };
                        setTimeout(() => {
                            resumeBanner.classList.add("tdb-d-none");
                        }, 12000);
                    }
                } catch (e) {}

                // ==================== KHỐI 2.3: GHI CHÚ TRONG VIDEO (COURSERA NOTES) ====================
                const notesKey = "odoo_slide_notes_" + SLIDE_ID;
                let notes = [];

                function loadNotes() {
                    try {
                        const raw = localStorage.getItem(notesKey);
                        notes = raw ? JSON.parse(raw) : [];
                    } catch (e) {
                        notes = [];
                    }
                    renderNotes();
                }

                function saveNotes() {
                    try {
                        localStorage.setItem(notesKey, JSON.stringify(notes));
                    } catch (e) {}
                    renderNotes();
                }

                function renderNotes() {
                    const listEl = document.getElementById("tdb_notes_list");
                    const badgeEl = document.getElementById("tdb_notes_count_badge");
                    if (!listEl) return;

                    if (badgeEl) {
                        badgeEl.innerText = notes.length;
                    }

                    if (!notes.length) {
                        listEl.innerHTML = `
                            <div class="tdb-empty-text">
                                Bạn chưa có ghi chú nào trong bài học này.<br/>Bấm nút phía trên để vừa học vừa ghi chép kiến thức!
                            </div>`;
                        return;
                    }

                    notes.sort((a, b) => a.time - b.time);
                    let html = "";
                    notes.forEach((item, idx) => {
                        html += `
                        <div class="tdb-note-card">
                            <div class="tdb-note-header">
                                <button type="button" class="tdb-time-badge tdb-btn-jump" data-time="${item.time}">
                                    ${formatTime(item.time)}
                                </button>
                                <button type="button" class="tdb-btn-danger-link tdb-btn-del-note" data-idx="${idx}">
                                    Xóa
                                </button>
                            </div>
                            <div class="tdb-note-text">${escapeHtml(item.text)}</div>
                        </div>`;
                    });
                    listEl.innerHTML = html;

                    listEl.querySelectorAll(".tdb-btn-jump").forEach((btn) => {
                        btn.onclick = (e) => {
                            const time = parseFloat(e.currentTarget.dataset.time);
                            if (!isNaN(time)) {
                                video.currentTime = time;
                                video.play();
                            }
                        };
                    });

                    listEl.querySelectorAll(".tdb-btn-del-note").forEach((btn) => {
                        btn.onclick = (e) => {
                            const idx = parseInt(e.currentTarget.dataset.idx, 10);
                            notes.splice(idx, 1);
                            saveNotes();
                        };
                    });
                }

                function escapeHtml(str) {
                    if (!str) return "";
                    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
                }

                // Xử lý tạo ghi chú mới
                let pendingNoteTime = 0;
                const addNoteForm = document.getElementById("tdb_add_note_form");
                const newNoteTimeLabel = document.getElementById("tdb_new_note_time_label");
                const newNoteText = document.getElementById("tdb_new_note_text");

                document.getElementById("tdb_btn_open_add_note").onclick = () => {
                    video.pause();
                    pendingNoteTime = Math.floor(video.currentTime);
                    newNoteTimeLabel.innerText = formatTime(pendingNoteTime);
                    newNoteText.value = "";
                    addNoteForm.classList.remove("tdb-d-none");
                    newNoteText.focus();
                };

                document.getElementById("tdb_btn_cancel_add_note").onclick = () => {
                    addNoteForm.classList.add("tdb-d-none");
                };

                document.getElementById("tdb_btn_confirm_add_note").onclick = () => {
                    const text = newNoteText.value.trim();
                    if (!text) return;
                    notes.push({
                        time: pendingNoteTime,
                        text: text,
                        created: Date.now()
                    });
                    saveNotes();
                    addNoteForm.classList.add("tdb-d-none");
                };

                loadNotes();

                // ==================== KHỐI 2.4: ĐÍNH KÈM TÀI LIỆU DÀNH CHO ADMIN ====================
                if (IS_OFFICER) {
                    const uploadResBtn = document.getElementById("tdb_btn_upload_res");
                    if (uploadResBtn) {
                        uploadResBtn.onclick = async () => {
                            const fileInput = document.getElementById("tdb_res_file_input");
                            const titleInput = document.getElementById("tdb_res_title_input");
                            const statusEl = document.getElementById("tdb_res_upload_status");
                            const file = fileInput.files[0];
                            if (!file) {
                                alert("Vui lòng chọn file tài liệu muốn đính kèm!");
                                return;
                            }

                            statusEl.innerText = "Đang tải lên tài liệu...";
                            statusEl.style.color = "#60a5fa";
                            statusEl.classList.remove("tdb-d-none");
                            uploadResBtn.disabled = true;

                            const formData = new FormData();
                            formData.append("slide_id", SLIDE_ID);
                            formData.append("name", titleInput.value.trim() || file.name);
                            formData.append("file", file);
                            if (CSRF_TOKEN) formData.append("csrf_token", CSRF_TOKEN);

                            try {
                                const res = await fetch("/slides/resource/upload", {
                                    method: "POST",
                                    body: formData
                                });
                                const data = await res.json();
                                if (data.error) {
                                    throw new Error(data.error);
                                }
                                statusEl.innerText = "Tải lên thành công! Đang cập nhật...";
                                statusEl.style.color = "#10b981";
                                setTimeout(() => window.location.reload(), 800);
                            } catch (err) {
                                statusEl.innerText = "Lỗi: " + err.message;
                                statusEl.style.color = "#ef4444";
                                uploadResBtn.disabled = false;
                            }
                        };
                    }
                }

                // ==================== KHỐI 3: QUẢN LÝ / CHỈNH SỬA & THÊM QUIZ DÀNH CHO ADMIN ====================
                if (IS_OFFICER) {
                    let allQuizzes = [];
                    try {
                        const initEl = document.getElementById("tdb_initial_quiz_data");
                        if (initEl && initEl.textContent) {
                            let raw = initEl.textContent.trim();
                            if (raw.includes("&quot;") || raw.includes("&#34;")) {
                                const txt = document.createElement("textarea");
                                txt.innerHTML = raw;
                                raw = txt.value;
                            }
                            allQuizzes = JSON.parse(raw);
                        }
                    } catch (e) {
                        console.warn("Lỗi phân tích quiz data:", e);
                        allQuizzes = [];
                    }

                    function makeBlankQuestion() {
                        return {
                            id: 0,
                            question: "",
                            question_type: "single",
                            answers: [
                                { id: 0, text: "Đáp án 1", is_correct: true },
                                { id: 0, text: "Đáp án 2", is_correct: false },
                                { id: 0, text: "Đáp án 3", is_correct: false },
                                { id: 0, text: "Đáp án 4", is_correct: false },
                            ]
                        };
                    }

                    if (!allQuizzes || !allQuizzes.length) {
                        allQuizzes = [{
                            id: SLIDE_ID,
                            name: "Quiz bài giảng",
                            is_inline: true,
                            questions: [makeBlankQuestion()],
                            questions_count: 0
                        }];
                    } else {
                        allQuizzes.forEach((q) => {
                            if (!q.questions || !q.questions.length) {
                                q.questions = [makeBlankQuestion()];
                            }
                        });
                    }

                    let currentQuizIndex = 0;
                    let isCreatingNewQuiz = false;
                    let newQuizQuestions = [makeBlankQuestion()];

                    function getCurrentQuiz() {
                        if (isCreatingNewQuiz) {
                            return {
                                id: 0,
                                name: "Quiz mới",
                                is_inline: false,
                                questions: newQuizQuestions,
                                questions_count: newQuizQuestions.length
                            };
                        }
                        if (currentQuizIndex >= allQuizzes.length) {
                            currentQuizIndex = Math.max(0, allQuizzes.length - 1);
                        }
                        return allQuizzes[currentQuizIndex];
                    }

                    function updateQuizUIState() {
                        const curr = getCurrentQuiz();
                        const questions = curr.questions || [];
                        const totalQuestionsAll = allQuizzes.reduce((acc, q) => acc + (q.questions ? q.questions.filter((item) => item.question && item.question.trim()).length : 0), 0);

                        const countBadge = document.getElementById("tdb_quiz_count_badge");
                        if (countBadge) {
                            countBadge.innerText = totalQuestionsAll;
                        }

                        const tabLabel = document.getElementById("tdb_quiz_tab_label");
                        if (tabLabel) {
                            tabLabel.innerText = totalQuestionsAll > 0 ? "Chỉnh sửa Quiz" : "Tạo Quiz";
                        }

                        // Badge trạng thái Quiz hiện tại
                        const badge = document.getElementById("tdb_quiz_current_badge");
                        if (badge) {
                            if (isCreatingNewQuiz) {
                                badge.innerText = "Tạo một bài Quiz mới cho video";
                                badge.style.color = "#10b981";
                            } else {
                                const countStr = questions.length > 0 ? ` (${questions.length} câu hỏi)` : " (Chưa có câu hỏi)";
                                badge.innerText = curr.is_inline ? `Quiz của video bài học${countStr}` : `Bài Quiz: ${curr.name}${countStr}`;
                                badge.style.color = "#3b82f6";
                            }
                        }

                        // Nút chuyển đổi chế độ Sửa Quiz hiện tại vs Tạo Quiz mới
                        const newModeBtn = document.getElementById("tdb_btn_new_quiz_mode");
                        if (newModeBtn) {
                            newModeBtn.innerText = isCreatingNewQuiz ? "Quay lại Quiz video" : "+ Thêm một bài Quiz mới";
                            newModeBtn.className = isCreatingNewQuiz ? "tdb-btn tdb-btn-secondary tdb-btn-sm" : "tdb-btn tdb-btn-outline tdb-btn-sm";
                        }

                        // Thanh chọn Quiz cũ: CHỈ HIỂN THỊ KHI CÓ TỪ 2 BÀI QUIZ TRỞ LÊN VÀ KHÔNG Ở CHẾ ĐỘ TẠO MỚI
                        const navBar = document.getElementById("tdb_quiz_nav_bar");
                        const selector = document.getElementById("tdb_quiz_selector");
                        if (navBar && selector) {
                            if (!isCreatingNewQuiz && allQuizzes.length > 1) {
                                navBar.classList.remove("tdb-d-none");
                                let selHtml = "";
                                allQuizzes.forEach((q, idx) => {
                                    const qCount = q.questions ? q.questions.filter((item) => (item.id && item.id > 0) || (item.question && item.question.trim())).length : 0;
                                    const isCurrent = (idx === currentQuizIndex);
                                    const titleStr = q.is_inline ? `Quiz của video bài học (${qCount} câu)` : `${q.name} (${qCount} câu)`;
                                    selHtml += `<option value="${idx}" ${isCurrent ? "selected" : ""}>${idx + 1}. ${escapeHtml(titleStr)}</option>`;
                                });
                                selector.innerHTML = selHtml;
                            } else {
                                navBar.classList.add("tdb-d-none");
                            }
                        }

                        // Form nhập tiêu đề khi tạo bài Quiz mới
                        const titleWrap = document.getElementById("tdb_new_quiz_title_wrap");
                        if (titleWrap) {
                            titleWrap.classList.toggle("tdb-d-none", !isCreatingNewQuiz);
                        }

                        const panelTitle = document.getElementById("tdb_quiz_panel_title");
                        if (panelTitle) {
                            if (isCreatingNewQuiz) {
                                panelTitle.innerText = "Soạn các câu hỏi cho bài Quiz mới của video này:";
                            } else {
                                panelTitle.innerText = `Nội dung câu hỏi trắc nghiệm (${questions.length} câu):`;
                            }
                        }

                        const saveText = document.getElementById("tdb_save_quiz_text");
                        if (saveText) {
                            saveText.innerText = isCreatingNewQuiz ? "Tạo bài Quiz mới" : "Cập nhật bài trắc nghiệm";
                        }

                        const delWrap = document.getElementById("tdb_quiz_delete_wrap");
                        if (delWrap) {
                            if (isCreatingNewQuiz) {
                                delWrap.classList.add("tdb-d-none");
                            } else {
                                delWrap.classList.remove("tdb-d-none");
                                const delBtn = document.getElementById("tdb_btn_delete_quiz");
                                if (delBtn) {
                                    delBtn.innerHTML = curr.is_inline
                                        ? "&#215; Xóa toàn bộ câu hỏi của video này"
                                        : `&#215; Xóa bài "${escapeHtml(curr.name)}" khỏi khóa học`;
                                }
                            }
                        }
                    }

                    function renderQuizBuilder() {
                        const container = document.getElementById("tdb_quiz_questions_container");
                        if (!container) return;

                        updateQuizUIState();

                        const curr = getCurrentQuiz();
                        const questions = curr.questions || [];

                        let html = "";
                        questions.forEach((q, qIdx) => {
                            if (!q.question_type) q.question_type = "single";
                            const isMulti = q.question_type === "multiple";
                            html += `
                            <div class="tdb-q-card">
                                <div class="tdb-q-card-header">
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span class="tdb-q-title-text">Câu hỏi ${qIdx + 1}</span>
                                        <select class="tdb-input tdb-q-type-select" data-qidx="${qIdx}" style="padding: 2px 6px; font-size: 11px; height: 26px; width: auto;">
                                            <option value="single" ${!isMulti ? "selected" : ""}>Một đáp án (Radio)</option>
                                            <option value="multiple" ${isMulti ? "selected" : ""}>Nhiều đáp án (Checkbox)</option>
                                        </select>
                                    </div>
                                    ${questions.length > 1 ? `<button type="button" class="tdb-btn-danger-link tdb-del-q-btn" data-qidx="${qIdx}" style="font-size: 11px;">Xóa câu</button>` : ""}
                                </div>
                                <input type="text" class="tdb-input tdb-q-title" data-qidx="${qIdx}"
                                       value="${escapeHtml(q.question)}" placeholder="Nhập nội dung câu hỏi..."/>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin: 8px 0 6px;">
                                    <span class="tdb-q-help-text">
                                        Các phương án trả lời (${isMulti ? "tích chọn các ô vuông đúng" : "chọn 1 nút tròn đúng"}):
                                    </span>
                                    <button type="button" class="tdb-btn-outline tdb-add-ans-btn" data-qidx="${qIdx}" style="padding: 2px 8px; font-size: 11px;">
                                        + Thêm phương án
                                    </button>
                                </div>
                                ${q.answers.map((ans, aIdx) => `
                                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                                        <input type="${isMulti ? "checkbox" : "radio"}" name="${isMulti ? `ans_multi_${qIdx}_${aIdx}` : `ans_single_${qIdx}`}"
                                               class="tdb-ans-correct" data-qidx="${qIdx}" data-aidx="${aIdx}" ${ans.is_correct ? "checked" : ""}
                                               title="Tích chọn đáp án đúng" style="width: 16px; height: 16px; cursor: pointer; flex-shrink: 0;"/>
                                        <input type="text" class="tdb-input tdb-ans-text" data-qidx="${qIdx}" data-aidx="${aIdx}"
                                               value="${escapeHtml(ans.text)}" placeholder="Đáp án ${aIdx + 1}" style="flex: 1;"/>
                                        ${q.answers.length > 2 ? `
                                        <button type="button" class="tdb-btn-danger-link tdb-del-ans-btn" data-qidx="${qIdx}" data-aidx="${aIdx}" title="Xóa phương án này" style="font-size: 14px; padding: 0 4px;">
                                            &#215;
                                        </button>` : ""}
                                    </div>
                                `).join("")}
                            </div>`;
                        });
                        container.innerHTML = html;

                        container.querySelectorAll(".tdb-q-title").forEach((inp) => {
                            inp.oninput = (e) => {
                                questions[parseInt(e.target.dataset.qidx, 10)].question = e.target.value;
                            };
                        });
                        container.querySelectorAll(".tdb-q-type-select").forEach((sel) => {
                            sel.onchange = (e) => {
                                const qIdx = parseInt(e.target.dataset.qidx, 10);
                                const newType = e.target.value;
                                questions[qIdx].question_type = newType;
                                if (newType === "single") {
                                    let found = false;
                                    questions[qIdx].answers.forEach((a) => {
                                        if (a.is_correct && !found) found = true;
                                        else a.is_correct = false;
                                    });
                                    if (!found && questions[qIdx].answers.length > 0) {
                                        questions[qIdx].answers[0].is_correct = true;
                                    }
                                }
                                renderQuizBuilder();
                            };
                        });
                        container.querySelectorAll(".tdb-ans-text").forEach((inp) => {
                            inp.oninput = (e) => {
                                const qIdx = parseInt(e.target.dataset.qidx, 10);
                                const aIdx = parseInt(e.target.dataset.aidx, 10);
                                questions[qIdx].answers[aIdx].text = e.target.value;
                            };
                        });
                        container.querySelectorAll(".tdb-ans-correct").forEach((input) => {
                            input.onchange = (e) => {
                                const qIdx = parseInt(e.target.dataset.qidx, 10);
                                const aIdx = parseInt(e.target.dataset.aidx, 10);
                                const q = questions[qIdx];
                                if (q.question_type === "single") {
                                    q.answers.forEach((a, i) => {
                                        a.is_correct = (i === aIdx);
                                    });
                                    renderQuizBuilder();
                                } else {
                                    q.answers[aIdx].is_correct = e.target.checked;
                                }
                            };
                        });
                        container.querySelectorAll(".tdb-add-ans-btn").forEach((btn) => {
                            btn.onclick = (e) => {
                                const qIdx = parseInt(e.currentTarget.dataset.qidx, 10);
                                questions[qIdx].answers.push({ id: 0, text: `Đáp án ${questions[qIdx].answers.length + 1}`, is_correct: false });
                                renderQuizBuilder();
                            };
                        });
                        container.querySelectorAll(".tdb-del-ans-btn").forEach((btn) => {
                            btn.onclick = (e) => {
                                const qIdx = parseInt(e.currentTarget.dataset.qidx, 10);
                                const aIdx = parseInt(e.currentTarget.dataset.aidx, 10);
                                if (questions[qIdx].answers.length > 2) {
                                    questions[qIdx].answers.splice(aIdx, 1);
                                    renderQuizBuilder();
                                }
                            };
                        });
                        container.querySelectorAll(".tdb-del-q-btn").forEach((btn) => {
                            btn.onclick = (e) => {
                                const qIdx = parseInt(e.target.dataset.qidx, 10);
                                questions.splice(qIdx, 1);
                                if (!questions.length) {
                                    questions.push(makeBlankQuestion());
                                }
                                renderQuizBuilder();
                            };
                        });
                    }

                    // Sự kiện chọn Quiz từ dropdown (chỉ khi có > 1 quiz)
                    const quizSelector = document.getElementById("tdb_quiz_selector");
                    if (quizSelector) {
                        quizSelector.onchange = (e) => {
                            currentQuizIndex = parseInt(e.target.value, 10);
                            isCreatingNewQuiz = false;
                            renderQuizBuilder();
                        };
                    }

                    // Sự kiện bấm nút "+ Thêm Quiz mới" / "Quay lại Quiz video"
                    const newQuizModeBtn = document.getElementById("tdb_btn_new_quiz_mode");
                    if (newQuizModeBtn) {
                        newQuizModeBtn.onclick = () => {
                            isCreatingNewQuiz = !isCreatingNewQuiz;
                            if (isCreatingNewQuiz) {
                                newQuizQuestions = [makeBlankQuestion()];
                                const titleInp = document.getElementById("tdb_new_quiz_title");
                                if (titleInp) titleInp.value = `Bài kiểm tra trắc nghiệm ${allQuizzes.length + 1}`;
                            }
                            renderQuizBuilder();
                        };
                    }

                    const addQBtn = document.getElementById("tdb_btn_add_quiz_q");
                    if (addQBtn) {
                        addQBtn.onclick = () => {
                            const curr = getCurrentQuiz();
                            curr.questions.push({
                                id: 0,
                                question: "",
                                question_type: "single",
                                answers: [
                                    { id: 0, text: "Đáp án 1", is_correct: true },
                                    { id: 0, text: "Đáp án 2", is_correct: false },
                                    { id: 0, text: "Đáp án 3", is_correct: false },
                                    { id: 0, text: "Đáp án 4", is_correct: false },
                                ]
                            });
                            renderQuizBuilder();
                        };
                    }

                    const saveQuizBtn = document.getElementById("tdb_btn_save_quiz");
                    if (saveQuizBtn) {
                        saveQuizBtn.onclick = async () => {
                            const statusEl = document.getElementById("tdb_quiz_status");
                            const curr = getCurrentQuiz();
                            const questions = curr.questions || [];

                            let newTitle = "";
                            if (isCreatingNewQuiz) {
                                const titleInp = document.getElementById("tdb_new_quiz_title");
                                newTitle = (titleInp && titleInp.value.trim()) || `Bài kiểm tra trắc nghiệm ${allQuizzes.length + 1}`;
                            }

                            for (let i = 0; i < questions.length; i++) {
                                const q = questions[i];
                                if (!q.question.trim()) {
                                    alert(`Vui lòng nhập nội dung cho Câu hỏi ${i + 1}`);
                                    return;
                                }
                                const validAnswers = q.answers.filter((a) => a.text && a.text.trim());
                                if (validAnswers.length < 2) {
                                    alert(`Câu hỏi ${i + 1} phải có ít nhất 2 phương án trả lời!`);
                                    return;
                                }
                                const correctCount = validAnswers.filter((a) => a.is_correct).length;
                                const incorrectCount = validAnswers.filter((a) => !a.is_correct).length;
                                if (correctCount === 0) {
                                    alert(`Câu hỏi ${i + 1} bắt buộc phải có ít nhất 1 đáp án đúng!`);
                                    return;
                                }
                                if (incorrectCount === 0) {
                                    alert(`Câu hỏi ${i + 1} bắt buộc phải có ít nhất 1 phương án sai!`);
                                    return;
                                }
                            }

                            statusEl.innerText = "Đang lưu bài trắc nghiệm...";
                            statusEl.style.color = "#60a5fa";
                            statusEl.classList.remove("tdb-d-none");
                            saveQuizBtn.disabled = true;

                            try {
                                const payload = {
                                    channel_id: CHANNEL_ID,
                                    slide_id: isCreatingNewQuiz ? null : curr.id,
                                    category_id: CATEGORY_ID,
                                    prerequisite_video_id: SLIDE_ID,
                                    lesson_title: isCreatingNewQuiz ? newTitle : curr.name,
                                    questions: questions
                                };

                                const res = await fetch("/slides/quiz/quick_create", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                        jsonrpc: "2.0",
                                        method: "call",
                                        params: payload
                                    })
                                });
                                const data = await res.json();
                                const result = data.result || {};
                                if (result.error) {
                                    throw new Error(result.error);
                                }

                                if (isCreatingNewQuiz) {
                                    const createdQuiz = {
                                        id: result.slide_id,
                                        name: result.slide_name || newTitle,
                                        is_inline: false,
                                        questions: result.questions || questions,
                                        questions_count: result.questions_count || questions.length
                                    };
                                    allQuizzes.push(createdQuiz);
                                    currentQuizIndex = allQuizzes.length - 1;
                                    isCreatingNewQuiz = false;
                                    statusEl.innerText = `Đã tạo thành công bài Quiz mới "${createdQuiz.name}"!`;
                                } else {
                                    if (result.questions) {
                                        curr.questions = result.questions;
                                    }
                                    curr.questions_count = (curr.questions || []).length;
                                    statusEl.innerText = `Đã cập nhật thành công "${curr.name}" (${curr.questions_count} câu)!`;
                                }

                                statusEl.style.color = "#10b981";
                                renderQuizBuilder();

                                // Làm mới thanh bài học bên ngoài nếu có thay đổi cấu trúc slide
                                if (isCreatingNewQuiz && window.parent && window.parent !== window) {
                                    setTimeout(() => {
                                        try { window.parent.location.reload(); } catch (e) {}
                                    }, 1200);
                                }
                            } catch (err) {
                                statusEl.innerText = "Lỗi: " + err.message;
                                statusEl.style.color = "#ef4444";
                            } finally {
                                saveQuizBtn.disabled = false;
                            }
                        };
                    }

                    const delQuizBtn = document.getElementById("tdb_btn_delete_quiz");
                    if (delQuizBtn) {
                        delQuizBtn.onclick = async () => {
                            const curr = getCurrentQuiz();
                            const confirmMsg = curr.is_inline
                                ? "Bạn có chắc chắn muốn xóa toàn bộ câu hỏi trắc nghiệm của video này không?"
                                : `Bạn có chắc chắn muốn xóa bài Quiz "${curr.name}" khỏi khóa học không?`;

                            if (!confirm(confirmMsg)) return;

                            const statusEl = document.getElementById("tdb_quiz_status");
                            statusEl.innerText = "Đang xóa...";
                            statusEl.style.color = "#60a5fa";
                            statusEl.classList.remove("tdb-d-none");

                            try {
                                const res = await fetch("/slides/quiz/delete", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                        jsonrpc: "2.0",
                                        method: "call",
                                        params: { slide_id: curr.id }
                                    })
                                });
                                const data = await res.json();
                                const result = data.result || {};
                                if (result.error) {
                                    throw new Error(result.error);
                                }

                                if (curr.is_inline) {
                                    curr.questions = [makeBlankQuestion()];
                                    curr.questions_count = 0;
                                    statusEl.innerText = "Đã xóa toàn bộ câu hỏi của video này.";
                                } else {
                                    allQuizzes.splice(currentQuizIndex, 1);
                                    currentQuizIndex = Math.max(0, currentQuizIndex - 1);
                                    statusEl.innerText = "Đã xóa bài Quiz khỏi khóa học thành công.";
                                }

                                statusEl.style.color = "#10b981";
                                renderQuizBuilder();

                                if (!curr.is_inline && window.parent && window.parent !== window) {
                                    setTimeout(() => {
                                        try { window.parent.location.reload(); } catch (e) {}
                                    }, 1200);
                                }
                            } catch (err) {
                                statusEl.innerText = "Lỗi: " + err.message;
                                statusEl.style.color = "#ef4444";
                            }
                        };
                    }

                    // Khởi tạo sẵn giao diện Quiz builder ngay khi trang nhúng tải xong
                    renderQuizBuilder();
                }

                // ==================== ĐIỀU KHIỂN TABS CỘT PHẢI ====================
                const panelNotes = document.getElementById("tdb_panel_notes");
                const panelDesc = document.getElementById("tdb_panel_desc");
                const panelRes = document.getElementById("tdb_panel_resources");
                const panelQuiz = document.getElementById("tdb_panel_quiz");
                const tabNotesBtn = document.getElementById("tdb_tab_notes_btn");
                const tabDescBtn = document.getElementById("tdb_tab_desc_btn");
                const tabResBtn = document.getElementById("tdb_tab_res_btn");
                const tabQuizBtn = document.getElementById("tdb_tab_quiz_btn");

                function switchSideTab(tab) {
                    if (isPanelCollapsed) {
                        isPanelCollapsed = false;
                        sideCol.classList.remove("collapsed");
                        togglePanelText.innerText = "Thu nhỏ bảng";
                    }
                    panelNotes.classList.toggle("tdb-d-none", tab !== "notes");
                    if (panelDesc) panelDesc.classList.toggle("tdb-d-none", tab !== "desc");
                    panelRes.classList.toggle("tdb-d-none", tab !== "res");
                    if (panelQuiz) panelQuiz.classList.toggle("tdb-d-none", tab !== "quiz");

                    tabNotesBtn.classList.toggle("active", tab === "notes");
                    if (tabDescBtn) tabDescBtn.classList.toggle("active", tab === "desc");
                    tabResBtn.classList.toggle("active", tab === "res");
                    if (tabQuizBtn) tabQuizBtn.classList.toggle("active", tab === "quiz");

                    if (tab === "quiz" && IS_OFFICER) {
                        renderQuizBuilder();
                    }
                }

                tabNotesBtn.onclick = () => switchSideTab("notes");
                if (tabDescBtn) tabDescBtn.onclick = () => switchSideTab("desc");
                tabResBtn.onclick = () => switchSideTab("res");
                if (tabQuizBtn) tabQuizBtn.onclick = () => switchSideTab("quiz");

                // ==================== BẬT / TẮT BẢNG BÊN (TOGGLE SIDE PANEL) ====================
                const sideCol = document.getElementById("tdb_col_side");
                const togglePanelBtn = document.getElementById("tdb_btn_toggle_panel");
                const togglePanelText = document.getElementById("tdb_toggle_panel_text");
                let isPanelCollapsed = false;

                togglePanelBtn.onclick = () => {
                    isPanelCollapsed = !isPanelCollapsed;
                    sideCol.classList.toggle("collapsed", isPanelCollapsed);
                    togglePanelText.innerText = isPanelCollapsed ? "Mở bảng tiện ích" : "Thu nhỏ bảng";
                };

                // ==================== CHUYỂN ĐỔI GIAO DIỆN SÁNG / TỐI (LIGHT / DARK THEME) ====================
                const toggleThemeBtn = document.getElementById("tdb_btn_toggle_theme");
                const themeIcon = document.getElementById("tdb_theme_icon");
                const themeText = document.getElementById("tdb_theme_text");

                const sunIconSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
                const moonIconSvg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';

                const parentCssRules = `
                    .o_wslides_fs_main.tdb-parent-light {
                        background-image: none !important;
                        background-color: #f8fafc !important;
                        color: #1e293b !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_slide_fs_header {
                        background-image: none !important;
                        background-color: #ffffff !important;
                        border-bottom: 1px solid #e2e8f0 !important;
                        color: #0f172a !important;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_slide_fs_header a {
                        background-color: #f1f5f9 !important;
                        color: #334155 !important;
                        border: 1px solid #e2e8f0 !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_slide_fs_header a:hover {
                        background-color: #e2e8f0 !important;
                        color: #0f172a !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_slide_fs_header a.active {
                        background-color: #2563eb !important;
                        color: #ffffff !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_fs_sidebar {
                        background-image: none !important;
                        background-color: #ffffff !important;
                        border-right: 1px solid #e2e8f0 !important;
                        color: #1e293b !important;
                        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04) !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_fs_sidebar_header h1,
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_fs_sidebar_header a {
                        color: #0f172a !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_progress_percentage {
                        color: #0f172a !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .progress {
                        background-color: #e2e8f0 !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_fs_sidebar_section {
                        background-color: #f8fafc !important;
                        border-bottom: 1px solid #e2e8f0 !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_fs_sidebar_section a b {
                        color: #0f172a !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light li.o_wslides_fs_sidebar_list_item:not(.active) {
                        color: #475569 !important;
                        background-color: transparent !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light li.o_wslides_fs_sidebar_list_item:not(.active) a {
                        color: #334155 !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light li.o_wslides_fs_sidebar_list_item:hover {
                        background-color: #f1f5f9 !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light li.o_wslides_fs_sidebar_list_item.active {
                        background-color: #eff6ff !important;
                        box-shadow: inset 3px 0 0 #2563eb !important;
                        color: #1d4ed8 !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light li.o_wslides_fs_sidebar_list_item.active a {
                        color: #1d4ed8 !important;
                        font-weight: 600 !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .text-600,
                    .o_wslides_fs_main.tdb-parent-light .text-muted,
                    .o_wslides_fs_main.tdb-parent-light i.oi {
                        color: #64748b !important;
                    }
                    .o_wslides_fs_main.tdb-parent-light .o_wslides_fs_slide_name {
                        color: inherit !important;
                    }
                `;

                function syncParentTheme(isLight) {
                    try {
                        if (window.parent && window.parent.document) {
                            const pDoc = window.parent.document;
                            let styleEl = pDoc.getElementById("tdb_fs_theme_style");
                            if (!styleEl) {
                                styleEl = pDoc.createElement("style");
                                styleEl.id = "tdb_fs_theme_style";
                                styleEl.innerHTML = parentCssRules;
                                pDoc.head.appendChild(styleEl);
                            }
                            const pFsMain = pDoc.querySelector(".o_wslides_fs_main");
                            if (pFsMain) {
                                pFsMain.classList.toggle("tdb-parent-light", isLight);
                            }
                            pDoc.body.classList.toggle("tdb-parent-light", isLight);
                        }
                    } catch (e) {
                        console.warn("Theme sync with parent:", e);
                    }
                }

                function applyTheme(theme) {
                    const isLight = (theme === "light");
                    if (isLight) {
                        if (wrapper) wrapper.classList.add("tdb-theme-light");
                        document.body.classList.add("tdb-theme-light");
                        if (themeIcon) themeIcon.innerHTML = moonIconSvg;
                        if (themeText) themeText.innerText = "Chế độ tối";
                    } else {
                        if (wrapper) wrapper.classList.remove("tdb-theme-light");
                        document.body.classList.remove("tdb-theme-light");
                        if (themeIcon) themeIcon.innerHTML = sunIconSvg;
                        if (themeText) themeText.innerText = "Chế độ sáng";
                    }
                    try {
                        localStorage.setItem("tdb_theme_mode", isLight ? "light" : "dark");
                    } catch (e) {}

                    syncParentTheme(isLight);
                }

                // Khởi tạo theme từ bộ nhớ trình duyệt
                const savedTheme = localStorage.getItem("tdb_theme_mode") || "dark";
                applyTheme(savedTheme);

                if (toggleThemeBtn) {
                    toggleThemeBtn.onclick = () => {
                        const isCurrentLight = wrapper ? wrapper.classList.contains("tdb-theme-light") : false;
                        applyTheme(isCurrentLight ? "dark" : "light");
                    };
                }
            })();

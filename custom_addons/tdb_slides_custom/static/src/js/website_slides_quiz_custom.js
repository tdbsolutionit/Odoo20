/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { WebsiteSlidesQuiz } from "@website_slides/interactions/slides_course_quiz";
import { _t } from "@web/core/l10n/translation";

patch(WebsiteSlidesQuiz.prototype, {
    setup() {
        super.setup(...arguments);
        const quizEl = this.el.querySelector("#lessonQuiz") || this.el;
        if (quizEl && quizEl.dataset.isQuizLocked === "1") {
            for (const inputEl of this.el.querySelectorAll("input")) {
                inputEl.disabled = true;
            }
            const submitBtn = this.el.querySelector(".o_wslides_js_lesson_quiz_submit");
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.classList.add("disabled");
                submitBtn.style.opacity = "0.5";
                submitBtn.style.pointerEvents = "none";
            }
        }
    },

    onAnswerClick(event) {
        if (this.slide.completed) return;
        const answerEl = event.currentTarget;
        const qEl = answerEl.closest(".o_wslides_js_lesson_quiz_question");
        const listGroup = answerEl.closest(".list-group");
        const isMulti = (listGroup && listGroup.dataset.isMulti === "1") || (qEl && qEl.dataset.isMulti === "1") || !!answerEl.querySelector("input[type=checkbox]");

        if (isMulti) {
            const input = answerEl.querySelector("input");
            if (input) {
                input.checked = !input.checked;
            }
            const isChecked = input ? input.checked : !answerEl.classList.contains("list-group-item-primary");
            answerEl.classList.toggle("list-group-item-primary", isChecked);
            return;
        }

        const radio = answerEl.querySelector("input[type=radio]") || answerEl.querySelector("input");
        if (radio) {
            radio.checked = true;
            if (qEl) {
                for (const a of qEl.querySelectorAll(".o_wslides_quiz_answer")) {
                    a.classList.remove("list-group-item-primary");
                }
            }
            answerEl.classList.add("list-group-item-primary");
        }
    },

    getQuizAnswers() {
        const answers = [];
        for (const inputEl of this.el.querySelectorAll("input:checked")) {
            if (inputEl.value) {
                answers.push(parseInt(inputEl.value, 10));
            }
        }
        return answers;
    },

    disableAnswers() {
        for (const el of this.el.querySelectorAll(".o_wslides_js_lesson_quiz_question")) {
            el.classList.add("completed-disabled");
        }
        for (const el of this.el.querySelectorAll("input")) {
            el.disabled = this.slide.completed;
        }
    },

    applySessionAnswers() {
        if (!this.quiz.sessionAnswers || this.quiz.sessionAnswers.length === 0) {
            return;
        }
        for (const questionEl of this.el.querySelectorAll(".o_wslides_js_lesson_quiz_question")) {
            for (const answerEl of questionEl.querySelectorAll("a.o_wslides_quiz_answer")) {
                const answerId = Number(answerEl.dataset.answerId);
                if (this.quiz.sessionAnswers.includes(answerId)) {
                    const inputEl = answerEl.querySelector("input");
                    if (inputEl) inputEl.checked = true;
                    answerEl.classList.add("list-group-item-primary");
                }
            }
        }
        this.quiz.sessionAnswers = [];
    },

    showErrorMessage(errorCode) {
        if (errorCode === "quiz_locked") {
            this.error = _t("Bài kiểm tra đang bị khóa! Bạn cần xem và hoàn thành video bài học trước khi làm bài.");
            return;
        }
        super.showErrorMessage(errorCode);
    },

    renderAnswersHighlightingAndComments() {
        for (const questionEl of this.el.querySelectorAll(".o_wslides_js_lesson_quiz_question")) {
            const questionId = Number(questionEl.dataset.questionId);
            const isCorrect = this.quiz.answers[questionId] ? this.quiz.answers[questionId].is_correct : false;

            for (const answerEl of questionEl.querySelectorAll("a.o_wslides_quiz_answer")) {
                for (const iconEl of answerEl.querySelectorAll("i.oi")) {
                    iconEl.classList.add("d-none");
                }

                const inputEl = answerEl.querySelector("input[type=radio], input[type=checkbox]");
                if (inputEl && inputEl.checked) {
                    if (isCorrect) {
                        answerEl.classList.remove("list-group-item-danger", "list-group-item-primary");
                        answerEl.classList.add("list-group-item-success");
                        const checkIcon = answerEl.querySelector("i[data-icon='check_circle']");
                        if (checkIcon) checkIcon.classList.remove("d-none");
                    } else {
                        answerEl.classList.remove("list-group-item-success", "list-group-item-primary");
                        answerEl.classList.add("list-group-item-danger");
                        const cancelIcon = answerEl.querySelector("i[data-icon='cancel']");
                        if (cancelIcon) cancelIcon.classList.remove("d-none");
                        inputEl.checked = false;
                    }
                } else {
                    answerEl.classList.remove("list-group-item-danger", "list-group-item-success", "list-group-item-primary");
                    const circleIcon = answerEl.querySelector("i[data-icon='circle'].oi-filled");
                    if (circleIcon) circleIcon.classList.remove("d-none");
                }
            }

            const comment = this.quiz.answers[questionId] ? this.quiz.answers[questionId].comment : null;
            if (comment) {
                const infoEl = questionEl.querySelector(".o_wslides_quiz_answer_info");
                const commentEl = questionEl.querySelector(".o_wslides_quiz_answer_comment");
                if (infoEl) infoEl.classList.remove("d-none");
                if (commentEl) commentEl.textContent = comment;
            }
        }
    }
});

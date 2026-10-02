/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ToolbarPlugin } from "@html_editor/main/toolbar/toolbar_plugin";
import { FontTypePlugin } from "@html_editor/main/font/font_type_plugin";
import { AlignPlugin } from "@html_editor/main/align/align_plugin";
import { _t } from "@web/core/l10n/translation";

// 1. Đảm bảo FontTypeSelector luôn hiển thị nhãn "Bình thường" (thay vì ô trống) khi mới mở popup
patch(FontTypePlugin.prototype, {
    setup() {
        super.setup(...arguments);
        if (!this.fontType.displayName) {
            this.fontType.displayName = _t("Normal");
        }
    },
    get fontTypeName() {
        try {
            return super.fontTypeName || _t("Normal");
        } catch (e) {
            return _t("Normal");
        }
    },
});

// 2. Đảm bảo AlignSelector luôn hiển thị biểu tượng căn lề trái mặc định (thay vì ô trống)
patch(AlignPlugin.prototype, {
    setup() {
        super.setup(...arguments);
        if (!this.alignment.displayName) {
            this.alignment.displayName = "left";
        }
    },
    get alignmentIconMode() {
        try {
            return super.alignmentIconMode || "left";
        } catch (e) {
            return "left";
        }
    },
});

// 3. Tùy biến ToolbarPlugin cho chế độ cố định trong Popup Modal
patch(ToolbarPlugin.prototype, {
    get isStationaryMode() {
        // Chỉ kích hoạt chế độ stationary toolbar khi editor nằm TRONG popup modal
        // hoặc có cấu hình top_toolbar: true. Tuyệt đối không ảnh hưởng editor ở ngoài.
        return Boolean(
            this.config?.top_toolbar ||
            this.editable?.closest?.(".modal, .modal-dialog, .o_dialog, .modal-content")
        );
    },

    setup() {
        super.setup(...arguments);
        if (this.isStationaryMode) {
            this.state.namespace = "expanded";
            this.isToolbarExpanded = true;
            if (this.toolbarProps) {
                this.toolbarProps.class = "border-bottom bg-white w-100 shadow-none";
            }
            this.updateButtonsStates();
        }
    },

    closeToolbar(selectionData = null, { force = false } = {}) {
        if (this.isStationaryMode && !force) {
            return;
        }
        super.closeToolbar(...arguments);
    },

    _updateToolbar(selectionData = this.dependencies.selection.getSelectionData()) {
        if (this.isDestroyed || !this.document.isConnected) {
            return;
        }
        if (this.isStationaryMode) {
            this.state.namespace = "expanded";
            this.isToolbarExpanded = true;
            let filtered = [];
            try {
                const targeted = this.dependencies.selection.getTargetedNodes?.() || [];
                filtered = this.getFilteredTargetedNodes(targeted);
            } catch (e) {
                filtered = [];
            }
            this.updateButtonsStates(selectionData?.editableSelection || null, filtered);
            return;
        }
        super._updateToolbar(...arguments);
    },

    getAvailableButtonsSet(selection) {
        if (this.isStationaryMode) {
            this.state.namespace = "expanded";
            this.isToolbarExpanded = true;
            const isAvailable = (button) => {
                try {
                    return button.isAvailable ? button.isAvailable(selection) : true;
                } catch (e) {
                    return true;
                }
            };
            return new Set(
                this.getButtonsForNamespace("expanded")
                    .filter((b) => b.groupId !== "expand_toolbar" && b.id !== "expand_toolbar")
                    .filter(isAvailable)
            );
        }
        return super.getAvailableButtonsSet(...arguments);
    },

    getButtonGroups() {
        if (!this.isStationaryMode) {
            return super.getButtonGroups(...arguments);
        }
        const buttons = this.getButtons();
        const mapExpanded = (b) => ({ ...b, namespaces: ["expanded"] });
        const findButton = (id) => {
            const b = buttons.find((btn) => btn.id === id);
            return b ? mapExpanded(b) : null;
        };

        // Khôi phục chính xác 4 nhóm nút chuẩn Odoo 20 giống hệt thanh ngoài:
        // Nhóm 1: font (Bình thường, Font, Cỡ chữ - 14 +)
        // Nhóm 2: decoration (B, I, U, S, A, Sơn, Xóa định dạng)
        // Nhóm 3: layout (Danh sách :≡, Căn lề ≡)
        // Nhóm 4: link (Liên kết 🔗)
        return [
            {
                id: "font",
                buttons: ["font-type", "font-family", "font-size"].map(findButton).filter(Boolean),
            },
            {
                id: "decoration",
                buttons: [
                    "bold",
                    "italic",
                    "underline",
                    "strikethrough",
                    "forecolor",
                    "backcolor",
                    "remove_format",
                ].map(findButton).filter(Boolean),
            },
            {
                id: "layout",
                buttons: ["list", "alignment"].map(findButton).filter(Boolean),
            },
            {
                id: "link",
                buttons: ["link"].map(findButton).filter(Boolean),
            },
        ].filter((g) => g.buttons.length > 0);
    },

    updateButtonsStates(selection = null, targetedNodes = []) {
        if (!this.isStationaryMode) {
            return super.updateButtonsStates(...arguments);
        }

        if (!selection && this.dependencies?.selection) {
            try {
                selection = this.dependencies.selection.getEditableSelection?.() || null;
            } catch (e) {
                selection = null;
            }
        }
        if (!selection && this.editable) {
            selection = {
                anchorNode: this.editable,
                anchorOffset: 0,
                focusNode: this.editable,
                focusOffset: 0,
                isCollapsed: true,
                toString: () => "",
            };
        }
        if ((!targetedNodes || targetedNodes.length === 0) && this.dependencies?.selection && selection) {
            try {
                targetedNodes = this.dependencies.selection.getTargetedNodes?.() || [];
            } catch (e) {
                targetedNodes = [];
            }
        }

        let availableButtons = new Set();
        try {
            availableButtons = this.getAvailableButtonsSet(selection);
        } catch (e) {
            try {
                availableButtons = new Set(this.getButtonsForNamespace("expanded"));
            } catch (err) {}
        }

        this.state.buttonGroups = this.buttonGroups
            .map((group) => ({
                id: group.id,
                buttons: group.buttons
                    .filter((button) => {
                        try {
                            return availableButtons.has(button);
                        } catch (e) {
                            return true;
                        }
                    })
                    .map((button) => {
                        let description = "";
                        try {
                            description = typeof button.description === "function"
                                ? (button.description(selection, targetedNodes) || "")
                                : (button.description || "");
                        } catch (e) {
                            description = button.id || "";
                        }
                        if (button.id === "forecolor") {
                            description = description || "Màu chữ";
                        } else if (button.id === "backcolor") {
                            description = description || "Màu đánh dấu";
                        } else if (button.id === "strikethrough") {
                            description = description || "Gạch ngang";
                        } else if (button.id === "remove_format") {
                            description = description || "Xóa định dạng";
                        }
                        if (typeof description !== "string") {
                            description = String(description || "");
                        }

                        let isDisabled = false;
                        try {
                            isDisabled = Boolean(
                                typeof button.isDisabled === "function"
                                    ? button.isDisabled(selection, targetedNodes)
                                    : button.isDisabled
                            );
                        } catch (e) {
                            isDisabled = false;
                        }

                        if (button.Component) {
                            return {
                                id: button.id,
                                description,
                                isDisabled,
                                Component: button.Component,
                                props: button.props || {},
                            };
                        } else {
                            let isActive = false;
                            try {
                                isActive = Boolean(
                                    typeof button.isActive === "function"
                                        ? button.isActive(selection, targetedNodes)
                                        : button.isActive
                                );
                            } catch (e) {
                                isActive = false;
                            }
                            const run = typeof button.run === "function" ? button.run : () => {};
                            const res = {
                                id: button.id,
                                description,
                                isDisabled,
                                isActive,
                                run,
                            };
                            if (button.icon) res.icon = button.icon;
                            if (button.iconClass) res.iconClass = button.iconClass;
                            if (button.text) res.text = button.text;
                            return res;
                        }
                    }),
            }))
            .filter((group) => group.buttons.length > 0);
    },
});

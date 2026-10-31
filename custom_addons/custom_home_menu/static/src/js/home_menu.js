/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { useListener } from "@odoo/owl";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.state.isHomeMenuOpened = false;
        this.state.searchQuery = "";

        useListener(window, "keydown", (ev) => {
            if (this.state.isHomeMenuOpened && ev.key === "Escape") {
                this.state.isHomeMenuOpened = false;
                this.state.searchQuery = "";
            }
        });
        useListener(this.env.bus, "MENUS:APP-CHANGED", () => {
            this.state.isHomeMenuOpened = false;
            this.state.searchQuery = "";
        });
    },

    toggleHomeMenu(force) {
        this.state.isHomeMenuOpened =
            typeof force === "boolean" ? force : !this.state.isHomeMenuOpened;
        this.state.searchQuery = "";
        if (this.state.isHomeMenuOpened) {
            setTimeout(() => {
                const input = document.querySelector(".o_home_menu_search_input");
                input?.focus();
            }, 60);
        }
    },

    onAppClick(app) {
        this.state.isHomeMenuOpened = false;
        this.state.searchQuery = "";
        this.onNavBarDropdownItemSelection(app);
    },

    onSearchKeyDown(ev) {
        if (ev.key === "Enter") {
            const apps = this.displayedApps;
            if (apps.length > 0) {
                this.onAppClick(apps[0]);
            }
        } else if (ev.key === "Escape") {
            this.toggleHomeMenu(false);
        }
    },

    getAppIcon(app) {
        if (!app) {
            return "/web/static/img/default_icon_app.png";
        }

        // 1. ƯU TIÊN SỐ 1: Ánh xạ theo tên app chuẩn của Odoo
        const defaultAppIcons = {
            "discuss": "/mail/static/description/icon.png",
            "calendar": "/calendar/static/description/icon.png",
            "to-do": "/project_todo/static/description/icon.png",
            "contacts": "/contacts/static/description/icon.png",
            "crm": "/crm/static/description/icon.png",
            "sales": "/sale/static/description/icon.png",
            "dashboards": "/spreadsheet_dashboard/static/description/icon.png",
            "point of sale": "/point_of_sale/static/description/icon.png",
            "invoicing": "/account/static/description/icon.png",
            "project": "/project/static/description/icon.png",
            "website": "/website/static/description/icon.png",
            "elearning": "/website_slides/static/description/icon.png",
            "email marketing": "/mass_mailing/static/description/icon.png",
            "purchase": "/purchase/static/description/icon.png",
            "inventory": "/stock/static/description/icon.png",
            "manufacturing": "/mrp/static/description/icon.png",
            "documents": "/dms/static/description/icon.png",
            "plm": "/plm/static/description/icon.png",
        };
        const normalizedName = (app.name || "").toLowerCase().trim();
        if (defaultAppIcons[normalizedName]) {
            return defaultAppIcons[normalizedName];
        }

        // 2. Nếu có web_icon riêng của module (như PLM, DMS)
        if (app.webIcon && typeof app.webIcon === "string" && app.webIcon.includes(",")) {
            const parts = app.webIcon.split(",");
            return `/${parts[0].trim()}/${parts[1].trim()}`;
        }
        if (app.webIcon && typeof app.webIcon === "string" && app.webIcon.includes("/")) {
            return app.webIcon.startsWith("/") ? app.webIcon : `/${app.webIcon}`;
        }

        // 3. Nếu có xmlid của module
        if (app.xmlid) {
            const moduleName = app.xmlid.split(".")[0];
            return `/${moduleName}/static/description/icon.png`;
        }

        // 4. Chỉ dùng webIconData nếu không phải là icon mặc định
        if (app.webIconData) {
            return app.webIconData.startsWith("data:") || app.webIconData.startsWith("/")
                ? app.webIconData
                : `data:image/png;base64,${app.webIconData}`;
        }

        return "/web/static/img/default_icon_app.png";
    },

    get displayedApps() {
        const apps =
            (typeof this.menuService.getApps === "function"
                ? this.menuService.getApps()
                : this.menuService.getApps) || [];
        if (!this.state.searchQuery) {
            return apps;
        }
        const query = this.state.searchQuery.toLowerCase().trim();
        return apps.filter((app) => app && app.name && app.name.toLowerCase().includes(query));
    },
});

/**
 * Tự động chuẩn hóa Accessibility (A11y) & Autofill cho toàn bộ giao diện Odoo
 * Giải quyết triệt để các cảnh báo trong tab Issues của Google Chrome:
 * 1. A form field element should have an id or name attribute
 * 2. No label associated with a form field
 * 3. Incorrect use of <label for=FORM_ELEMENT>
 */
if (typeof window !== "undefined") {
    let a11yTimeout = null;
    let isRunning = false;

    const fixAccessibilityIssues = () => {
        if (isRunning) return;
        isRunning = true;

        try {
            // 1. Chuẩn hóa thẻ <label for="xxx"> (Khắc phục lỗi "Incorrect use of <label for=FORM_ELEMENT>")
            document.querySelectorAll("label[for]").forEach((label) => {
                const targetId = label.getAttribute("for");
                if (!targetId || document.getElementById(targetId)) return;

                // Tìm trong cùng dòng / ô input lân cận (Odoo Form Grid)
                const container = label.closest(".o_wrap_field, tr, .row, .o_group_col, .o_inner_group, .o_cell") || label.parentElement?.parentElement;
                let target = container?.querySelector("input, select, textarea, .o_field_widget");

                // Nếu chưa thấy, tìm theo tên trường tương ứng (ví dụ: for="name_0" -> tìm field "name")
                if (!target) {
                    const rawField = targetId.replace(/_\d+$/, "");
                    target = document.querySelector(`.o_field_widget[name="${rawField}"] input, .o_field_widget[name="${rawField}"]`);
                }

                if (target) {
                    target.id = targetId;
                } else {
                    const nextCell = label.closest(".o_cell")?.nextElementSibling;
                    if (nextCell) {
                        nextCell.id = targetId;
                    } else if (label.parentElement) {
                        label.parentElement.id = targetId;
                    }
                }
            });

            // 2. Chuẩn hóa tất cả các trường input/select/textarea (Khắc phục "No label" và "Missing id or name")
            document.querySelectorAll("input, select, textarea").forEach((el, idx) => {
                // Bổ sung ID nếu chưa có
                if (!el.id) {
                    el.id = `o_field_id_${idx}`;
                }

                // Bổ sung Name nếu chưa có
                if (!el.getAttribute("name")) {
                    const clean = (el.placeholder || el.getAttribute("aria-label") || el.type || "field")
                        .toLowerCase().replace(/[^a-z0-9]/g, "_").replace(/^_+|_+$/g, "") || "field";
                    el.setAttribute("name", `${clean}_${idx}`);
                }

                // Bổ sung thẻ <label> chuẩn nếu chưa có (Khắc phục "No label associated with a form field")
                if (el.type !== "hidden") {
                    const hasLabel = document.querySelector(`label[for="${el.id}"]`) || el.closest("label");
                    if (!hasLabel) {
                        const lbl = document.createElement("label");
                        lbl.setAttribute("for", el.id);
                        lbl.className = "visually-hidden";
                        lbl.style.cssText = "position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important;";
                        lbl.textContent = el.placeholder || el.getAttribute("aria-label") || el.name || "Input";
                        el.parentNode?.insertBefore(lbl, el);
                    }
                }
            });
        } catch (e) {
            // Không làm ảnh hưởng logic nghiệp vụ
        } finally {
            isRunning = false;
        }
    };

    const debouncedFix = () => {
        if (a11yTimeout) cancelAnimationFrame(a11yTimeout);
        a11yTimeout = requestAnimationFrame(fixAccessibilityIssues);
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", debouncedFix);
    } else {
        debouncedFix();
    }

    const observer = new MutationObserver(debouncedFix);
    observer.observe(document.documentElement, { childList: true, subtree: true });
}


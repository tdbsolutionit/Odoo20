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
    let fieldCounter = 0;

    const fixAccessibilityIssues = () => {
        // 1. Chuẩn hóa tất cả các trường input, textarea, select thiếu name, id, hoặc aria-label
        const formFields = document.querySelectorAll(
            "input:not([data-a11y-checked]), textarea:not([data-a11y-checked]), select:not([data-a11y-checked])"
        );

        formFields.forEach((el) => {
            el.setAttribute("data-a11y-checked", "true");
            fieldCounter++;

            // Bổ sung name nếu thiếu
            if (!el.getAttribute("name")) {
                const baseName = el.placeholder || el.getAttribute("aria-label") || el.className?.split(" ")[0] || "field";
                const cleanName = baseName.toLowerCase().replace(/[^a-z0-9]/g, "_").replace(/^_+|_+$/g, "") || "field";
                el.setAttribute("name", `${cleanName}_${fieldCounter}`);
            }

            // Bổ sung id nếu thiếu
            if (!el.getAttribute("id")) {
                el.setAttribute("id", `o_a11y_field_${fieldCounter}`);
            }

            // Bổ sung aria-label nếu thiếu và không có label liên kết
            const hasLabel = el.id && document.querySelector(`label[for="${el.id}"]`);
            if (!el.getAttribute("aria-label") && !hasLabel) {
                const labelText = el.placeholder || el.title || el.getAttribute("name") || "Nhập dữ liệu";
                el.setAttribute("aria-label", labelText);
            }
        });

        // 2. Chuẩn hóa thẻ <label for="xxx"> trong trang Settings nếu ID chưa khớp
        document.querySelectorAll("label[for]").forEach((label) => {
            const targetId = label.getAttribute("for");
            if (targetId && !document.getElementById(targetId)) {
                const input = label.querySelector("input") || label.parentElement?.querySelector("input");
                if (input && (!input.id || input.id.startsWith("o_a11y_field_"))) {
                    input.id = targetId;
                }
            }
        });
    };

    const debouncedFix = () => {
        if (a11yTimeout) {
            cancelAnimationFrame(a11yTimeout);
        }
        a11yTimeout = requestAnimationFrame(fixAccessibilityIssues);
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", debouncedFix);
    } else {
        debouncedFix();
    }

    // Lắng nghe thay đổi DOM khi chuyển trang / mở popup trong Odoo
    const observer = new MutationObserver(debouncedFix);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true,
    });
}


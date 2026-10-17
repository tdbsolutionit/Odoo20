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

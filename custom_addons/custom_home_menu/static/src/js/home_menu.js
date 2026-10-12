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
        if (app.webIconData) {
            return app.webIconData.startsWith("data:") || app.webIconData.startsWith("/")
                ? app.webIconData
                : `data:image/png;base64,${app.webIconData}`;
        }
        if (app.webIcon && typeof app.webIcon === "string" && app.webIcon.includes("/")) {
            const parts = app.webIcon.split(",");
            return `/${parts[0]}/${parts[1]}`;
        }
        return `/web/image/ir.ui.menu/${app.id}/web_icon_data`;
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

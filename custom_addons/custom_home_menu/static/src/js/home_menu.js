/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { useListener, onWillUnmount } from "@odoo/owl";

patch(NavBar.prototype, {
    setup() {
        super.setup();

        // 1. Kiểm tra trạng thái đăng nhập hoặc landing mặc định để mở ngay Home Menu
        const isFromLogin =
            sessionStorage.getItem("tdb_open_home_menu") === "true" ||
            (document.referrer && document.referrer.includes("/web/login"));

        const isDefaultLanding =
            window.location.pathname === "/odoo/discuss" ||
            window.location.pathname === "/odoo" ||
            window.location.pathname === "/odoo/" ||
            window.location.pathname === "/web" ||
            window.location.pathname === "/web/" ||
            !window.location.hash ||
            window.location.hash === "#" ||
            window.location.hash.includes("action=mail.action_discuss");

        const shouldOpenHomeMenu = isFromLogin || isDefaultLanding;

        if (sessionStorage.getItem("tdb_open_home_menu")) {
            sessionStorage.removeItem("tdb_open_home_menu");
        }

        this.state.isHomeMenuOpened = Boolean(shouldOpenHomeMenu);
        this.state.searchQuery = "";
        this.state.currentDateTime = this.getFormattedDateTime();

        if (this.state.isHomeMenuOpened) {
            this._suppressMenuAppChanged = true;
            document.title = "TDB Solution";
            setTimeout(() => {
                this._suppressMenuAppChanged = false;
            }, 1000);
            setTimeout(() => {
                const input = document.querySelector(".o_home_menu_search_input");
                input?.focus();
            }, 120);
        }

        // Tự động cập nhật ngày giờ thời gian thực mỗi giây
        if (this.dateTimeTimer) {
            clearInterval(this.dateTimeTimer);
        }
        this.dateTimeTimer = setInterval(() => {
            if (this.state.isHomeMenuOpened) {
                this.state.currentDateTime = this.getFormattedDateTime();
            }
        }, 1000);

        try {
            if (typeof onWillUnmount === "function") {
                onWillUnmount(() => {
                    if (this.dateTimeTimer) {
                        clearInterval(this.dateTimeTimer);
                        this.dateTimeTimer = null;
                    }
                });
            }
        } catch (e) {
            // Safe fallback
        }

        useListener(window, "keydown", (ev) => {
            if (this.state.isHomeMenuOpened && ev.key === "Escape") {
                this.state.isHomeMenuOpened = false;
                this.state.searchQuery = "";
            }
        });

        useListener(this.env.bus, "MENUS:APP-CHANGED", () => {
            if (this._suppressMenuAppChanged) {
                return;
            }
            this.state.isHomeMenuOpened = false;
            this.state.searchQuery = "";
        });
    },

    getFormattedDateTime() {
        const now = new Date();
        const days = [
            "Chủ Nhật",
            "Thứ Hai",
            "Thứ Ba",
            "Thứ Tư",
            "Thứ Năm",
            "Thứ Sáu",
            "Thứ Bảy",
        ];
        const day = days[now.getDay()];
        const pad = (n) => String(n).padStart(2, "0");
        const d = pad(now.getDate());
        const m = pad(now.getMonth() + 1);
        const y = now.getFullYear();
        const hours = pad(now.getHours());
        const minutes = pad(now.getMinutes());
        const seconds = pad(now.getSeconds());
        return `${day}, ${d}/${m}/${y} - ${hours}:${minutes}:${seconds}`;
    },

    toggleHomeMenu(force) {
        this.state.isHomeMenuOpened =
            typeof force === "boolean" ? force : !this.state.isHomeMenuOpened;
        this.state.searchQuery = "";
        if (this.state.isHomeMenuOpened) {
            this.state.currentDateTime = this.getFormattedDateTime();
            document.title = "TDB Solution";
            setTimeout(() => {
                const input = document.querySelector(".o_home_menu_search_input");
                input?.focus();
            }, 60);
        }
    },

    onAppClick(app) {
        this._suppressMenuAppChanged = false;
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


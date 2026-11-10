/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { useListener, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { user } from "@web/core/user";
import { rpc } from "@web/core/network/rpc";

patch(NavBar.prototype, {
    setup() {
        super.setup();

        try {
            this.rpc = useService("rpc");
        } catch (e) {
            this.rpc = null;
        }

        // 1. Kiểm tra trạng thái tải trang (F5/Reload vs Điều hướng mới/Đăng nhập)
        const navEntries =
            typeof performance !== "undefined" && performance.getEntriesByType
                ? performance.getEntriesByType("navigation")
                : [];
        const isPageReload =
            (navEntries.length > 0 && navEntries[0].type === "reload") ||
            (typeof performance !== "undefined" &&
                performance.navigation &&
                performance.navigation.type === 1);

        // Kiểm tra xem trước khi tải lại trang người dùng có đang chủ động mở Home Menu hay không
        const wasHomeMenuExplicitlyOpen =
            sessionStorage.getItem("tdb_home_menu_active") === "true";

        // Kiểm tra đăng nhập mới từ trang login
        const isFreshLogin = sessionStorage.getItem("tdb_open_home_menu") === "true";
        if (isFreshLogin) {
            sessionStorage.removeItem("tdb_open_home_menu");
        }

        // Kiểm tra đường dẫn có phải trang gốc không (chỉ root /odoo, /web và không có action/model cụ thể)
        const pathname = (window.location.pathname || "").replace(/\/+$/, "") || "/";
        const isBareRoot = pathname === "/odoo" || pathname === "/web" || pathname === "";
        const hasSpecificActionOrTarget =
            Boolean(window.location.search && window.location.search.length > 1) ||
            Boolean(window.location.hash && window.location.hash.length > 1 && window.location.hash !== "#");

        let shouldOpenHomeMenu = false;
        if (isPageReload) {
            // Khi F5 / Reload: GIỮ NGUYÊN TRANG HIỆN TẠI!
            // Chỉ mở Home Menu nếu trước đó người dùng thực sự đang đứng ở màn hình Home Menu
            shouldOpenHomeMenu = wasHomeMenuExplicitlyOpen;
        } else if (isFreshLogin) {
            shouldOpenHomeMenu = !hasSpecificActionOrTarget;
        } else if (isBareRoot && !hasSpecificActionOrTarget) {
            shouldOpenHomeMenu = true;
        } else {
            shouldOpenHomeMenu = false;
        }

        this.state.isHomeMenuOpened = Boolean(shouldOpenHomeMenu);
        this.state.searchQuery = "";
        this.state.currentDateTime = this.getFormattedDateTime();

        if (this.state.isHomeMenuOpened) {
            sessionStorage.setItem("tdb_home_menu_active", "true");
            this._suppressMenuAppChanged = true;
            document.title = "TDB Solution";
            setTimeout(() => {
                this._suppressMenuAppChanged = false;
            }, 1000);
            setTimeout(() => {
                const input = document.querySelector(".o_home_menu_search_input");
                input?.focus();
            }, 120);
        } else {
            sessionStorage.removeItem("tdb_home_menu_active");
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
                this.toggleHomeMenu(false);
            }
        });

        useListener(this.env.bus, "MENUS:APP-CHANGED", () => {
            if (this._suppressMenuAppChanged) {
                return;
            }
            this.toggleHomeMenu(false);
        });
    },

    getFormattedDateTime() {
        const now = new Date();
        const isEn = this.currentLanguage === "EN";
        const daysVi = [
            "Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"
        ];
        const daysEn = [
            "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
        ];
        const day = isEn ? daysEn[now.getDay()] : daysVi[now.getDay()];
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
            sessionStorage.setItem("tdb_home_menu_active", "true");
            this.state.currentDateTime = this.getFormattedDateTime();
            document.title = "TDB Solution";
            setTimeout(() => {
                const input = document.querySelector(".o_home_menu_search_input");
                input?.focus();
            }, 60);
        } else {
            sessionStorage.removeItem("tdb_home_menu_active");
        }
    },

    onAppClick(app) {
        this._suppressMenuAppChanged = false;
        this.state.isHomeMenuOpened = false;
        this.state.searchQuery = "";
        sessionStorage.removeItem("tdb_home_menu_active");
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

    get currentLanguage() {
        let lang = "";
        try {
            lang = (user && user.lang) || (user && user.context && user.context.lang);
        } catch (e) {}

        if (!lang) {
            try {
                if (this.env && this.env.services && this.env.services.user && this.env.services.user.context) {
                    lang = this.env.services.user.context.lang;
                }
            } catch (e) {}
        }

        if (!lang) {
            try {
                if (window.odoo && window.odoo.loader && window.odoo.loader.modules) {
                    const userMod = window.odoo.loader.modules.get("@web/core/user");
                    if (userMod && userMod.user && userMod.user.context) {
                        lang = userMod.user.context.lang;
                    }
                }
            } catch (e) {}
        }

        if (!lang) {
            try {
                lang = session && session.user_context && session.user_context.lang;
            } catch (e) {}
        }

        if (!lang) {
            const m = document.cookie.match(/(?:^|;\s*)frontend_lang=([^;]+)/);
            if (m) {
                lang = decodeURIComponent(m[1]);
            }
        }

        if (!lang) {
            lang = document.documentElement.getAttribute("lang") || "";
        }

        lang = (lang || "").toLowerCase();
        return lang.startsWith("en") ? "EN" : "VI";
    },

    async switchLanguage(targetLangCode) {
        const lang = targetLangCode === "VI" ? "vi_VN" : "en_US";
        try {
            document.cookie = "frontend_lang=" + lang + ";path=/;max-age=" + (365 * 24 * 3600);
            if (typeof rpc === "function") {
                await rpc("/web/session/switch_language", { lang: lang });
            } else if (this.rpc) {
                await this.rpc("/web/session/switch_language", { lang: lang });
            }
        } catch (e) {
            console.warn("Lưu ý switch_language:", e);
        }
        window.location.href = "/web/session/switch_language_http?lang=" + lang + "&redirect=" + encodeURIComponent(window.location.pathname + window.location.search + window.location.hash);
    },
});


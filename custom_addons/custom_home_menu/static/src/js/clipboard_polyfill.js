/** @odoo-module **/

/**
 * Polyfill cho navigator.clipboard tren HTTP / Insecure Context.
 * Giup cac tinh nang Copy, Tour, Error Dialog cua Odoo 20 khong bi crash
 * khi truy cap qua dia chi IP mang noi bo (vi du: http://192.168.x.x:8080).
 */
(function initClipboardPolyfill() {
    if (typeof window === "undefined" || !window.navigator) {
        return;
    }

    if (!window.navigator.clipboard) {
        const polyfill = {
            writeText: async function (text) {
                const str = text !== undefined && text !== null ? String(text) : "";
                const textArea = document.createElement("textarea");
                textArea.value = str;
                textArea.style.position = "fixed";
                textArea.style.top = "-9999px";
                textArea.style.left = "-9999px";
                textArea.style.opacity = "0";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {
                    document.execCommand("copy");
                } catch (e) {
                    console.warn("[ClipboardPolyfill] execCommand copy failed:", e);
                } finally {
                    document.body.removeChild(textArea);
                }
            },
            readText: async function () {
                return "";
            },
        };

        try {
            Object.defineProperty(window.navigator, "clipboard", {
                value: polyfill,
                configurable: true,
                writable: true,
                enumerable: true,
            });
        } catch (e) {
            try {
                window.navigator.clipboard = polyfill;
            } catch (err) {}
        }
    }
})();

/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FontSizeSelector } from "@html_editor/main/font/font_size_selector";

patch(FontSizeSelector.prototype, {
    stepFontSize(delta) {
        let current = parseInt(this.state?.displayName, 10);
        if (isNaN(current) || current <= 0) {
            current = 11;
        }
        let next = current + delta;
        if (next < 6) next = 6;
        if (next > (this.props?.maxFontSize || 144)) next = this.props?.maxFontSize || 144;
        if (this.state) {
            this.state.displayName = next;
        }
        this.props?.onFontSizeInput?.(`${next}px`);
    },
});

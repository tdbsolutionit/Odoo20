/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Wysiwyg } from "@html_editor/wysiwyg";
import { onMounted, proxy } from "@odoo/owl";
import { render } from "@web/owl2/utils";
import { htmlField } from "@html_editor/fields/html_field";

// Kế thừa htmlField để chuyển options top_toolbar vào editorConfig
if (htmlField?.extractProps) {
    const origExtractProps = htmlField.extractProps;
    htmlField.extractProps = function ({ attrs, options, viewType }) {
        const props = origExtractProps(...arguments);
        if (props) {
            props.editorConfig = props.editorConfig || {};
            if ("top_toolbar" in (options || {})) {
                props.editorConfig.top_toolbar = Boolean(options.top_toolbar);
            }
        }
        return props;
    };
}

patch(Wysiwyg.prototype, {
    setup() {
        super.setup(...arguments);
        this.state = proxy({
            isMounted: false,
        });

        onMounted(() => {
            this.state.isMounted = true;
            if (this.showStationaryToolbar) {
                render(this);
            }
        });
    },

    get isInsideModal() {
        const el = this.contentRef?.();
        return Boolean(el?.closest?.(".modal, .modal-dialog, .o_dialog, .modal-content"));
    },

    get showStationaryToolbar() {
        // Chỉ hiển thị stationary toolbar nếu editor có cấu hình top_toolbar: true
        // HOẶC editor này thực sự nằm BÊN TRONG modal/dialog popup.
        // Tuyệt đối không hiển thị ở ngoài màn hình chính (sale order form).
        return Boolean(this.props?.config?.top_toolbar || this.isInsideModal);
    },

    get toolbarProps() {
        if (!this.editor?.plugins) {
            return null;
        }
        const tbPlugin = this.editor.plugins.find(
            (p) => p.toolbarProps || p.constructor.id === "toolbar" || p.constructor.name === "ToolbarPlugin"
        );
        if (tbPlugin?.toolbarProps) {
            if (!tbPlugin.state.namespace) {
                tbPlugin.state.namespace = "expanded";
            }
            tbPlugin.isToolbarExpanded = true;
            if (!tbPlugin.state.buttonGroups || tbPlugin.state.buttonGroups.length === 0) {
                tbPlugin.updateButtonsStates?.();
            }
            return tbPlugin.toolbarProps;
        }
        return null;
    },
});

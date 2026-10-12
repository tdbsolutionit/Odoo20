// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {BinaryField} from "@web/views/fields/binary/binary_field";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class PreviewRecordField extends BinaryField {
    static template = "dms.FilePreviewField";

    setup() {
        super.setup();
        this.action = useService("action");
    }

    onFilePreview() {
        this.action.doAction({
            name: this.props.record.data.display_name || this.props.record.data.name || _t("Xem trước tài liệu"),
            type: "ir.actions.act_window",
            res_model: this.props.record.resModel || "dms.file",
            res_id: this.props.record.resId,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }
}

const previewRecordField = {
    component: PreviewRecordField,
    displayName: _t("Preview Record"),
    supportedTypes: ["binary"],
    extractProps: () => {
        return {};
    },
};
registry.category("fields").add("preview_binary", previewRecordField);

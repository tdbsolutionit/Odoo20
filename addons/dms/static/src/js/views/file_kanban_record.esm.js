// /** ********************************************************************************
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {KanbanRecord} from "@web/views/kanban/kanban_record";
import {useService} from "@web/core/utils/hooks";

export class FileKanbanRecord extends KanbanRecord {
    setup() {
        super.setup();
        this.action = useService("action");
    }

    /**
     * @override
     *
     * Override to open the record preview upon clicking the image / preview icon or preview button.
     */
    onGlobalClick(ev) {
        if (
            ev.target.closest(".o_kanban_dms_file_preview") ||
            ev.target.closest("button[name='action_preview_file']") ||
            ev.target.closest(".o_dms_preview_btn")
        ) {
            ev.stopPropagation();
            ev.preventDefault();
            if (this.props.openRecord) {
                this.props.openRecord(this.props.record);
                return;
            }
            this.action.doAction({
                name: this.props.record.data.name || "",
                type: "ir.actions.act_window",
                res_model: this.props.record.resModel || "dms.file",
                res_id: this.props.record.data.id,
                view_mode: "form",
                views: [[false, "form"]],
                target: "current",
            });
            return;
        }
        return super.onGlobalClick(ev);
    }
}


// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {ListRenderer} from "@web/views/list/list_renderer";
import {useEffect, proxy} from "@odoo/owl";

export class FileListRenderer extends ListRenderer {
    get dragState() {
        if (!this._dragState) {
            this._dragState = proxy({ showDragZone: false });
        }
        return this._dragState;
    }
    set dragState(val) {
        this._dragState = val;
    }

    setup() {
        super.setup();
        // Drag-drop zone state - direct class property (OWL 3 compatible)
        this._dragState = proxy({
            showDragZone: false,
        });
        useEffect(
            (el) => {
                if (!el) return;
                const highlight = (ev) => {
                    ev.stopPropagation();
                    ev.preventDefault();
                    this.dragState.showDragZone = true;
                };
                const unhighlight = (ev) => {
                    ev.stopPropagation();
                    ev.preventDefault();
                    this.dragState.showDragZone = false;
                };
                const drop = async (ev) => {
                    ev.preventDefault();
                    this.dragState.showDragZone = false;
                    await this.env.bus.trigger("change_file_input", {
                        files: ev.dataTransfer.files,
                    });
                };
                el.addEventListener("dragover", highlight);
                el.addEventListener("dragleave", unhighlight);
                el.addEventListener("drop", drop);
                return () => {
                    el.removeEventListener("dragover", highlight);
                    el.removeEventListener("dragleave", unhighlight);
                    el.removeEventListener("drop", drop);
                };
            },
            () => [document.querySelector(".o_content")]
        );
    }
}

FileListRenderer.components = {
    ...ListRenderer.components,
};

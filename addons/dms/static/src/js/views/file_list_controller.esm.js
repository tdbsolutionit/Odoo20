// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2017-2019 MuK IT GmbH
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/
import {ListController} from "@web/views/list/list_controller";
import {useBus, useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";
import {signal} from "@odoo/owl";

export class FileListController extends ListController {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.http = useService("http");
        this.fileInput = signal.ref();

        useBus(this.env.bus, "change_file_input", async () => {
            await this.onChangeFileInput();
        });
    }

    uploadDocument() {
        const input = this.fileInput();
        if (input) {
            input.click();
        }
    }

    async onChangeFileInput() {
        const input = this.fileInput();
        if (!input || !input.files || !input.files.length) return;

        // Search the correct directory_id value according to the domain
        let directory_id = false;
        if (this.props.domain) {
            for (const domain_item of this.props.domain) {
                if (domain_item.length === 3) {
                    if (
                        domain_item[0] === "directory_id" &&
                        ["=", "child_of"].includes(domain_item[1])
                    ) {
                        directory_id = domain_item[2];
                    }
                }
            }
        }

        if (directory_id === false) {
            return this.notification.add(_t("You must select a directory first"), {
                type: "danger",
            });
        }

        const params = {
            csrf_token: odoo.csrf_token,
            ufile: [...input.files],
            directory_id: directory_id,
        };

        const fileData = await this.http.post(
            "/web/binary/upload_dms_file",
            params,
            "text"
        );
        const result = JSON.parse(fileData);
        if (result.error) {
            throw new Error(result.error);
        }
        this.model.load();
    }
}

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

        useBus(this.env.bus, "change_file_input", async (ev) => {
            await this.onChangeFileInput(ev);
        });
    }

    get canCreate() {
        return this.activeActions?.create;
    }

    _getDirectoryId() {
        // 1. Check SearchModel categories (SearchPanel)
        if (this.env.searchModel?.categories) {
            for (const category of this.env.searchModel.categories) {
                if (category.fieldName === "directory_id" && category.activeValueId) {
                    return category.activeValueId;
                }
            }
        }

        // 2. Check domains (searchModel, model.root, props)
        const domains = [
            this.env.searchModel?.domain,
            this.model?.root?.domain,
            this.props?.domain,
        ];

        for (const dom of domains) {
            if (!dom || !Array.isArray(dom)) continue;
            for (const item of dom) {
                if (Array.isArray(item) && item.length === 3) {
                    if (
                        item[0] === "directory_id" &&
                        ["=", "child_of"].includes(item[1]) &&
                        item[2]
                    ) {
                        return item[2];
                    }
                }
            }
        }

        return false;
    }

    uploadDocument() {
        const directory_id = this._getDirectoryId();
        if (!directory_id) {
            return this.notification.add(_t("Vui lòng chọn thư mục trước khi tải lên"), {
                type: "danger",
            });
        }
        const input = this.fileInput();
        if (input) {
            input.click();
        }
    }

    openDateFilterWizard() {
        const directoryId = this._getDirectoryId();
        this.actionService.doAction({
            name: _t("Lọc tệp tin theo khoảng thời gian"),
            type: "ir.actions.act_window",
            res_model: "dms.file.date.filter.wizard",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_directory_id: directoryId || false,
            },
        });
    }

    async onChangeFileInput(ev) {
        let files = null;
        if (ev?.detail?.files) {
            files = ev.detail.files;
        } else if (ev?.target?.files) {
            files = ev.target.files;
        } else {
            const input = this.fileInput();
            if (input && input.files) {
                files = input.files;
            }
        }

        if (!files || !files.length) return;

        const directory_id = this._getDirectoryId();
        if (!directory_id) {
            return this.notification.add(_t("Vui lòng chọn thư mục trước khi tải lên"), {
                type: "danger",
            });
        }

        const params = {
            csrf_token: odoo.csrf_token,
            ufile: [...files],
            directory_id: directory_id,
        };

        try {
            const fileData = await this.http.post(
                "/web/binary/upload_dms_file",
                params,
                "text"
            );
            let result;
            try {
                result = typeof fileData === "string" ? JSON.parse(fileData) : fileData;
            } catch (err) {
                return this.notification.add(
                    _t("Máy chủ trả về kết quả không hợp lệ hoặc bạn không có đủ quyền hạn."),
                    {type: "danger"}
                );
            }

            let errorMsg = null;
            if (Array.isArray(result)) {
                const err = result.find((item) => item.error);
                if (err) {
                    errorMsg = err.error;
                }
            } else if (result?.error) {
                errorMsg = result.error;
            }

            if (errorMsg) {
                return this.notification.add(errorMsg, {
                    type: "danger",
                });
            }

            // Clear input so selecting the same file again triggers change
            const input = this.fileInput();
            if (input) {
                input.value = "";
            }

            await this.model.load();
            this.notification.add(_t("Tải tài liệu lên thành công"), {
                type: "success",
            });
        } catch (e) {
            this.notification.add(e.message || _t("Không thể tải tài liệu lên"), {
                type: "danger",
            });
        }
    }
}

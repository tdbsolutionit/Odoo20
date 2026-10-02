// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2017-2019 MuK IT GmbH
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/

import {FileListController} from "./file_list_controller.esm";
import {FileListRenderer} from "./file_list_renderer.esm";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

FileListRenderer.template = "dms.ListRenderer";

export const FileListView = {
    ...listView,
    Controller: FileListController,
    buttonTemplate: "dms.ListButtons",
    Renderer: FileListRenderer,
};

registry.category("views").add("file_list", FileListView);

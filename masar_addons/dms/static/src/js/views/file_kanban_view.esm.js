// /** ********************************************************************************
//     Copyright 2020 Creu Blanca
//     Copyright 2017-2019 MuK IT GmbH
//     Copyright 2024 Subteno - Timothée Vannier (https://www.subteno.com).
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//  **********************************************************************************/

import {
    createFileDropZoneExtension,
    createFileUploadExtension,
} from "./dms_file_upload.esm";
import {FileKanbanRenderer} from "./file_kanban_renderer.esm";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {patch} from "@web/core/utils/patch";
import {registry} from "@web/core/registry";

export class FileKanbanController extends KanbanController {}

patch(FileKanbanRenderer.prototype, createFileDropZoneExtension());
patch(FileKanbanController.prototype, createFileUploadExtension());
FileKanbanRenderer.template = "dms.KanbanRenderer";

export const FileKanbanView = {
    ...kanbanView,
    Controller: FileKanbanController,
    buttonTemplate: "dms.KanbanButtons",
    Renderer: FileKanbanRenderer,
};

registry.category("views").add("file_kanban", FileKanbanView);

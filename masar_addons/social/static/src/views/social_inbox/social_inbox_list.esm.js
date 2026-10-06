/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { SocialPlatformFilter } from "./platform_filter.esm";

export class SocialInboxListRenderer extends ListRenderer {
    static template = "social.InboxListRenderer";
    static components = {
        ...ListRenderer.components,
        SocialPlatformFilter,
    };
}

export const socialInboxListView = {
    ...listView,
    Renderer: SocialInboxListRenderer,
};

registry.category("views").add("social_inbox_list", socialInboxListView);

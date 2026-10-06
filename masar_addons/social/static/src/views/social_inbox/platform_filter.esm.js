/** @odoo-module **/

import { Component, onWillStart, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

const PLATFORM_FALLBACK_ICON = "/web/static/img/smiling_face.svg";

export class SocialPlatformFilter extends Component {
    static template = "social.PlatformFilter";

    setup() {
        this.orm = useService("orm");
        this.state = proxy({
            platforms: [],
            active: "all",
        });
        onWillStart(async () => {
            try {
                this.state.platforms = await this.orm.call(
                    "social.conversation",
                    "_inbox_platforms",
                    []
                );
            } catch {
                this.state.platforms = [];
            }
        });
    }

    get searchModel() {
        return this.env.searchModel;
    }

    _clearPlatformFilters() {
        const items = this.searchModel.getSearchItems(
            (item) => item.socialPlatformFilter
        );
        for (const item of items) {
            if (item.isActive) {
                this.searchModel.toggleSearchItem(item.id);
            }
        }
    }

    onSelectAll() {
        this._clearPlatformFilters();
        this.state.active = "all";
    }

    onSelectPlatform(mediaType) {
        this._clearPlatformFilters();
        if (mediaType && mediaType !== "all") {
            this.searchModel.createNewFilters([
                {
                    description: mediaType,
                    domain: [["platform", "=", mediaType]],
                    socialPlatformFilter: true,
                },
            ]);
        }
        this.state.active = mediaType || "all";
    }

    platformIcon(platform) {
        return platform.image_url || PLATFORM_FALLBACK_ICON;
    }
}

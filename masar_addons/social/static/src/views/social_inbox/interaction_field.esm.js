/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const KIND_META = {
    private: { label: "MESSAGE", icon: "fa fa-envelope", css: "o_social_kind_message" },
    comment: { label: "COMMENT", icon: "fa fa-comment", css: "o_social_kind_comment" },
    mention: { label: "MENTION", icon: "fa fa-at", css: "o_social_kind_mention" },
    review: { label: "REVIEW", icon: "fa fa-star", css: "o_social_kind_review" },
};

const PLATFORM_ICONS = {
    facebook: "/social/static/src/img/facebook.svg",
    instagram: "/social/static/src/img/instagram.svg",
    telegram: "/social/static/src/img/telegram.svg",
};

export class SocialInteractionField extends Component {
    static template = "social.InteractionField";
    static props = { ...standardFieldProps };

    get record() {
        return this.props.record;
    }

    get customerName() {
        return this.record.data.name || "";
    }

    get preview() {
        return this.record.data.preview || "";
    }

    get platform() {
        return this.record.data.platform || "unconfigured";
    }

    get kind() {
        return this.record.data.kind || "private";
    }

    get kindMeta() {
        return KIND_META[this.kind] || KIND_META.private;
    }

    get needsReply() {
        return Boolean(this.record.data.needs_reply);
    }

    get partnerId() {
        const partner = this.record.data.partner_id;
        if (!partner) {
            return false;
        }
        return Array.isArray(partner) ? partner[0] : partner;
    }

    get avatarUrl() {
        if (this.partnerId) {
            return `/web/image/res.partner/${this.partnerId}/avatar_128`;
        }
        return false;
    }

    get initials() {
        const parts = this.customerName.trim().split(/\s+/).filter(Boolean);
        if (!parts.length) {
            return "?";
        }
        if (parts.length === 1) {
            return parts[0].slice(0, 2).toUpperCase();
        }
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }

    get platformIcon() {
        return PLATFORM_ICONS[this.platform] || false;
    }
}

registry.category("fields").add("social_interaction", {
    component: SocialInteractionField,
    displayName: "Social Interaction",
    supportedTypes: ["char"],
});

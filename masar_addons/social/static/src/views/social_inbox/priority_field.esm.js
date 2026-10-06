/** @odoo-module **/

import { Component, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const LABELS = {
    "0": "Low",
    "1": "Medium",
    "2": "High",
};

export class SocialPriorityField extends Component {
    static template = "social.PriorityField";
    props = useProps({ ...standardFieldProps });

    get value() {
        return this.props.record.data[this.props.name] || "0";
    }

    get label() {
        return LABELS[this.value] || this.value;
    }
}

registry.category("fields").add("social_priority", {
    component: SocialPriorityField,
    displayName: "Social Priority",
    supportedTypes: ["selection"],
});

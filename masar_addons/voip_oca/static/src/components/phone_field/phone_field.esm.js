/*
    Copyright 2025 Dixmit
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/
import {PhoneField} from "@web/views/fields/phone/phone_field";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(PhoneField.prototype, {
    setup() {
        super.setup();
        this.agent = useService("voip_agent_oca");
    },
    onLinkClicked() {
        if (!this.agent.agent) {
            return super.onLinkClicked();
        }
        this.agent.call({number: this.dialNumber});
    },
});

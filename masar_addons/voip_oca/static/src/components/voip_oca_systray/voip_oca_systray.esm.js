/*
    Copyright 2025 Dixmit
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/
import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class VoipOCASystray extends Component {
    static template = "voip_oca.VoipOCASystray";
    setup() {
        // voip_oca service is already reactive via proxy().
        this.voip_oca = useService("voip_oca");
    }
    onClick() {
        this.voip_oca.handleVoip();
    }
}
registry.category("systray").add("voip_systray_oca", {Component: VoipOCASystray});

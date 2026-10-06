/*
    Copyright 2025 Dixmit
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/
import {Component, onMounted, signal, t, useProps} from "@odoo/owl";
import {useSelection} from "@mail/utils/common/hooks";
import {useService} from "@web/core/utils/hooks";

export class Numpad extends Component {
    static template = "voip_oca.Numpad";
    props = useProps({
        onNumpadValue: t.function().optional(() => {}),
        onCall: t.function().optional(() => {}),
    });
    setup() {
        super.setup();
        this.keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"];
        this.voip = useService("voip_oca");
        this.numpadValue = signal.ref();
        this.selectionNumpad = useSelection({
            ref: this.numpadValue,
            model: this.voip.numpad.selection,
        });
        onMounted(() => this.numpadValue()?.focus());
    }

    onKeyClick(key) {
        const {value} = this.voip.numpad;
        const el = this.numpadValue();
        if (!el) {
            return;
        }
        const {selectionStart, selectionEnd} = el;
        this.voip.numpad.value =
            value.slice(0, selectionStart) + key + value.slice(selectionEnd);
        el.focus();
        this.selectionNumpad.restore();
        this.onNumpadValue({key});
    }

    onNumpadValue(ev) {
        const {value} = this.voip.numpad;
        if (ev.key === "Enter" && value.length > 0) {
            this.props.onCall();
            return;
        }
        this.props.onNumpadValue(ev.key);
    }

    deleteNumber() {
        const {value} = this.voip.numpad;
        if (value.length > 0) {
            this.voip.numpad.value = value.slice(0, -1);
        }
    }
}

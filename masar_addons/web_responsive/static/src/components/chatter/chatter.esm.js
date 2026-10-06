/* Copyright 2021 ITerra - Sergey Shebanin
 * Copyright 2023 Onestein - Anjeel Haria
 * Copyright 2023 Taras Shabaranskyi
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {Chatter} from "@mail/chatter/web_portal_project/chatter";
import {patch} from "@web/core/utils/patch";
import {useEffect} from "@odoo/owl";

patch(Chatter.prototype, {
    setup() {
        super.setup();
        // Odoo 20 renamed attachment-box state to activePanel; keep a
        // defensive no-op so older scrollIntoView races cannot crash.
        useEffect(this._resetScrollToAttachmentsEffect.bind(this), () => [
            this.state.activePanel ?? this.state.isAttachmentBoxOpened,
        ]);
    },
    /**
     * Prevent scrollIntoView error
     * @param {Boolean|String} attachmentPanel
     * @private
     */
    _resetScrollToAttachmentsEffect(attachmentPanel) {
        const closed =
            attachmentPanel === false ||
            attachmentPanel === undefined ||
            attachmentPanel === "NONE" ||
            attachmentPanel === this.CHATTER_PANEL?.NONE;
        if (closed && "scrollToAttachments" in (this.state || {})) {
            this.state.scrollToAttachments = 0;
        }
    },
});

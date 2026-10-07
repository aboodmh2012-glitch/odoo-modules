/** @odoo-module **/

/**
 * Helpdesk portal attachment size check.
 * Odoo 20 dropped @web/legacy/js/public/public_widget — keep this as a
 * frontend asset without that missing import (it crashed the module loader).
 */
import {_t} from "@web/core/l10n/translation";
import {humanNumber} from "@web/core/utils/numbers";

function bindNewTicketForm(root) {
    const form = root.querySelector("form[action='/submitted/ticket']");
    if (!form || form.dataset.masarTicketBound) {
        return;
    }
    form.dataset.masarTicketBound = "1";
    form.addEventListener("change", (ev) => {
        if (!ev.target || ev.target.getAttribute("name") !== "attachment") {
            return;
        }
        ev.preventDefault();
        const attachmentInput = form.querySelector("#attachment") || document.getElementById("attachment");
        const informationInput =
            form.querySelector("#attachment_information") ||
            document.getElementById("attachment_information");
        if (!attachmentInput || !informationInput) {
            return;
        }
        informationInput.style.display = "none";
        const maxUploadSize = parseInt(attachmentInput.getAttribute("max_upload_size"), 10);
        const dt = new DataTransfer();
        for (const file of attachmentInput.files) {
            if (file.size > maxUploadSize) {
                informationInput.textContent = _t(
                    "The selected file (%sB) is over the maximum allowed file size (%sB).",
                    humanNumber(file.size),
                    humanNumber(maxUploadSize)
                );
                informationInput.style.display = "";
            } else {
                dt.items.add(file);
            }
        }
        attachmentInput.files = dt.files;
    });
}

function start() {
    bindNewTicketForm(document);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
} else {
    start();
}

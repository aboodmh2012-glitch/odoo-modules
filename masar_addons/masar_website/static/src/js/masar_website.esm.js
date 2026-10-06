/** @odoo-module **/

import {whenReady} from "@odoo/owl";

function revealOnScroll() {
    const nodes = document.querySelectorAll(".masar-reveal");
    if (!nodes.length) {
        return;
    }
    if (!("IntersectionObserver" in window)) {
        nodes.forEach((el) => el.classList.add("is-in"));
        return;
    }
    const io = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-in");
                    io.unobserve(entry.target);
                }
            }
        },
        {rootMargin: "0px 0px -8% 0px", threshold: 0.12}
    );
    nodes.forEach((el) => io.observe(el));
}

function bindHeader() {
    const header = document.querySelector(".masar-header");
    if (!header) {
        return;
    }
    const toggle = header.querySelector(".masar-nav__toggle");
    const nav = header.querySelector(".masar-nav");
    if (toggle && nav) {
        toggle.addEventListener("click", () => {
            const open = header.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
        });
        nav.addEventListener("click", (event) => {
            if (event.target.closest("a")) {
                header.classList.remove("is-open");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    }
    document.addEventListener("click", (event) => {
        if (!header.contains(event.target)) {
            header.classList.remove("is-open");
            if (toggle) {
                toggle.setAttribute("aria-expanded", "false");
            }
        }
    });
}

function bindLanguages() {
    const langs = [...document.querySelectorAll(".masar-lang")];
    if (!langs.length) {
        return;
    }
    const close = (lang) => {
        lang.classList.remove("is-open");
        const button = lang.querySelector(".masar-lang__toggle");
        if (button && button.tagName === "BUTTON") {
            button.setAttribute("aria-expanded", "false");
        }
    };
    langs.forEach((lang) => {
        const button = lang.querySelector(".masar-lang__toggle");
        if (!button || button.tagName !== "BUTTON") {
            return;
        }
        button.addEventListener("click", (event) => {
            event.stopPropagation();
            const willOpen = !lang.classList.contains("is-open");
            langs.forEach(close);
            if (willOpen) {
                lang.classList.add("is-open");
                button.setAttribute("aria-expanded", "true");
            }
        });
    });
    document.addEventListener("click", (event) => {
        langs.forEach((lang) => {
            if (!lang.contains(event.target)) {
                close(lang);
            }
        });
    });
}

function bindFooterMenus() {
    const columns = document.querySelectorAll(".masar-footer__col--menu");
    if (!columns.length || !window.matchMedia) {
        return;
    }
    const compact = window.matchMedia("(max-width: 1199.98px)");
    const sync = () => {
        columns.forEach((col) => {
            const button = col.querySelector(".masar-footer__toggle");
            if (!button) {
                return;
            }
            if (!compact.matches) {
                button.setAttribute("aria-expanded", "true");
                return;
            }
            button.setAttribute("aria-expanded", col.classList.contains("is-open") ? "true" : "false");
        });
    };
    columns.forEach((col) => {
        const button = col.querySelector(".masar-footer__toggle");
        if (!button) {
            return;
        }
        button.addEventListener("click", () => {
            if (!compact.matches) {
                return;
            }
            const open = col.classList.toggle("is-open");
            button.setAttribute("aria-expanded", open ? "true" : "false");
        });
    });
    sync();
    if (compact.addEventListener) {
        compact.addEventListener("change", sync);
    }
}

function bindServiceCarousel() {
    document.querySelectorAll("[data-masar-carousel]").forEach((root) => {
        const track = root.querySelector(".masar-service-grid");
        const prev = root.querySelector(".masar-service-carousel__nav--prev");
        const next = root.querySelector(".masar-service-carousel__nav--next");
        const dots = root.querySelector(".masar-service-carousel__dots");
        if (!track || !prev || !next || !dots) {
            return;
        }
        const cards = [...track.querySelectorAll(".masar-service-card")];
        if (cards.length < 2) {
            return;
        }
        const compact = window.matchMedia("(max-width: 767.98px)");
        const scrollTo = (index, behavior) => {
            const card = cards[Math.min(cards.length - 1, Math.max(0, index))];
            const trackRect = track.getBoundingClientRect();
            const cardRect = card.getBoundingClientRect();
            const delta = cardRect.left + cardRect.width / 2 - (trackRect.left + trackRect.width / 2);
            track.scrollBy({left: delta, behavior: behavior || "smooth"});
        };
        cards.forEach((card, index) => {
            const dot = document.createElement("button");
            dot.type = "button";
            dot.className = "masar-service-carousel__dot";
            dot.setAttribute("aria-label", String(index + 1));
            dot.addEventListener("click", () => scrollTo(index));
            dots.appendChild(dot);
        });
        const activeIndex = () => {
            const trackRect = track.getBoundingClientRect();
            const midpoint = trackRect.left + trackRect.width / 2;
            let best = 0;
            let bestDistance = Infinity;
            cards.forEach((card, index) => {
                const rect = card.getBoundingClientRect();
                const distance = Math.abs(rect.left + rect.width / 2 - midpoint);
                if (distance < bestDistance) {
                    bestDistance = distance;
                    best = index;
                }
            });
            return best;
        };
        const sync = () => {
            if (!compact.matches) {
                return;
            }
            const index = activeIndex();
            dots.querySelectorAll(".masar-service-carousel__dot").forEach((dot, dotIndex) => {
                const on = dotIndex === index;
                dot.classList.toggle("is-active", on);
                dot.setAttribute("aria-current", on ? "true" : "false");
            });
            prev.disabled = index === 0;
            next.disabled = index === cards.length - 1;
        };
        const step = (direction) => scrollTo(activeIndex() + direction);
        prev.addEventListener("click", () => step(-1));
        next.addEventListener("click", () => step(1));
        track.addEventListener("scroll", () => window.requestAnimationFrame(sync), {passive: true});
        sync();
        if (compact.addEventListener) {
            compact.addEventListener("change", sync);
        }
    });
}


function bindJobLinkCopying() {
    document.querySelectorAll(".masar-job-copy").forEach((button) => {
        let busy = false;
        let resetTimer;
        button.addEventListener("click", async () => {
            if (busy) return;
            busy = true;
            const group = button.closest(".masar-job-share-actions");
            const status = group.querySelector(".masar-job-share-status");
            const field = group.querySelector(".masar-job-copy-fallback");
            const icon = button.querySelector(".fa");
            const url = button.dataset.copyUrl;
            let copied = false;
            clearTimeout(resetTimer);
            try {
                if (navigator.clipboard?.writeText) {
                    await navigator.clipboard.writeText(url);
                    copied = true;
                }
            } catch {
                // Browser permissions can reject clipboard access.
            }
            if (!copied) {
                field.hidden = false;
                field.focus();
                field.select();
                field.setSelectionRange(0, field.value.length);
                try {
                    copied = document.execCommand("copy");
                } catch {
                    copied = false;
                }
            }
            field.hidden = copied;
            status.textContent = copied ? button.dataset.copied : button.dataset.copyFailed;
            button.classList.toggle("is-copied", copied);
            icon.classList.toggle("fa-check", copied);
            icon.classList.toggle("fa-link", !copied);
            if (copied) {
                button.focus({preventScroll: true});
                resetTimer = setTimeout(() => {
                    status.textContent = "";
                    button.classList.remove("is-copied");
                    icon.classList.remove("fa-check");
                    icon.classList.add("fa-link");
                }, 3000);
            }
            busy = false;
        });
    });
}

whenReady(() => {
    bindJobLinkCopying();
    revealOnScroll();
    bindHeader();
    bindLanguages();
    bindFooterMenus();
    bindServiceCarousel();
});

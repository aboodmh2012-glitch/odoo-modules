/** @odoo-module **/

/**
 * MASAR Apps Home for Odoo 20.
 *
 * Built on native NavBar / BurgerMenu (Owl 3). No web_responsive dependency.
 * Home is a full-viewport workspace overlay; sections/account drawers stay
 * mutually exclusive with Home.
 */

import {onMounted, signal, useEffect, useListener} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {useBus} from "@web/core/utils/hooks";
import {useHotkey} from "@web/core/hotkeys/hotkey_hook";
import {_t} from "@web/core/l10n/translation";
import {NavBar} from "@web/webclient/navbar/navbar";
import {BurgerMenu} from "@web/webclient/burger_menu/burger_menu";

const OVERLAY_CHANGED = "MASAR_NAVIGATION:OVERLAY_CHANGED";
const FOCUSABLE =
    'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function focusable(root) {
    return root
        ? [...root.querySelectorAll(FOCUSABLE)].filter((el) => el.getClientRects().length)
        : [];
}

function hasNestedOverlay(root) {
    return [
        ...document.querySelectorAll(
            ".o-overlay-container .o_popover, .o-overlay-container .o_dialog, .o-overlay-container .o-dropdown--menu"
        ),
    ].some((el) => el.getClientRects().length && !root?.contains(el));
}

function setupDrawer(component, name, rootRef, isOpen, close) {
    useEffect(
        () => {
            if (isOpen()) {
                focusable(rootRef())[0]?.focus();
            }
        },
        () => [isOpen()]
    );
    useHotkey("Escape", () => close(), {
        area: () => rootRef(),
        isAvailable: () =>
            isOpen() && component.masarOverlay === name && !hasNestedOverlay(rootRef()),
        bypassEditableProtection: true,
    });
    useListener(window, "keydown", (ev) => {
        if (
            ev.key !== "Tab" ||
            !isOpen() ||
            component.masarOverlay !== name ||
            hasNestedOverlay(rootRef())
        ) {
            return;
        }
        const items = focusable(rootRef());
        if (!items.length) {
            return;
        }
        const index = items.indexOf(document.activeElement);
        if (
            index === -1 ||
            (ev.shiftKey && index === 0) ||
            (!ev.shiftKey && index === items.length - 1)
        ) {
            ev.preventDefault();
            (ev.shiftKey ? items[items.length - 1] : items[0]).focus();
        }
    });
}

patch(NavBar.prototype, {
    setup() {
        super.setup();
        Object.assign(this.state, {
            masarHomeOpen: false,
            masarSearch: "",
            masarSectionsOpen: false,
        });
        this.masarOverlay = null;
        this.masarRestoreHomeFocus = false;
        this.masarHome = signal.ref();
        this.masarNavButton = signal.ref();
        this.masarSearchInput = signal.ref();
        this.masarSectionsDrawer = signal.ref();

        useBus(this.env.bus, OVERLAY_CHANGED, ({detail}) => {
            this.masarOverlay = detail;
            this.state.masarSectionsOpen = detail === "sections";
            if (detail && detail !== "sections" && this.state.isAppMenuSidebarOpened) {
                this._closeAppMenuSidebar();
            }
        });

        setupDrawer(
            this,
            "sections",
            () => this.masarSectionsDrawer(),
            () => this.state.isAppMenuSidebarOpened,
            () => this._closeAppMenuSidebar()
        );

        useHotkey(
            "Escape",
            () => this.closeMasarHome({restoreFocus: true}),
            {
                area: () => this.masarHome(),
                isAvailable: () =>
                    this.state.masarHomeOpen &&
                    !this.masarOverlay &&
                    !!this.menuService.getCurrentApp(),
                bypassEditableProtection: true,
            }
        );

        for (const key of ["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp"]) {
            useHotkey(
                key,
                () => {
                    const rtl = document.documentElement.dir === "rtl";
                    const previous =
                        key === "ArrowUp" || key === (rtl ? "ArrowRight" : "ArrowLeft");
                    this._masarMoveAppFocus(previous ? "prev" : "next");
                },
                {
                    area: () => this.masarHome(),
                    isAvailable: () => this.state.masarHomeOpen && !this.masarOverlay,
                    allowRepeat: true,
                }
            );
        }

        useEffect(
            () => {
                document.body.classList.toggle("o_masar_home_opened", this.state.masarHomeOpen);
                if (this.state.masarHomeOpen) {
                    this.masarRestoreHomeFocus = false;
                    queueMicrotask(() => this.masarSearchInput()?.focus());
                } else if (this.masarRestoreHomeFocus) {
                    this.masarRestoreHomeFocus = false;
                    this.masarNavButton()?.focus();
                }
                if (!this.state.masarHomeOpen && !this.ui.isSmall) {
                    this.adapt();
                }
            },
            () => [this.state.masarHomeOpen, this.ui.isSmall]
        );

        onMounted(() => {
            if (this.state.masarHomeOpen) {
                document.body.classList.add("o_masar_home_opened");
            }
        });
    },

    get masarNavigationLabel() {
        if (this.state.masarHomeOpen) {
            return this.menuService.getCurrentApp()
                ? _t("Return to application")
                : _t("All applications");
        }
        return this.ui.isSmall ? _t("Application menu") : _t("All applications");
    },

    get masarFilteredApps() {
        const apps = this.menuService.getApps() || [];
        const query = (this.state.masarSearch || "").trim().toLowerCase();
        if (!query) {
            return apps;
        }
        return apps.filter((app) => (app.name || "").toLowerCase().includes(query));
    },

    openMasarHome() {
        this.env.bus.trigger(OVERLAY_CHANGED, null);
        if (this.state.isAppMenuSidebarOpened) {
            this._closeAppMenuSidebar();
        }
        this.state.masarSearch = "";
        this.state.masarHomeOpen = true;
    },

    closeMasarHome({restoreFocus = false} = {}) {
        if (!this.state.masarHomeOpen) {
            return;
        }
        if (restoreFocus && this.menuService.getCurrentApp()) {
            this.masarRestoreHomeFocus = true;
        }
        this.state.masarHomeOpen = false;
        this.state.masarSearch = "";
    },

    toggleMasarHome() {
        if (this.state.masarHomeOpen) {
            this.closeMasarHome({restoreFocus: true});
            return;
        }
        if (this.ui.isSmall) {
            this._openAppMenuSidebar();
            return;
        }
        this.openMasarHome();
    },

    onAllAppsBtnClick() {
        this._closeAppMenuSidebar();
        this.openMasarHome();
    },

    _openAppMenuSidebar() {
        if (this.state.masarHomeOpen) {
            return;
        }
        if (this.state.isAppMenuSidebarOpened) {
            this._closeAppMenuSidebar();
            return;
        }
        this.env.bus.trigger(OVERLAY_CHANGED, "sections");
        super._openAppMenuSidebar();
    },

    _closeAppMenuSidebar() {
        const wasOpen = this.state.isAppMenuSidebarOpened;
        super._closeAppMenuSidebar();
        if (this.masarOverlay === "sections") {
            this.env.bus.trigger(OVERLAY_CHANGED, null);
        }
        if (wasOpen) {
            this.masarNavButton()?.focus();
        }
    },

    onMasarAppSelected(app) {
        this.closeMasarHome();
        this.onNavBarDropdownItemSelection(app);
    },

    onMasarAppKeydown(ev, app) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            this.onMasarAppSelected(app);
        }
    },

    onMasarSearchInput(ev) {
        this.state.masarSearch = ev.target.value || "";
    },

    clearMasarSearch() {
        this.state.masarSearch = "";
        this.masarSearchInput()?.focus();
    },

    onMasarSearchKeydown(ev) {
        if (ev.code === "Escape") {
            if (this.state.masarSearch) {
                ev.preventDefault();
                this.clearMasarSearch();
                return;
            }
            if (this.menuService.getCurrentApp()) {
                ev.preventDefault();
                this.closeMasarHome({restoreFocus: true});
            }
        }
    },

    _masarMoveAppFocus(direction) {
        const items = [...(this.masarHome()?.querySelectorAll(".o-masar-app-item") || [])].filter(
            (el) => el.getClientRects().length
        );
        if (!items.length) {
            return;
        }
        const index = items.indexOf(document.activeElement);
        const next =
            index < 0
                ? 0
                : (index + (direction === "prev" ? -1 : 1) + items.length) % items.length;
        items[next].focus();
    },

    _onSectionKeydown(ev, section) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            return this._onMenuClicked(section);
        }
    },

    _onSwipeEnd(ev) {
        if (this.swipeStartX == null) {
            return;
        }
        const delta = ev.changedTouches[0].clientX - this.swipeStartX;
        this.swipeStartX = null;
        if ((document.documentElement.dir === "rtl" ? -delta : delta) >= 100) {
            this._closeAppMenuSidebar();
        }
    },
});

patch(BurgerMenu.prototype, {
    setup() {
        super.setup();
        this.masarOverlay = null;
        this.masarAccountDrawer = signal.ref();
        this.masarAccountButton = signal.ref();
        useBus(this.env.bus, OVERLAY_CHANGED, ({detail}) => {
            this.masarOverlay = detail;
            if (detail !== "account" && this.state.isBurgerOpened) {
                this._closeBurger();
            }
        });
        useBus(this.env.bus, "MASAR_NAVIGATION:HOME_CHANGED", ({detail: open}) => {
            if (open && this.state.isBurgerOpened) {
                this._closeBurger();
            }
        });
        setupDrawer(
            this,
            "account",
            () => this.masarAccountDrawer(),
            () => this.state.isBurgerOpened,
            () => this._closeBurger()
        );
    },

    _openBurger() {
        this.env.bus.trigger(OVERLAY_CHANGED, "account");
        super._openBurger();
    },

    _closeBurger() {
        const wasOpen = this.state.isBurgerOpened;
        super._closeBurger();
        if (this.masarOverlay === "account") {
            this.env.bus.trigger(OVERLAY_CHANGED, null);
        }
        if (wasOpen) {
            this.masarAccountButton()?.focus();
        }
    },

    _onSwipeEnd(ev) {
        if (this.swipeStartX == null) {
            return;
        }
        const delta = ev.changedTouches[0].clientX - this.swipeStartX;
        this.swipeStartX = null;
        if ((document.documentElement.dir === "rtl" ? -delta : delta) >= 100) {
            this._closeBurger();
        }
    },
});

// Keep body class in sync when home toggles via NavBar only.
patch(NavBar.prototype, {
    openMasarHome() {
        this.env.bus.trigger("MASAR_NAVIGATION:HOME_CHANGED", true);
        return super.openMasarHome(...arguments);
    },
    closeMasarHome() {
        this.env.bus.trigger("MASAR_NAVIGATION:HOME_CHANGED", false);
        return super.closeMasarHome(...arguments);
    },
});

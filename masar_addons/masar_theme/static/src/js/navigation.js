/** @odoo-module **/

import {onMounted, useEffect, useExternalListener, useRef, useState} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {useBus, useService} from "@web/core/utils/hooks";
import {useHotkey} from "@web/core/hotkeys/hotkey_hook";
import {_t} from "@web/core/l10n/translation";
import {AppsMenu} from "@web_responsive/components/apps_menu/apps_menu.esm";
import {AppsMenuCanonicalSearchBar} from "@web_responsive/components/menu_canonical_searchbar/searchbar.esm";
import {NavBar} from "@web/webclient/navbar/navbar";
import {BurgerMenu} from "@web/webclient/burger_menu/burger_menu";

// Home is a workspace; a drawer is a separate, mutually exclusive surface.
const OVERLAY_CHANGED = "MASAR_NAVIGATION:OVERLAY_CHANGED";
const CLOSE_HOME = "MASAR_NAVIGATION:CLOSE_HOME";
const FOCUSABLE = 'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function focusable(root) {
    return root ? [...root.querySelectorAll(FOCUSABLE)].filter(el => el.getClientRects().length) : [];
}

function hasNestedOverlay(root) {
    return [...document.querySelectorAll(".o-overlay-container .o_popover, .o-overlay-container .o_dialog, .o-overlay-container .o-dropdown--menu")]
        .some(el => el.getClientRects().length && !root?.contains(el));
}

function setupDrawer(component, name, root, isOpen, close) {
    useEffect(() => {
        if (isOpen()) {
            focusable(root.el)[0]?.focus();
        }
    }, () => [isOpen()]);
    useHotkey("Escape", () => close(), {
        area: () => root.el,
        isAvailable: () => isOpen() && component.masarOverlay === name && !hasNestedOverlay(root.el),
        bypassEditableProtection: true,
    });
    useExternalListener(window, "keydown", ev => {
        if (ev.key !== "Tab" || !isOpen() || component.masarOverlay !== name || hasNestedOverlay(root.el)) {
            return;
        }
        const items = focusable(root.el);
        if (!items.length) {
            return;
        }
        const index = items.indexOf(document.activeElement);
        if (index === -1 || (ev.shiftKey && index === 0) || (!ev.shiftKey && index === items.length - 1)) {
            ev.preventDefault();
            (ev.shiftKey ? items[items.length - 1] : items[0]).focus();
        }
    });
}

patch(AppsMenu.prototype, {
    setup() {
        super.setup();
        this.ui = useState(useService("ui"));
        this.state.sectionsOpen = false;
        this.state.overlay = null;
        this.restoreLauncherFocus = false;
        useBus(this.env.bus, "APP_MENU:OPEN_APP_MENU", () => this.setOpenState(true));
        useBus(this.env.bus, CLOSE_HOME, () => this._closeLauncher());
        useBus(this.env.bus, OVERLAY_CHANGED, ({detail}) => {
            this.state.overlay = detail;
            this.state.sectionsOpen = detail === "sections";
        });
        // Synchronize the navbar even when home was selected before it mounted.
        onMounted(() => this.env.bus.trigger("APPS_MENU:STATE_CHANGED", this.state.open));
        useEffect(() => {
            if (this.state.open) {
                this.restoreLauncherFocus = false;
                this.launcher.el?.querySelector("input")?.focus();
            } else if (this.restoreLauncherFocus) {
                this.restoreLauncherFocus = false;
                this.navigationButton.el?.focus();
            }
        }, () => [this.state.open]);
    },

    setOpenState(open) {
        if (open) {
            this.env.bus.trigger(OVERLAY_CHANGED, null);
        }
        super.setOpenState(open);
    },

    get navigationLabel() {
        if (this.state.open) {
            return this.menuService.getCurrentApp() ? _t("Return to application") : _t("All applications");
        }
        return this.ui.isSmall ? _t("Application menu") : _t("All applications");
    },

    _closeLauncher() {
        if (this.state.open && !this.state.overlay && this.menuService.getCurrentApp()) {
            this.restoreLauncherFocus = true;
            this.setOpenState(false);
        }
    },

    onMenuClick() {
        if (this.state.open) {
            this._closeLauncher();
        } else if (this.ui.isSmall) {
            this.env.bus.trigger("APP_MENU:TOGGLE_SIDEBAR");
        } else {
            this.setOpenState(true);
        }
    },

    _setupKeyNavigation() {
        this.launcher = useRef("masarLauncher");
        this.navigationButton = useRef("masarNavigationButton");
        const options = {
            area: () => this.launcher.el,
            isAvailable: () => this.state.open && !this.state.overlay,
            allowRepeat: true,
        };
        for (const key of ["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp"]) {
            useHotkey(key, () => {
                const rtl = document.documentElement.dir === "rtl";
                const previous = key === "ArrowUp" || key === (rtl ? "ArrowRight" : "ArrowLeft");
                this._onWindowKeydown(previous ? "prev" : "next");
            }, options);
        }
        useHotkey("Escape", () => this._closeLauncher(), {
            area: () => this.launcher.el,
            isAvailable: () => this.state.open && !this.state.overlay && !!this.menuService.getCurrentApp(),
            bypassEditableProtection: true,
        });
    },

    _onWindowKeydown(direction) {
        if (!this.state.open || this.state.overlay) {
            return;
        }
        const items = [...(this.launcher.el?.querySelectorAll(".o-app-menu-item") || [])].filter(el => el.getClientRects().length);
        if (!items.length) {
            return;
        }
        const index = items.indexOf(document.activeElement);
        const next = index < 0 ? 0 : (index + (direction === "prev" ? -1 : 1) + items.length) % items.length;
        items[next].focus();
    },
});

// The canonical (and inherited Fuse) search input stops Escape propagation.
// Keep its clear-query behavior, but close only MASAR home for an empty query.
patch(AppsMenuCanonicalSearchBar.prototype, {
    _onKeyDown(ev) {
        if (ev.code === "Escape" && !this.inputValue && ev.target?.closest("#masar-apps-launcher")) {
            ev.stopPropagation();
            ev.preventDefault();
            this.env.bus.trigger(CLOSE_HOME);
            return;
        }
        return super._onKeyDown(ev);
    },
});

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.state.masarHomeOpen = false;
        this.masarOverlay = null;
        this.sectionsDrawer = useRef("masarSectionsDrawer");
        useBus(this.env.bus, "APPS_MENU:STATE_CHANGED", ({detail: open}) => {
            this.state.masarHomeOpen = open;
            if (open) {
                this._closeAppMenuSidebar(false);
            }
        });
        useBus(this.env.bus, OVERLAY_CHANGED, ({detail}) => {
            this.masarOverlay = detail;
            if (detail !== "sections") {
                this._closeAppMenuSidebar(false);
            }
        });
        setupDrawer(this, "sections", this.sectionsDrawer,
            () => this.state.isAppMenuSidebarOpened, () => this._closeAppMenuSidebar());
        // Home hides sections with display:none. Native adapt may have measured
        // zero widths on an app change; measure again after the launcher closes
        // and Owl has restored the visible navbar. Keep native More behavior.
        useEffect(() => {
            if (!this.state.masarHomeOpen && !this.ui.isSmall) {
                this.adapt();
            }
        }, () => [this.state.masarHomeOpen, this.ui.isSmall]);
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

    _closeAppMenuSidebar(restoreFocus = true) {
        const wasOpen = this.state.isAppMenuSidebarOpened;
        super._closeAppMenuSidebar();
        if (this.masarOverlay === "sections") {
            this.env.bus.trigger(OVERLAY_CHANGED, null);
        }
        if (wasOpen && restoreFocus) {
            this.root.el?.querySelector(".o_grid_apps_menu__button")?.focus();
        }
    },

    openAppMenu() {
        this._closeAppMenuSidebar(false);
        this.env.bus.trigger("APP_MENU:OPEN_APP_MENU");
    },

    onAllAppsBtnClick() {
        this.openAppMenu();
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
        this.accountDrawer = useRef("masarAccountDrawer");
        this.accountButton = useRef("masarAccountButton");
        useBus(this.env.bus, OVERLAY_CHANGED, ({detail}) => {
            this.masarOverlay = detail;
            if (detail !== "account") {
                this._closeBurger(false);
            }
        });
        useBus(this.env.bus, "APPS_MENU:STATE_CHANGED", ({detail: open}) => {
            if (open) {
                this._closeBurger(false);
            }
        });
        setupDrawer(this, "account", this.accountDrawer,
            () => this.state.isBurgerOpened, () => this._closeBurger());
    },

    _openBurger() {
        this.env.bus.trigger(OVERLAY_CHANGED, "account");
        super._openBurger();
    },

    _closeBurger(restoreFocus = true) {
        const wasOpen = this.state.isBurgerOpened;
        super._closeBurger();
        if (this.masarOverlay === "account") {
            this.env.bus.trigger(OVERLAY_CHANGED, null);
        }
        if (wasOpen && restoreFocus) {
            this.accountButton.el?.focus();
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

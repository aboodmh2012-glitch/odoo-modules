/* Behavior tests for MASAR navigation. Run with node; no Odoo database required.
 * Loads the actual native NavBar/BurgerMenu and restored OCA source, then the
 * MASAR patch. The hook/DOM mocks test state and event seams, not rendering or
 * browser layout. Browser and real-device verification remain separate.
 */
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '../../..');
const theme = path.resolve(__dirname, '..');
const nativeRoot = [process.env.MASAR_ODOO_WEB_SRC,
    '/usr/lib/python3/dist-packages/odoo/addons/web/static/src',
    path.join(root, 'addons/web/static/src')]
    .filter(Boolean).find(candidate => fs.existsSync(path.join(candidate, 'webclient/navbar/navbar.js')));
const nativeFixtures = path.join(__dirname, 'fixtures/odoo19');
const ocaPath = path.join(root, 'custom_addons/web_responsive/static/src/components/apps_menu/apps_menu.esm.js');
const patchPath = path.join(theme, 'static/src/js/navigation.js');
const canonicalCheckout = path.join(root, 'custom_addons/web_responsive/static/src/components/menu_canonical_searchbar/searchbar.esm.js');
const canonicalPath = fs.existsSync(canonicalCheckout) ? canonicalCheckout : path.join(__dirname, 'fixtures/web_responsive/menu_canonical_searchbar.esm.js');
const OVERLAY = 'MASAR_NAVIGATION:OVERLAY_CHANGED';

class Bus {
    constructor() { this.listeners = new Map(); this.events = []; }
    addEventListener(event, callback) {
        const callbacks = this.listeners.get(event) || [];
        callbacks.push(callback);
        this.listeners.set(event, callbacks);
    }
    removeEventListener(event, callback) {
        this.listeners.set(event, (this.listeners.get(event) || []).filter(cb => cb !== callback));
    }
    trigger(event, detail) {
        this.events.push({event, detail});
        for (const callback of [...(this.listeners.get(event) || [])]) { callback({detail}); }
    }
    count(event) { return (this.listeners.get(event) || []).length; }
}

function loadSource(context, text, filename, exported = []) {
    const source = text
        .replace(/^import\s+[\s\S]*?\s+from\s+["'][^"']+["'];\s*/gm, '')
        .replace(/^export\s+/gm, '');
    const result = vm.runInContext(`(() => { ${source}\nreturn {${exported.join(',')}}; })()`, context, {filename});
    Object.assign(context, result);
}

function load(context, filename, exported = []) {
    loadSource(context, fs.readFileSync(filename, 'utf8'), filename, exported);
}

function patch(target, extension) {
    // Match Odoo patch's super semantics: each extension sees the previous
    // descriptors and the prototype chain rather than itself after mutation.
    const previous = Object.create(Object.getPrototypeOf(target));
    Object.defineProperties(previous, Object.getOwnPropertyDescriptors(target));
    Object.setPrototypeOf(extension, previous);
    Object.defineProperties(target, Object.getOwnPropertyDescriptors(extension));
}

function createHarness({small = true, redirect = false, app = {id: 8, name: 'Appraisals'}, rtl = false} = {}) {
    const bus = new Bus();
    const overlayNodes = [];
    const doc = {documentElement: {dir: rtl ? 'rtl' : 'ltr'}, activeElement: null,
        querySelectorAll: selector => {
            const selectors = selector.split(',').map(part => part.trim());
            const valid = ['.o-overlay-container .o_popover', '.o-overlay-container .o_dialog', '.o-overlay-container .o-dropdown--menu'];
            // Model actual runtime classes. An underscore container typo must
            // return no matches, just as it does in a browser.
            return selectors.every(part => valid.includes(part))
                ? overlayNodes.filter(node => selectors.includes(`.o-overlay-container ${node.overlayClass || '.o_popover'}`)) : [];
        },
        body: {classList: {toggle() {}}}};
    const window = {history: {replaceState() {}}};
    const services = {menu: {getApps: () => [], getCurrentApp: () => app, getMenuAsTree: () => ({childrenTree: []}), selectMenu() {}},
        ui: {isSmall: small}, action: {}, pwa: {isScopedApp: false}, orm: {async searchRead() { return []; }}};
    let owner;
    const components = [];
    const registryBus = new Bus();
    const registry = {category: () => ({add() {}, getEntries: () => [],
        addEventListener: registryBus.addEventListener.bind(registryBus),
        removeEventListener: registryBus.removeEventListener.bind(registryBus)})};
    class Component { setup() {} render() {} }
    class WebClient extends Component { setup() { this.orm = services.orm; } _loadDefaultApp() {} }
    class Dummy {}
    const ctx = vm.createContext({Component, WebClient, Dropdown: Dummy, DropdownItem: Dummy,
        DropdownGroup: Dummy, Transition: Dummy, ErrorHandler: Dummy, BurgerUserMenu: Dummy,
        MobileSwitchCompanyMenu: Dummy, AppMenuItem: Dummy, AppsMenuSearchBar: Dummy,
        registry, patch, document: doc, window,
        Element: class {getBoundingClientRect() { return {width: 0}; }},
        location: {href: 'https://msarpay.com/odoo', hash: ''},
        user: {userId: 1, context: {is_redirect_to_home: redirect}, updateContext() {}},
        router: {current: {menu_id: redirect ? 0 : 8}}, session: {apps_menu: {theme: 'milk'}},
        browser: {localStorage: {getItem() { return ''; }, setItem() {}}}, _t: x => x,
        debounce: fn => Object.assign(fn, {cancel() {}}),
        collectRootMenuItems: items => items, collectSubMenuItems() {},
        fuzzyLookup: () => [], scrollTo() {}, escapeRegExp: value => value,
        useState: value => value,
        useService: name => services[name],
        useRef: name => (owner.refs[name] ||= {el: null}),
        useBus: (target, event, callback) => {
            target.addEventListener(event, callback);
            owner.cleanup.push(() => target.removeEventListener(event, callback));
        },
        useEffect: (callback, dependencies = () => []) => owner.effects.push({callback, dependencies, previous: undefined, cleanup: null}),
        useHotkey: (key, callback, options = {}) => owner.hotkeys.push({key, callback, options}),
        useExternalListener: (target, event, callback) => owner.external.push({target, event, callback}),
        onMounted: callback => owner.mounted.push(callback),
        onWillPatch: callback => owner.willPatch.push(callback),
        onPatched: callback => owner.patched.push(callback),
        useAutofocus: ({refName}) => (owner.refs[refName] ||= {el: null}),
        onWillStart: callback => owner.start.push(callback),
        onWillDestroy: callback => owner.cleanup.push(callback),
        onWillUnmount: callback => owner.cleanup.push(callback),
    });
    if (nativeRoot) {
        load(ctx, path.join(nativeRoot, 'webclient/navbar/navbar.js'), ['NavBar']);
        load(ctx, path.join(nativeRoot, 'webclient/burger_menu/burger_menu.js'), ['BurgerMenu']);
    } else {
        load(ctx, path.join(nativeFixtures, 'navbar.js'), ['NavBar']);
        load(ctx, path.join(nativeFixtures, 'burger_menu.js'), ['BurgerMenu']);
    }
    load(ctx, canonicalPath, ['AppsMenuCanonicalSearchBar']);
    load(ctx, ocaPath, ['AppsMenu']);
    load(ctx, patchPath);

    function element(label, editable = false, visible = true) {
        return {label, editable, getClientRects: () => visible ? [{}] : [],
            focus() { doc.activeElement = this; }};
    }
    function domRoot(items, input = null) {
        return {querySelectorAll: selector => selector === '.o-app-menu-item' ? items : [input, ...items].filter(Boolean),
            querySelector: selector => selector === 'input' ? input : null,
            contains: item => items.includes(item) || item === input};
    }
    const navButton = element('navigation');
    const accountButton = element('account');
    const input = Object.assign(element('search', true), {value: '',
        closest: selector => selector === '#masar-apps-launcher' ? apps.launcher.el : null});
    const appItems = [element('Discuss'), element('Calendar'), element('Hidden', false, false), element('To-do')];
    const sectionItems = [element('All apps'), element('section'), element('sections close')];
    const accountItems = [element('account close'), element('Help'), element('My Preferences')];
    function instantiate(Cls, refs) {
        const instance = new Cls();
        instance.env = {bus};
        instance.refs = {};
        instance.effects = []; instance.hotkeys = []; instance.external = [];
        instance.mounted = []; instance.start = []; instance.cleanup = []; instance.willPatch = []; instance.patched = [];
        for (const [name, el] of Object.entries(refs)) { instance.refs[name] = {el}; }
        owner = instance;
        instance.setup();
        owner = null;
        components.push(instance);
        return instance;
    }
    // Parent setup precedes child setup; child onMounted publishes initial state.
    const nav = instantiate(ctx.NavBar, {root: {querySelector: () => navButton}, appSubMenus: null,
        masarSectionsDrawer: domRoot(sectionItems)});
    const burger = instantiate(ctx.BurgerMenu, {masarAccountDrawer: domRoot(accountItems), masarAccountButton: accountButton});
    const apps = instantiate(ctx.AppsMenu, {masarLauncher: domRoot(appItems, input), masarNavigationButton: navButton});
    const search = instantiate(ctx.AppsMenuCanonicalSearchBar, {SearchBarInput: input, searchItems: null});
    function flush() {
        for (const component of components) {
            for (const effect of component.effects) {
                const next = effect.dependencies();
                if (!effect.previous || next.some((value, i) => !Object.is(value, effect.previous[i]))) {
                    effect.cleanup?.();
                    effect.cleanup = effect.callback();
                    effect.previous = [...next];
                }
            }
        }
    }
    components.forEach(component => component.mounted.forEach(callback => callback()));
    flush();
    function key(keyName, target = doc.activeElement, {shift = false} = {}) {
        let handled = 0;
        if (target === input) {
            let stopped = false;
            let prevented = false;
            search._onKeyDown({key: keyName, code: keyName, shiftKey: shift, target,
                stopPropagation() { stopped = true; }, preventDefault() { prevented = true; }});
            if (prevented) { handled++; }
            if (stopped) { flush(); return handled; }
        }
        for (const component of components) {
            for (const hotkey of component.hotkeys) {
                if (hotkey.key !== keyName || (hotkey.options.isAvailable && !hotkey.options.isAvailable())) { continue; }
                if (target?.editable && !hotkey.options.bypassEditableProtection) { continue; }
                const area = hotkey.options.area?.();
                if (hotkey.options.area && (!area || !area.contains(target))) { continue; }
                hotkey.callback(); handled++;
            }
            for (const listener of component.external) {
                if (listener.event === 'keydown') {
                    listener.callback({key: keyName, shiftKey: shift, preventDefault() { handled++; }});
                }
            }
        }
        flush();
        return handled;
    }
    function destroy() { components.forEach(component => component.cleanup.forEach(callback => callback())); }
    return {apps, nav, burger, search, bus, doc, flush, key, destroy, services, navButton, accountButton, input, overlayNodes, element,
        appItems, sectionItems, accountItems, setApp(value) { app = value; }};
}

const tests = [];
function test(name, run) { tests.push({name, run}); }

test('mobile navigation button opens sections exactly once and toggles closed', () => {
    const h = createHarness();
    assert.equal(h.bus.count('APP_MENU:TOGGLE_SIDEBAR'), 1);
    h.apps.onMenuClick(); h.flush();
    assert.equal(h.nav.state.isAppMenuSidebarOpened, true);
    assert.equal(h.apps.state.open, false);
    assert.equal(h.apps.state.sectionsOpen, true);
    assert.equal(h.apps.state.overlay, 'sections');
    h.apps.onMenuClick(); h.flush();
    assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
    assert.equal(h.apps.state.overlay, null);
    assert.equal(h.doc.activeElement, h.navButton);
});

test('All applications leaves sections and opens home with no duplicate drawer', () => {
    const h = createHarness();
    h.nav._openAppMenuSidebar(); h.flush();
    h.nav.onAllAppsBtnClick(); h.flush();
    assert.equal(h.apps.state.open, true);
    assert.equal(h.nav.state.masarHomeOpen, true);
    assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
    assert.equal(h.apps.state.overlay, null);
    assert.equal(h.doc.activeElement, h.input);
    h.nav._openAppMenuSidebar();
    assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
});

test('initial redirect-to-home publishes the launcher state after mount', () => {
    const h = createHarness({redirect: true, app: null});
    assert.equal(h.apps.state.open, true);
    assert.equal(h.nav.state.masarHomeOpen, true);
    assert.equal(h.apps.navigationLabel, 'All applications');
    h.apps.onMenuClick();
    assert.equal(h.apps.state.open, true, 'without an application, do not reveal an empty workspace');
});

test('desktop navigation opens home and returns to the current application', () => {
    const h = createHarness({small: false});
    assert.equal(h.apps.navigationLabel, 'All applications');
    h.apps.onMenuClick(); h.flush();
    assert.equal(h.apps.state.open, true);
    assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
    assert.equal(h.apps.navigationLabel, 'Return to application');
    h.apps.onMenuClick(); h.flush();
    assert.equal(h.apps.state.open, false);
});

test('desktop sections reflow after home closes, once visible and once per transition', () => {
    const h = createHarness({small: false});
    let adapted = 0;
    h.nav.adapt = () => { adapted++; };
    h.apps.setOpenState(true); h.flush();
    assert.equal(adapted, 0, 'do not measure hidden sections');
    h.apps.setOpenState(false);
    assert.equal(adapted, 0, 'wait until Owl has restored the visible DOM');
    h.flush();
    assert.equal(adapted, 1);
    h.flush();
    assert.equal(adapted, 1, 'unrelated renders must not repeatedly adapt');
});

test('mobile home closure keeps the drawer flow, desktop transition restores native reflow', () => {
    const h = createHarness({small: true});
    let adapted = 0;
    h.nav.adapt = () => { adapted++; };
    h.apps.setOpenState(true); h.flush();
    h.apps.setOpenState(false); h.flush();
    assert.equal(adapted, 0);
    h.services.ui.isSmall = false; h.flush();
    assert.equal(adapted, 1);
});

test('account opens above home without closing it and suppresses launcher keys', () => {
    const h = createHarness();
    h.apps.setOpenState(true); h.flush();
    h.burger._openBurger(); h.flush();
    assert.equal(h.apps.state.open, true);
    assert.equal(h.burger.state.isBurgerOpened, true);
    assert.equal(h.apps.state.overlay, 'account');
    assert.equal(h.doc.activeElement, h.accountItems[0]);
    const arrows = h.apps.hotkeys.filter(hotkey => hotkey.key.startsWith('Arrow'));
    assert(arrows.every(hotkey => !hotkey.options.isAvailable()));
    assert.equal(h.key('Escape'), 1);
    assert.equal(h.burger.state.isBurgerOpened, false);
    assert.equal(h.apps.state.open, true);
    assert.equal(h.apps.state.overlay, null);
    assert.equal(h.doc.activeElement, h.accountButton);
});

test('opening either drawer replaces the other and maintains a single overlay', () => {
    const h = createHarness();
    h.nav._openAppMenuSidebar(); h.flush();
    h.burger._openBurger(); h.flush();
    assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
    assert.equal(h.burger.state.isBurgerOpened, true);
    assert.equal(h.apps.state.overlay, 'account');
    h.nav._openAppMenuSidebar(); h.flush();
    assert.equal(h.burger.state.isBurgerOpened, false);
    assert.equal(h.nav.state.isAppMenuSidebarOpened, true);
    assert.equal(h.apps.state.overlay, 'sections');
    h.apps.setOpenState(true); h.flush();
    assert.equal(h.burger.state.isBurgerOpened, false);
    assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
    assert.equal(h.apps.state.overlay, null);
});

test('Escape closes the focused surface locally and restores its trigger', () => {
    const h = createHarness();
    h.nav._openAppMenuSidebar(); h.flush();
    assert.equal(h.key('Escape'), 1);
    assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
    assert.equal(h.doc.activeElement, h.navButton);
    h.apps.setOpenState(true); h.flush();
    assert.equal(h.key('Escape'), 1, 'Escape can leave launcher even while search input has focus');
    assert.equal(h.apps.state.open, false);
    assert.equal(h.doc.activeElement, h.navButton);
    assert.equal(h.bus.events.filter(({event}) => event === 'ACTION_MANAGER:UI-UPDATED').length, 0);
    assert.equal(h.key('Escape'), 0, 'no launcher shortcut should run after it closes');
});

test('Escape cannot close initial home when no application is selected', () => {
    const h = createHarness({redirect: true, app: null});
    h.key('Escape');
    assert.equal(h.apps.state.open, true);
});

test('arrow keys are local, ignore editable search, visible-only, and mirror RTL', () => {
    const h = createHarness();
    h.apps.setOpenState(true); h.flush();
    assert.equal(h.key('ArrowRight'), 0);
    assert.equal(h.doc.activeElement, h.input);
    h.appItems[0].focus();
    assert.equal(h.key('ArrowRight'), 1);
    assert.equal(h.doc.activeElement, h.appItems[1]);
    h.key('ArrowDown');
    assert.equal(h.doc.activeElement, h.appItems[3], 'hidden menu must be skipped');
    h.key('ArrowRight');
    assert.equal(h.doc.activeElement, h.appItems[0], 'visible menus wrap');
    h.doc.documentElement.dir = 'rtl';
    h.key('ArrowLeft');
    assert.equal(h.doc.activeElement, h.appItems[1]);
    h.key('ArrowRight');
    assert.equal(h.doc.activeElement, h.appItems[0]);
    h.apps.setOpenState(false); h.flush();
    assert.equal(h.key('ArrowDown'), 0);
});

test('native action events still close home and account without stale overlay', () => {
    const h = createHarness();
    h.apps.setOpenState(true); h.flush();
    h.burger._openBurger(); h.flush();
    h.bus.trigger('ACTION_MANAGER:UPDATE', {id: 42});
    h.bus.trigger('ACTION_MANAGER:UI-UPDATED'); h.flush();
    assert.equal(h.apps.state.open, false);
    assert.equal(h.nav.state.masarHomeOpen, false);
    assert.equal(h.burger.state.isBurgerOpened, false);
    assert.equal(h.apps.state.overlay, null);
});

test('launcher hotkeys neither capture unrelated navbar controls nor broadcast actions', () => {
    const h = createHarness();
    h.apps.setOpenState(true); h.flush();
    h.accountButton.focus();
    assert.equal(h.key('ArrowDown'), 0);
    assert.equal(h.key('Escape'), 0);
    assert.equal(h.apps.state.open, true);
    h.burger._openBurger(); h.flush();
    h.apps._onWindowKeydown('next');
    assert.equal(h.doc.activeElement, h.accountItems[0], 'direct callback also checks active overlay');
});

test('visible native popovers, dialogs, and dropdowns keep drawer Escape and Tab inactive', () => {
    const h = createHarness();
    h.burger._openBurger(); h.flush();
    for (const overlayClass of ['.o_popover', '.o_dialog', '.o-dropdown--menu']) {
        h.overlayNodes.push(Object.assign(h.element('native status overlay'), {overlayClass}));
        h.accountItems.at(-1).focus();
        assert.equal(h.key('Tab'), 0);
        assert.equal(h.doc.activeElement, h.accountItems.at(-1));
        assert.equal(h.key('Escape'), 0);
        assert.equal(h.burger.state.isBurgerOpened, true, 'native overlay must close first');
        h.overlayNodes.length = 0;
    }
    assert.equal(h.key('Escape'), 1);
    assert.equal(h.burger.state.isBurgerOpened, false);
});

test('empty canonical search Escape closes home locally and restores focus after DOM replacement', () => {
    const h = createHarness();
    h.apps.setOpenState(true); h.flush();
    let stopped = 0;
    let prevented = 0;
    h.search._onKeyDown({code: 'Escape', target: h.input, stopPropagation() { stopped++; }, preventDefault() { prevented++; }});
    assert.equal(stopped, 1);
    assert.equal(prevented, 1);
    assert.equal(h.apps.state.open, false);
    assert.equal(h.doc.activeElement, h.input, 'focus return must wait for the DOM update');
    assert.equal(h.bus.events.filter(({event}) => event === 'ACTION_MANAGER:UI-UPDATED').length, 0);
    const patchedNavigationButton = h.element('navigation after launcher DOM removed');
    h.apps.navigationButton.el = patchedNavigationButton;
    h.flush();
    assert.equal(h.doc.activeElement, patchedNavigationButton);
});

test('launcher grid Escape uses its scoped hotkey and returns focus', () => {
    const h = createHarness();
    h.apps.setOpenState(true); h.flush();
    h.appItems[0].focus();
    assert.equal(h.key('Escape'), 1);
    assert.equal(h.apps.state.open, false);
    assert.equal(h.doc.activeElement, h.navButton);
    assert.equal(h.bus.events.filter(({event}) => event === 'ACTION_MANAGER:UI-UPDATED').length, 0);
});

test('canonical Escape first clears search results and the second Escape closes home', () => {
    const h = createHarness();
    h.apps.setOpenState(true); h.flush();
    h.input.value = 'Calendar';
    h.search.state.hasResults = true;
    h.search.state.rootItems = [{name: 'Calendar'}];
    assert.equal(h.key('Escape'), 1);
    assert.equal(h.input.value, '');
    assert.equal(h.search.state.hasResults, false);
    assert.equal(h.search.state.rootItems.length, 0);
    assert.equal(h.apps.state.open, true);
    assert.equal(h.doc.activeElement, h.input);
    assert.equal(h.key('Escape'), 1);
    assert.equal(h.apps.state.open, false);
    assert.equal(h.doc.activeElement, h.navButton);
    assert.equal(h.bus.events.filter(({event}) => event === 'ACTION_MANAGER:UI-UPDATED').length, 0);
});

test('canonical empty Escape preserves initial home without an application', () => {
    const h = createHarness({redirect: true, app: null});
    h.key('Escape');
    assert.equal(h.apps.state.open, true);
    assert.equal(h.bus.events.filter(({event}) => event === 'ACTION_MANAGER:UI-UPDATED').length, 0);
});

test('close-home requests cannot dismiss home behind an active account drawer', () => {
    const h = createHarness();
    h.apps.setOpenState(true); h.flush();
    h.burger._openBurger(); h.flush();
    h.bus.trigger('MASAR_NAVIGATION:CLOSE_HOME'); h.flush();
    assert.equal(h.apps.state.open, true);
    assert.equal(h.burger.state.isBurgerOpened, true);
    assert.equal(h.doc.activeElement, h.accountItems[0]);
});

test('canonical search outside MASAR launcher keeps upstream Escape behavior', () => {
    const h = createHarness();
    const outside = Object.assign(h.element('external search', true), {closest: () => null});
    h.search._onKeyDown({code: 'Escape', target: outside, stopPropagation() {}, preventDefault() {}});
    assert.equal(h.bus.events.filter(({event}) => event === 'MASAR_NAVIGATION:CLOSE_HOME').length, 0);
    assert.equal(h.bus.events.filter(({event}) => event === 'ACTION_MANAGER:UI-UPDATED').length, 1);
});

test('hidden native overlays do not block drawer keyboard actions', () => {
    const h = createHarness();
    h.nav._openAppMenuSidebar(); h.flush();
    h.overlayNodes.push(h.element('hidden dialog', false, false));
    assert.equal(h.key('Escape'), 1);
    assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
});

test('Enter and Space select a section once and close its drawer', async () => {
    for (const key of ['Enter', ' ']) {
        const h = createHarness();
        const section = {id: 71, name: 'Settings'};
        const selected = [];
        h.services.menu.selectMenu = async menu => { selected.push(menu); };
        h.nav._openAppMenuSidebar(); h.flush();
        let prevented = 0;
        await h.nav._onSectionKeydown({key, preventDefault() { prevented++; }}, section);
        assert.deepEqual(selected, [section]);
        assert.equal(prevented, 1);
        assert.equal(h.nav.state.isAppMenuSidebarOpened, false);
        assert.equal(h.apps.state.overlay, null);
        await h.nav._onSectionKeydown({key: 'ArrowDown', preventDefault() { prevented++; }}, section);
        assert.deepEqual(selected, [section], 'unrelated key must not activate a section');
        assert.equal(prevented, 1);
    }
});

test('drawer Tab and Shift-Tab stay within the active drawer', () => {
    const h = createHarness();
    h.nav._openAppMenuSidebar(); h.flush();
    h.sectionItems.at(-1).focus();
    assert.equal(h.key('Tab'), 1);
    assert.equal(h.doc.activeElement, h.sectionItems[0]);
    h.key('Tab', h.doc.activeElement, {shift: true});
    assert.equal(h.doc.activeElement, h.sectionItems.at(-1));
    h.burger._openBurger(); h.flush();
    h.accountItems.at(-1).focus();
    h.key('Tab');
    assert.equal(h.doc.activeElement, h.accountItems[0]);
});

for (const rtl of [false, true]) {
    for (const kind of ['sections', 'account']) {
        test(`${kind} swipe handles start coordinate 0 and direction in ${rtl ? 'RTL' : 'LTR'}`, () => {
            const h = createHarness({rtl});
            const drawer = kind === 'sections' ? h.nav : h.burger;
            const open = () => kind === 'sections' ? drawer._openAppMenuSidebar() : drawer._openBurger();
            const isOpen = () => kind === 'sections' ? drawer.state.isAppMenuSidebarOpened : drawer.state.isBurgerOpened;
            open(); h.flush();
            drawer._onSwipeStart({changedTouches: [{clientX: 0}]});
            drawer._onSwipeEnd({changedTouches: [{clientX: rtl ? -150 : 150}]});
            assert.equal(isOpen(), false);
            assert.equal(drawer.swipeStartX, null);
            assert.equal(h.doc.activeElement, kind === 'sections' ? h.navButton : h.accountButton);
            open(); h.flush();
            drawer._onSwipeStart({changedTouches: [{clientX: 0}]});
            drawer._onSwipeEnd({changedTouches: [{clientX: rtl ? 150 : -150}]});
            assert.equal(isOpen(), true, 'opposite gesture must not close drawer');
            assert.equal(drawer.swipeStartX, null);
        });
    }
}

test('unmount removes hook-managed bus subscriptions', () => {
    const h = createHarness();
    assert.equal(h.bus.count('APP_MENU:TOGGLE_SIDEBAR'), 1);
    h.destroy();
    assert.equal(h.bus.count('APP_MENU:TOGGLE_SIDEBAR'), 0);
    assert.equal(h.bus.count(OVERLAY), 0);
    assert.equal(h.bus.count('APP_MENU:OPEN_APP_MENU'), 0);
    assert.equal(h.bus.count('MASAR_NAVIGATION:CLOSE_HOME'), 0);
});

async function main() {
    let failed = 0;
    for (const {name, run} of tests) {
        try { await run(); process.stdout.write(`PASS ${name}\n`); }
        catch (error) { failed++; process.stderr.write(`FAIL ${name}\n${error.stack}\n`); }
    }
    process.stdout.write(`${tests.length - failed}/${tests.length} navigation behavior tests passed (${nativeRoot ? 'native framework source' : 'Odoo 19 source fixtures'})\n`);
    process.exitCode = failed ? 1 : 0;
}
main().catch(error => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; });

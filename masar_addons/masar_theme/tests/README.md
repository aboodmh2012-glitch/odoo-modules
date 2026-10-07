# MASAR navigation behavior tests

Run from the repository root:

```sh
node custom_addons/masar_theme/tests/navigation_state.test.cjs
```

The Node VM loads the restored `web_responsive` AppsMenu source, the actual
canonical-searchbar source, and the MASAR navigation patch. It uses native Odoo NavBar and BurgerMenu source from:

1. `MASAR_ODOO_WEB_SRC`, if set to the Odoo `addons/web/static/src` directory;
2. `/usr/lib/python3/dist-packages/odoo/addons/web/static/src`, if installed;
3. a framework checkout under the repository's `addons/web/static/src`;
4. the included Odoo 19 source fixtures.

For example:

```sh
MASAR_ODOO_WEB_SRC=/path/to/odoo/addons/web/static/src node custom_addons/masar_theme/tests/navigation_state.test.cjs
```

The harness mocks OWL lifecycle hooks, services, and DOM focus. It checks
navigation state transitions, bus subscription cleanup, initial home-state
publication, overlay exclusivity, account access from home, local Escape
handling, search-field protection, visible app navigation in both directions,
native nested-overlay priority using the actual hyphenated container class,
canonical empty-Escape routing and clear-query behavior, focus restoration after
navigation-button DOM replacement, Enter/Space section activation, and swipes beginning at coordinate zero in LTR and RTL.

This suite does not render templates or compile assets. CSS stacking, responsive
layout, native touch behavior, screen-reader output, and browser integration
require separate browser/device verification.

## Native fixture provenance

`fixtures/odoo19/navbar.js` and `fixtures/odoo19/burger_menu.js` are verbatim
copies of the native source reviewed for this change from the Odoo 19.0 branch:

- https://github.com/odoo/odoo/blob/19.0/addons/web/static/src/webclient/navbar/navbar.js
- https://github.com/odoo/odoo/blob/19.0/addons/web/static/src/webclient/burger_menu/burger_menu.js

These upstream Odoo files are copyright Odoo S.A. and licensed under LGPL-3.0.
The included LGPL and GPL license texts apply to these fixtures. The installed
framework source takes precedence so the suite can also exercise the runtime
version's actual classes.

## Canonical-searchbar fixture provenance

`fixtures/web_responsive/menu_canonical_searchbar.esm.js` is the verbatim
production source fetched from `smartexsoftorg/masar` main while reviewing
commit `7e0ed4f1d8a1ff251ef294059ebcb6da7437592c`. Its Git blob SHA is
`e1f373342a7e71ec0d6abba8f661e65ac11c5cb5`. The test prefers the repository's
actual `custom_addons/web_responsive/static/src/components/menu_canonical_searchbar/searchbar.esm.js`
when present.

Source: https://github.com/smartexsoftorg/masar/blob/7e0ed4f1d8a1ff251ef294059ebcb6da7437592c/custom_addons/web_responsive/static/src/components/menu_canonical_searchbar/searchbar.esm.js

Copyright notices for Tecnativa, ITerra, Onestein, and Taras Shabaranskyi remain
in the fixture. Its upstream license is LGPL-3.0-or-later; the LGPL and GPL
license texts under `fixtures/odoo19/` also accompany this fixture.

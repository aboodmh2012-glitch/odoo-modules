# MASAR Theme

The application palette is navy `#071F3D`, deep navy `#04162C`, orange `#FF6A00`, and white. Quiet, text-free artwork is reserved for authentication and the app launcher; operational views use light surfaces. Old blue/cyan variable names remain compatibility aliases to the approved palette. Semantic success, warning, danger, and information colors remain functional status colors.

## Maintenance

Primary Sass variables, runtime tokens, and Bootstrap mappings must stay aligned. Orange controls use navy text in normal, hover, active, and disabled states. Odoo owns required/invalid input variables and row decorations. Use logical properties for inline edges and preserve LTR isolation for the English wordmark.

The background files `masar-workspace-desktop.webp` and `masar-workspace-mobile.webp` are separate compositions, each approximately 28 KB. Their versioned filenames replace the previous promotional login/app artwork without altering public website content.

## Responsive verification

Open `/masar_theme/static/tests/theme_preview.html` for a same-origin authentication preview at phone, small phone, landscape, tablet, and desktop widths. The fixture has no credentials or persistence. Administration's normal frame restrictions remain in place; verify it in its own tab or on a mobile device.

Check login, reset, sign-up, and Arabic login. Confirm fields/buttons stay reachable, labels do not overflow, the password reveal control works, and there is no horizontal overflow. In Administration check app launcher search/navigation, close/open the mobile section sidebar, and verify section text remains white on navy. Check a list and a form without saving business records. Preserve functional alert/validation colors.

Deployment does not require a module upgrade: asset changes rebuild on restart. Avoid blanket `-u` runs that overwrite live-edited QWeb views. Validate the actual `/web/login` page and Odoo runtime, not only Railway's boot health check.

## Navigation ownership

MASAR navigation behavior lives in `static/src/js/navigation.js` and the template extensions in `static/src/xml/navigation.xml`. The OCA apps-menu JS/XML/SCSS remain upstream. Home is a non-modal workspace below native Odoo dropdowns, backdrops, and drawers. Account and sections drawers coordinate through `MASAR_NAVIGATION:OVERLAY_CHANGED`; opening account over home preserves home, while entering home explicitly closes drawers.

There is one app-navigation trigger. On small screens it opens sections inside an application; All Apps returns to home. Home does not open a second sections drawer. Keep Odoo's systray registry, company access, user-menu items, action service, and menu service intact.

Hotkeys are registered only for the active surface. Home does not broadcast synthetic action-manager updates on Escape. Drawer keyboard behavior yields to native nested popovers/dialogs. Section leaves support Tab, Enter, and Space. Closing drawers restores their trigger focus; swipe direction mirrors in Arabic.

Run `node custom_addons/masar_theme/tests/navigation_state.test.cjs` for state/event behavior tests. These tests do not claim browser rendering or real-device coverage. On the running app verify home → user menu → close, app → sections → All Apps, search and Escape, messages and activities over home, preferences and company controls, and LTR/RTL swipe dismissal. Confirm no lingering backdrop and that account remains reachable at narrow widths.

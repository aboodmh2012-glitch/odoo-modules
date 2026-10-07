# Copyright 2026 MASAR
# License LGPL-3.0 or later.
import base64

from odoo.tools.misc import file_open


def post_init_hook(env):
    """Keep the public site identity aligned with the copy catalog."""
    website = env.ref("base.default_website", raise_if_not_found=False) or env["website"].search(
        [], limit=1
    )
    if website:
        try:
            with file_open("masar_website/static/src/img/app_icon.png", "rb") as icon:
                website.write({"favicon": base64.b64encode(icon.read())})
        except Exception:
            # Favicon is non-critical; apple-touch / manifest cover PWA chrome.
            pass
    env["website"].masar_apply_public_identity()

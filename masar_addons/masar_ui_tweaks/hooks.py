# Copyright 2026 MASAR
# License LGPL-3.0 or later.

def post_init_hook(env):
    """Quiet Odoo first-run chrome that fights MASAR branding."""
    env["res.users"]._masar_quiet_first_run()

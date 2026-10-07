"""Odoo shell entry: apply the MASAR website visual pass to stored views."""
import importlib.util

spec = importlib.util.spec_from_file_location(
    "masar_visual_pass",
    "/mnt/extra-addons/masar_website/visual_pass.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.apply(env)

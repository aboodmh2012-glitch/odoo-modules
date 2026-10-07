"""Odoo shell entry: retint stored website overrides to the MASAR Pay palette."""
import importlib.util

spec = importlib.util.spec_from_file_location(
    "masar_visual_pass",
    "/mnt/extra-addons/masar_website/visual_pass.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.apply_brand(env)

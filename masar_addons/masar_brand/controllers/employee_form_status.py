# Read-only public status for PR #167 employee-form overlay deactivation.
import json
import re

from odoo import http
from odoo.http import request

TARGET_XMLIDS = (
    "masar_hr_yemen.view_employee_form_masar_lifecycle",
    "masar_hr_employee_documents.view_employee_form_documents",
    "masar_hr_disciplinary.view_employee_form_disciplinary",
    "hr_appraisal_oca.view_employee_form",
    "hr_personal_equipment_request.hr_employee_form_view",
    "masar_hr_contract_sign.employee_contract_autofill",
    "masar_hr_payroll_yemen.employee_salary",
)

# Hints that still look like the retired MASAR employee overlays.
OVERLAY_HINTS = (
    "lifecycle",
    "resignation",
    "transfer",
    "document checklist",
    "employee documents",
    "disciplinary",
    "appraisal",
    "personal equipment",
    "contract pack",
    "contract number",
    "salary agreement",
    "masar salary",
    "sync salary",
)


class MasarEmployeeFormStatus(http.Controller):
    @http.route(
        "/masar/employee_form_overlay_status",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def employee_form_overlay_status(self, **_kwargs):
        env = request.env
        Imd = env["ir.model.data"].sudo()
        View = env["ir.ui.view"].sudo().with_context(active_test=False)
        Module = env["ir.module.module"].sudo()
        views = []
        all_inactive = True
        for xmlid in TARGET_XMLIDS:
            module, name = xmlid.split(".", 1)
            mod = Module.search([("name", "=", module)], limit=1)
            mod_state = mod.state if mod else "missing"
            imd = Imd.search([("module", "=", module), ("name", "=", name)], limit=1)
            if not imd:
                views.append(
                    {
                        "xmlid": xmlid,
                        "exists": False,
                        "active": None,
                        "module_state": mod_state,
                    }
                )
                if mod_state == "installed":
                    all_inactive = False
                continue
            view = View.browse(imd.res_id)
            active = bool(view.active) if view.exists() else None
            if active is not False:
                all_inactive = False
            views.append(
                {
                    "xmlid": xmlid,
                    "exists": bool(view.exists()),
                    "view_id": view.id if view.exists() else imd.res_id,
                    "active": active,
                    "noupdate": bool(imd.noupdate),
                    "module_state": mod_state,
                }
            )

        remaining = []
        suspicious = []
        base = env.ref("hr.view_employee_form", raise_if_not_found=False)
        if base:
            inherits = View.search(
                [
                    ("inherit_id", "=", base.id),
                    ("active", "=", True),
                    ("model", "=", "hr.employee"),
                ]
            )
            for view in inherits:
                xmlid = view.xml_id or ""
                module = xmlid.split(".", 1)[0] if xmlid else "?"
                arch = view.arch_db or ""
                # Compact signal of what the inherit injects.
                buttons = re.findall(
                    r'name="([^"]+)"[^>]*type="action"|string="([^"]+)"',
                    arch,
                )
                labels = []
                for a, b in buttons[:12]:
                    labels.append(a or b)
                item = {
                    "xmlid": xmlid or f"db-id:{view.id}",
                    "view_id": view.id,
                    "name": view.name,
                    "module": module,
                    "priority": view.priority,
                    "arch_len": len(arch),
                    "signals": labels,
                }
                remaining.append(item)
                blob = f"{view.name} {xmlid} {arch}".lower()
                if any(h in blob for h in OVERLAY_HINTS):
                    suspicious.append(item)

        payload = {
            "ok": all_inactive,
            "all_target_views_inactive": all_inactive,
            "views": views,
            "remaining_active_inherits": remaining,
            "remaining_active_inherits_count": len(remaining),
            "suspicious_remaining": suspicious,
        }
        return request.make_response(
            json.dumps(payload, indent=2, sort_keys=True),
            headers=[("Content-Type", "application/json")],
        )

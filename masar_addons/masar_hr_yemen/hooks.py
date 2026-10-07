# Copyright 2026 MASAR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Link catalog records to existing Knowledge pages by Arabic title (live DB)."""


# offense code -> document.page name (as on production Knowledge tree)
OFFENSE_POLICY_MAP = {
    "YE_ATT_LATE": "01 — الحضور والانصراف",
    "YE_ATT_ABSENT": "03 — الغياب",
    "YE_COND_CONDUCT": "09 — الجزاءات والإجراءات التأديبية",
    "YE_COND_SECRET": "09 — الجزاءات والإجراءات التأديبية",
    "YE_SAFE_RULES": "09 — الجزاءات والإجراءات التأديبية",
    "YE_PERF_DUTY": "09 — الجزاءات والإجراءات التأديبية",
    "YE_FRAUD_ID": "09 — الجزاءات والإجراءات التأديبية",
    "YE_POLICY_OTHER": "09 — الجزاءات والإجراءات التأديبية",
}

def post_init_hook(env):
    Page = env["document.page"].sudo()
    Offense = env["hr.discipline.offense.type"].sudo()
    for code, page_name in OFFENSE_POLICY_MAP.items():
        offense = Offense.search([("code", "=", code)], limit=1)
        if not offense or offense.policy_page_id:
            continue
        page = Page.search([("name", "=", page_name), ("type", "=", "content")], limit=1)
        if page:
            offense.policy_page_id = page.id

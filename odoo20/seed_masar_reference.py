# MASAR -> SMART Odoo 20 reference-data seed.
# Source: approved MASAR Odoo 19 repository seed definitions.
# Idempotent: safe to run again in SMART only.
Company = env["res.company"].sudo().browse(1)
if Company.exists():
    vals = {
        "name": "شركة مسار العالمية للأنظمة والحلول المالية",
        "email": "info@msarpay.com",
        "website": "https://msarpay.com",
    }
    Company.write({k: v for k, v in vals.items() if k in Company._fields})

Department = env["hr.department"].sudo()
Job = env["hr.job"].sudo()
company = env.company

STRUCTURE = {
    "Internal Audit Management": [],
    "Risk and Compliance Management": [],
    "Growth Management": ["Sales Section", "Marketing Section"],
    "Finance and Treasury Management": [],
    "Product and Operations Management": [
        "Payments and Merchant Operations Section",
        "Customer and Merchant Service Section",
    ],
    "Information Technology Management": [],
    "Corporate Affairs Management": ["Human Resources and Administration Section", "Procurement, Inventory and Assets Section"],
}

deps = {}
for management, sections in STRUCTURE.items():
    rec = Department.with_context(active_test=False).search(
        [("name", "=", management), ("company_id", "=", company.id)], limit=1
    )
    if not rec:
        rec = Department.create({"name": management, "company_id": company.id})
    vals = {"parent_id": False}
    if "active" in Department._fields:
        vals["active"] = True
    rec.write(vals)
    deps[management] = rec
    for section in sections:
        child = Department.with_context(active_test=False).search(
            [("name", "=", section), ("company_id", "=", company.id)], limit=1
        )
        if not child:
            child = Department.create({"name": section, "company_id": company.id})
        vals = {"parent_id": rec.id}
        if "active" in Department._fields:
            vals["active"] = True
        child.write(vals)
        deps[section] = child

JOBS = [
    ("Chief Executive Officer", None),
    ("Internal Audit Manager", "Internal Audit Management"),
    ("Internal Auditor", "Internal Audit Management"),
    ("Risk and Compliance Manager", "Risk and Compliance Management"),
    ("Money Laundering Reporting Officer (MLRO)", "Risk and Compliance Management"),
    ("Risk and Compliance Officer", "Risk and Compliance Management"),
    ("Chief Financial Officer", "Finance and Treasury Management"),
    ("Accountant and Reconciliation Officer", "Finance and Treasury Management"),
    ("Treasury and Settlement Officer", "Finance and Treasury Management"),
    ("Growth Manager", "Growth Management"),
    ("Sales and Merchant Development Officer", "Sales Section"),
    ("Marketing and Communications Officer", "Marketing Section"),
    ("Product and Operations Manager", "Product and Operations Management"),
    ("Payments and Merchant Operations Officer", "Payments and Merchant Operations Section"),
    ("Customer and Merchant Service Officer", "Customer and Merchant Service Section"),
    ("Information Technology Manager", "Information Technology Management"),
    ("Corporate Affairs Manager", "Corporate Affairs Management"),
    ("Human Resources and Administration Officer", "Human Resources and Administration Section"),
    ("Procurement, Inventory and Assets Officer", "Procurement, Inventory and Assets Section"),
] MASAR -> SMART Odoo 20 reference-data seed.
# Source: approved MASAR Odoo 19 repository seed definitions.
# Idempotent: safe to run again in SMART only.
Company = env["res.company"].sudo().browse(1)
if Company.exists():
    vals = {
        "name": "شركة مسار العالمية للأنظمة والحلول المالية",
        "email": "info@msarpay.com",
        "website": "https://msarpay.com",
    }
    Company.write({k: v for k, v in vals.items() if k in Company._fields})

Department = env["hr.department"].sudo()
Job = env["hr.job"].sudo()
company = env.company

STRUCTURE = {
    "Internal Audit Management": [],
    "Risk and Compliance Management": [],
    "Growth Management": ["Sales Section", "Marketing Section"],
    "Finance and Treasury Management": [],
    "Product and Operations Management": [
        "Payments and Merchant Operations Section",
        "Customer and Merchant Service Section",
    ],
    "Information Technology Management": [],
    "Corporate Affairs Management": ["Human Resources and Administration Section", "Procurement, Inventory and Assets Section"],
}

deps = {}
for management, sections in STRUCTURE.items():
    rec = Department.with_context(active_test=False).search(
        [("name", "=", management), ("company_id", "=", company.id)], limit=1
    )
    if not rec:
        rec = Department.create({"name": management, "company_id": company.id})
    vals = {"parent_id": False}
    if "active" in Department._fields:
        vals["active"] = True
    rec.write(vals)
    deps[management] = rec
    for section in sections:
        child = Department.with_context(active_test=False).search(
            [("name", "=", section), ("company_id", "=", company.id)], limit=1
        )
        if not child:
            child = Department.create({"name": section, "company_id": company.id})
        vals = {"parent_id": rec.id}
        if "active" in Department._fields:
            vals["active"] = True
        child.write(vals)
        deps[section] = child

JOBS = [
    ("Chief Executive Officer", None),
    ("Internal Audit Manager", "Internal Audit Management"),
    ("Risk and Compliance Manager", "Risk and Compliance Management"),
    ("AML/CFT and KYC Officer", "Risk and Compliance Management"),
    ("Growth Manager", "Growth Management"),
    ("Head of Sales", "Sales Section"),
    ("Head of Marketing", "Marketing Section"),
    ("Chief Financial Officer", "Finance and Treasury Management"),
    ("Accountant and Reconciliation Officer", "Finance and Treasury Management"),
    ("Treasury and Settlement Officer", "Finance and Treasury Management"),
    ("Product and Operations Manager", "Product and Operations Management"),
    ("Head of Payments and Merchant Operations", "Payments and Merchant Operations Section"),
    ("Head of Customer and Merchant Service", "Customer and Merchant Service Section"),
    ("Information Technology Manager", "Information Technology Management"),
    ("Corporate Affairs Manager", "Corporate Affairs Management"),
    ("Human Resources and Administration Officer", "Corporate Affairs Management"),
    ("Procurement, Inventory and Assets Officer", "Corporate Affairs Management"),
]

for title, department_name in JOBS:
    job = Job.search(
        [("name", "=", title), ("company_id", "in", [False, company.id])], limit=1
    )
    vals = {"name": title, "company_id": company.id}
    if department_name and "department_id" in Job._fields:
        vals["department_id"] = deps[department_name].id
    if not job:
        Job.create(vals)
    else:
        job.write(vals)

env.cr.commit()
print("MASAR_SMART_REFERENCE_SEED_OK")

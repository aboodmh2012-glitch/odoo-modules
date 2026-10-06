#!/usr/bin/env python3
"""Idempotent seed for MASAR AoA share capital (English founders).

Usage against SMART:
  python3 masar_addons/equity/scripts/seed_masar_founders.py
"""
from __future__ import annotations

import json
import ssl
import http.client
import xmlrpc.client

URL = "https://odoo20-fixed-production.up.railway.app"
DB, USER, PWD = "odoo20", "admin", "admin"
PRICE = 10000.0
DATE = "2026-04-01"
TOTAL = 150000
SHAREHOLDERS = [
    ("Abdulrahman Mohammed Ahmed Al-Zubairi", 37500, 25.0, "masar_shareholder_zubairi", "masar_equity_issue_zubairi"),
    ("Adel Ahmed Ali Al-Murisi", 52500, 35.0, "masar_shareholder_murisi", "masar_equity_issue_murisi"),
    ("Qaid Ahmed Hamoud Al-Zahri", 37500, 25.0, "masar_shareholder_zahri", "masar_equity_issue_zahri"),
    ("Abdo Ali Ahmed Al-Maqaleh", 18000, 12.0, "masar_shareholder_maqaleh", "masar_equity_issue_maqaleh"),
    ("Jawhar Adel Amin Khashana", 4500, 3.0, "masar_shareholder_khashana", "masar_equity_issue_khashana"),
]


class SafeTransport(xmlrpc.client.SafeTransport):
    def __init__(self, timeout=120):
        super().__init__()
        self.timeout = timeout

    def make_connection(self, host):
        conn = http.client.HTTPSConnection(
            host, timeout=self.timeout, context=ssl.create_default_context()
        )
        self._connection = host, conn
        return conn


def main():
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", transport=SafeTransport())
    uid = common.authenticate(DB, USER, PWD, {})
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", transport=SafeTransport())

    def ex(model, method, *args, **kw):
        return models.execute_kw(DB, uid, PWD, model, method, list(args), kw)

    def xid(name, model, res_id):
        found = ex("ir.model.data", "search", [["module", "=", "equity"], ["name", "=", name]])
        vals = {"module": "equity", "name": name, "model": model, "res_id": int(res_id), "noupdate": True}
        if found:
            ex("ir.model.data", "write", found, vals)
            return found[0]
        return ex("ir.model.data", "create", vals)

    def get_or_create(model, domain, vals):
        ids = ex(model, "search", domain, limit=1, context={"active_test": False})
        if ids:
            ex(model, "write", ids, vals)
            return ids[0]
        return ex(model, "create", vals)

    yer_id = ex("res.currency", "search", [["name", "=", "YER"]], context={"active_test": False})[0]
    ex("res.currency", "write", [yer_id], {"active": True})
    company_partner_id = ex("res.company", "read", [1], ["partner_id"])[0]["partner_id"][0]
    yemen = ex("res.country", "search", [["code", "=", "YE"]])[0]
    ex(
        "res.partner",
        "write",
        [company_partner_id],
        {
            "name": "MASAR Global for Financial Systems and Solutions",
            "is_company": True,
            "equity_currency_id": yer_id,
            "equity_legal_form": "Closed Yemeni Joint Stock Company",
            "equity_formation_date": DATE,
            "country_id": yemen,
            "city": "Aden",
        },
    )
    ex("res.company", "write", [1], {"name": "MASAR Global for Financial Systems and Solutions"})

    class_id = get_or_create(
        "equity.security.class",
        [["name", "=", "Ordinary Shares"]],
        {"name": "Ordinary Shares", "sequence": 10, "class_type": "shares", "share_votes": 1, "dividend_payout": True},
    )
    xid("masar_equity_ordinary_shares", "equity.security.class", class_id)

    # Keep founders-only set: remove other company txs then recreate/update by xmlid
    for name, shares, pct, partner_xid, tx_xid in SHAREHOLDERS:
        partner_id = get_or_create(
            "res.partner",
            [["name", "=", name], ["is_company", "=", False]],
            {
                "name": name,
                "is_company": False,
                "country_id": yemen,
                "comment": f"Founding shareholder — {pct:g}% of share capital (AoA 1 Apr 2026).",
            },
        )
        xid(partner_xid, "res.partner", partner_id)
        existing = ex("ir.model.data", "search_read", [["module", "=", "equity"], ["name", "=", tx_xid]], fields=["res_id"])
        vals = {
            "partner_id": company_partner_id,
            "transaction_type": "issuance",
            "date": DATE,
            "security_class_id": class_id,
            "securities": float(shares),
            "security_price": PRICE,
            "subscriber_id": partner_id,
            "notes": f"Founding cash shares: {shares:,} × YER {PRICE:,.0f} = YER {shares * PRICE:,.0f} ({pct:g}%).",
        }
        if existing:
            ex("equity.transaction", "write", [existing[0]["res_id"]], vals)
            tx_id = existing[0]["res_id"]
        else:
            tx_id = ex("equity.transaction", "create", vals)
        xid(tx_xid, "equity.transaction", tx_id)
        print(name, shares, tx_id)

    val = get_or_create(
        "equity.valuation",
        [["partner_id", "=", company_partner_id], ["date", "=", DATE]],
        {"partner_id": company_partner_id, "date": DATE, "event": "transaction", "valuation": TOTAL * PRICE},
    )
    xid("masar_equity_valuation_formation", "equity.valuation", val)

    cap = ex("equity.cap.table", "search_read", [["partner_id", "=", company_partner_id]], fields=["holder_id", "securities"])
    total = sum(r["securities"] for r in cap)
    print(json.dumps(cap, indent=2, default=str))
    print("TOTAL", total)
    assert abs(total - TOTAL) < 0.01


if __name__ == "__main__":
    main()

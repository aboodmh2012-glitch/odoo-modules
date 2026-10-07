#!/usr/bin/env python3
"""Static scan for Odoo 19 -> 20 API breaks in an addons directory.

Every pattern below was verified against the Odoo 20.0 source or observed as
an install/test failure on Odoo 20.0 (see docs/migration/ODOO20_FUNCTIONAL_AUDIT.md);
severities: BREAK = removed/changed (runtime failure or silent misbehaviour),
WARN = deprecated in 20, CHECK = review manually.

    python3 tools/odoo20_api_scan.py masar_addons /tmp/scan.json
"""
import collections
import json
import pathlib
import re
import sys
root=pathlib.Path(sys.argv[1])
P={ # name: (regex, file-suffixes, severity)

 'ir.attachment datas (REMOVED 20: silently stores empty)':(r"""['"]datas['"]\s*:|\.datas\b""", ('.py',), 'BREAK'),
 '_track_subtype (20 -> _track_log_get_default_subtype)':(r'def _track_subtype\(|super\(\)\._track_subtype', ('.py',), 'BREAK'),
 'XML <function> set_param/get_param':(r'name="(set|get)_param"', ('.xml',), 'BREAK'),
 't-esc/t-raw in server QWeb (renders EMPTY in 20)':(r'\bt-(esc|raw)=', ('.xml',), 'BREAK'),
 'odoo.http removed facade attrs':(r'http\.(Dispatcher|Request|Stream|_dispatchers|root|JsonRPCDispatcher|HttpDispatcher|SessionExpiredException|serialize_exception|content_disposition)\b|from odoo\.http import[^\n]*(_request_stack|Stream|root|content_disposition)', ('.py',), 'BREAK'),
 'odoo.service.db (removed 20)':(r'from odoo\.service import[^\n]*\bdb\b|odoo\.service\.db|from odoo\.service import \($', ('.py',), 'CHECK'),
 'resource.calendar tz/two_weeks/week_type (removed 20)':(r'calendar(_id)?\.tz\b|two_weeks_calendar|week_type', ('.py','.xml'), 'BREAK'),
 'DISABLED_MAIL_CONTEXT/DummyRLock test imports':(r'DISABLED_MAIL_CONTEXT\b|registry import DummyRLock', ('.py',), 'BREAK'),

 '_table_query (20 -> _table_sql)':(r'def _table_query\b|_table_query\b', ('.py',), 'BREAK'),
 'toggle_active (removed 20)':(r'toggle_active', ('.py','.xml','.js'), 'BREAK'),
 '_check_recursion/_check_m2m_recursion (removed 20 -> _has_cycle)':(r'_check_(m2m_)?recursion\(', ('.py',), 'BREAK'),
 'ir.model.access / ir.rule model usage (removed 20 -> ir.access)':(r"""['"]ir\.model\.access['"]|['"]ir\.rule['"]|model="ir\.rule"|model="ir\.model\.access"|rule_groups|model_access\b""", ('.py','.xml'), 'BREAK'),
 'company_type (removed 20)':(r'\bcompany_type\b', ('.py','.xml','.js'), 'BREAK'),
 'copy_translations/check_field_access_rights/_filter_access_rules':(r'copy_translations|check_field_access_rights|_filter_access_rules', ('.py',), 'BREAK'),
 'PG_CONCURRENCY_ERRORS_TO_RETRY import':(r'from odoo\.service\.model import', ('.py',), 'BREAK'),
 'env.reset()/flush_query':(r'env\.reset\(\)|flush_query\(', ('.py',), 'BREAK'),
 'owl global (const {..} = owl)':(r'=\s*owl;|owl\.Component', ('.js',), 'BREAK'),
 'static props (owl3 -> useProps)':(r'static props\s*=', ('.js',), 'CHECK'),
 'get_param/set_param (REMOVED in 20)':(r'\.(get_param|set_param)\(', ('.py',), 'BREAK'),
 'tools.ormcache import (deprecated 20)':(r'from odoo\.tools import[^\n]*\bormcache\b|tools\.ormcache|from odoo\.tools\.cache import|from odoo\.tools import[^\n]*\bcache\b', ('.py',), 'WARN'),
 '_sql_constraints (IGNORED since 18.1)':(r'^\s*_sql_constraints\s*=', ('.py',), 'BREAK'),
 'name_get (removed 17)':(r'def name_get\(|\.name_get\(\)', ('.py',), 'BREAK'),
 '_name_search (removed 18)':(r'def _name_search\(', ('.py',), 'BREAK'),
 'fields_view_get':(r'fields_view_get', ('.py',), 'BREAK'),
 '@api.multi/one':(r'@api\.(multi|one)\b', ('.py',), 'BREAK'),
 '.flush()/invalidate_cache':(r'\.flush\(\)|invalidate_cache\(', ('.py',), 'BREAK'),
 'user_has_groups/check_access_rights/check_access_rule':(r'user_has_groups\(|check_access_rights\(|check_access_rule\(|_filter_access_rules', ('.py',), 'BREAK'),
 'self._cr/_uid/_context':(r'self\._(cr|uid|context)\b', ('.py',), 'CHECK'),
 'read_group( public)':(r'\.read_group\(', ('.py',), 'CHECK'),
 'registry.clear_cache (19.4->transaction)':(r'registry\.clear_cache|\.clear_caches\(\)', ('.py',), 'BREAK'),
 'odoo.osv / expression':(r'from odoo\.osv|odoo\.osv\.expression|expression\.(AND|OR)', ('.py',), 'CHECK'),
 'groups_id / users on res.groups (19 rename)':(r"\bgroups_id\b|'users'\s*:|\.users\b", ('.py','.xml','.csv'), 'CHECK'),
 'compute+related same field':(r'fields\.\w+\([^)]*related=[^)]*compute=|fields\.\w+\([^)]*compute=[^)]*related=', ('.py',), 'WARN'),
 'tracking=':(r'tracking=', ('.py',), 'CHECK'),
 'attrs=/states= in XML':(r'\sattrs=|\sstates="', ('.xml',), 'BREAK'),
 '<tree / view_mode tree':(r'<tree\b|view_mode["\']?>?[^<\n]*\btree\b|"tree"', ('.xml','.py'), 'CHECK'),
 'ir.model.access.csv (19.4 -> ir.access.csv)':(r'ir\.model\.access\.csv', ('.py',), 'CHECK'),
 'ir.rule records (19.4 ir.access)':(r'model="ir\.rule"', ('.xml',), 'CHECK'),
 'type="base64" in XML':(r'type="base64"', ('.xml',), 'WARN'),
 'search date filter start_month etc':(r'start_month=|end_month=|start_year=|end_year=', ('.xml',), 'BREAK'),
 'account.group (removed 19.3)':(r"account\.group\b|account_group", ('.py','.xml','.csv'), 'BREAK'),
 'owl import @odoo/owl (owl3 check)':(r'from "@odoo/owl"', ('.js',), 'CHECK'),
 'legacy JS odoo.define':(r'odoo\.define\(', ('.js',), 'BREAK'),
 'useState/onWillStart owl2 hooks':(r'\buseRef\b|\buseSubEnv\b|\buseChildSubEnv\b|\bonWillUpdateProps\b|\buseExternalListener\b|this\.props\.|static template', ('.js',), 'CHECK'),
 'jsonrpc route type json (18.1)':(r"type=['\"]json['\"]", ('.py',), 'WARN'),
 'Query.where_clause/add_where (20 deprecated)':(r'add_where\(|where_clause|\.add_join\(|\.join\(\s*self\._table', ('.py',), 'WARN'),
 'web_read/web_search_read override':(r'def web_(search_)?read\(', ('.py',), 'CHECK'),
}
res=collections.defaultdict(lambda: collections.defaultdict(list))
for f in root.rglob('*'):
    if not f.is_file() or f.suffix not in ('.py','.xml','.js','.csv') or 'i18n' in f.parts:
        continue
    try:
        t=f.read_text(errors='ignore')
    except OSError:
        continue
    rel=f.relative_to(root); mod=rel.parts[0]
    for name,(rx,suf,sev) in P.items():
        if f.suffix not in suf: continue
        for m in re.finditer(rx,t,re.M):
            ln=t.count('\n',0,m.start())+1
            res[name][mod].append(f"{rel}:{ln}")
out={k:{m:v for m,v in d.items()} for k,d in res.items()}
json.dump(out,open(sys.argv[2],'w'),indent=1)
for k,d in out.items():
    sev=P[k][2]; tot=sum(len(v) for v in d.values())
    print(f"[{sev}] {k}: {tot} hits in {len(d)} modules: {', '.join(sorted(d)[:25])}{' ...' if len(d)>25 else ''}")

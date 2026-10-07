{'application': False,
 'author': 'much. Consulting',
 'auto_install': False,
 'category': 'Productivity',
 'data': ['security/security.xml',
          'security/ir.access.csv',
          'wizard/mcp_model_selection_wizard_views.xml',
          'wizard/oauth_bulk_confirm_wizard_views.xml',
          'views/mcp_enabled_models_views.xml',
          'views/mcp_custom_tool_views.xml',
          'views/mcp_log_views.xml',
          'views/oauth_views.xml',
          'views/res_config_settings_views.xml',
          'views/res_users_apikeys_views.xml',
          'views/mcp_menu.xml',
          'views/oauth_consent_templates.xml',
          'data/oauth_cron.xml'],
 'demo': [],
 'depends': ['base', 'base_setup', 'mail', 'rpc', 'web'],
 'description': '\n'
                'MCP Server for Odoo\n'
                '===================\n'
                '\n'
                'Enable AI assistants like Claude to securely\n'
                'access your Odoo data through natural language queries.\n'
                '\n'
                'Key Features\n'
                '------------\n'
                '* Native MCP endpoint at POST /mcp (Streamable HTTP, JSON-RPC 2.0) -\n'
                '  connect MCP clients directly to Odoo, no separate process to install\n'
                '* Search, retrieve, create, update and delete Odoo records, run aggregations\n'
                '  and call business methods\n'
                "* User context on connect: the handshake advertises the caller's timezone,\n"
                '  active and allowed companies (plus a get_current_context tool) so the model\n'
                '  writes to the right company and stops guessing timezones\n'
                '* Dedicated "MCP only" API-key scope: mint a key from My Profile that\n'
                '  authenticates only on /mcp (a smaller blast radius when leaked)\n'
                '* OAuth read-only consent: at the login/consent screen a user can withhold the\n'
                '  "Allow creating and modifying data" checkbox to grant a read-only (mcp:read)\n'
                '  session that cannot call - or even see - write tools\n'
                '* Custom tools: admins expose curated verbs (e.g. confirm_sale_order) by\n'
                '  wrapping an Odoo server action, instead of enabling generic create/write\n'
                '* Per-user opt-in: only members of the "MCP User" security group can use MCP\n'
                '* Granular permissions control per model and operation\n'
                '* Secure API key authentication with rate limiting and audit logging\n'
                '* Built-in OAuth 2.1 Authorization Server: browser MCP clients (Claude.ai, '
                'Gemini)\n'
                '  can connect by logging into Odoo, in addition to API keys\n'
                '* Easy configuration through Odoo settings\n'
                '\n'
                'How It Works\n'
                '------------\n'
                '1. Install this module and configure model access\n'
                '2. Add each user to the "MCP User" security group\n'
                '3. Generate an API key for authentication\n'
                '4. Point any MCP client (Claude, Cursor, VS Code, MCP Inspector) at your\n'
                "   Odoo URL's /mcp endpoint\n"
                '5. Start querying your Odoo data naturally\n'
                '\n'
                'Requirements: Odoo 19.0. The native /mcp endpoint needs no extra software;\n'
                "the module's legacy XML-RPC endpoints remain available for programmatic/RPC "
                'access.\n'
                '    ',
 'external_dependencies': {'python': ['authlib>=1.6.12,<1.7.0', 'defusedxml', 'packaging']},
 'images': ['static/description/banner.gif', 'static/description/icon.png'],
 'installable': True,
 'license': 'OPL-1',
 'name': 'MCP Server',
 'summary': 'Connect AI assistants to your Odoo instance via Model Context Protocol',
 'support': 'product@erp.muchconsulting.de',
 'version': '20.0.2.1.1',
 'website': 'https://muchconsulting.com/'}

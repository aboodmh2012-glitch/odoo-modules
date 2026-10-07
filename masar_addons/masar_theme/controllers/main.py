# -*- coding: utf-8 -*-
# Copyright 2026 MASAR
# License LGPL-3.0 or later.
import json

from odoo import http
from odoo.http import request
from odoo.tools.misc import file_open


class MasarWebManifest(http.Controller):
    """Rebrand the backend PWA manifest (/web/manifest.webmanifest).

    iOS/Android "Add to Home Screen" with "Open as Web App" reads the Web App
    Manifest for the app name and icon — not the apple-touch-icon / meta tags.
    Odoo's default manifest is named "Odoo" with the purple icon, so override it
    with MASAR branding. masar_theme depends on web, so this route wins over the
    core one.
    """

    _APPLE_TOUCH_ROUTES = [
        "/apple-touch-icon.png",
        "/apple-touch-icon-precomposed.png",
        "/apple-touch-icon-120x120.png",
        "/apple-touch-icon-152x152.png",
        "/apple-touch-icon-167x167.png",
        "/apple-touch-icon-180x180.png",
        # Safari also probes under the active website language prefix (/en/, /ar/).
        "/<string:lang>/apple-touch-icon.png",
        "/<string:lang>/apple-touch-icon-precomposed.png",
    ]

    @http.route("/web/manifest.webmanifest", type="http", auth="public", methods=["GET"])
    def masar_web_app_manifest(self, **kwargs):
        manifest = {
            "name": "MASAR Pay",
            "short_name": "MASAR Pay",
            "scope": "/odoo",
            "start_url": "/odoo",
            "display": "standalone",
            "background_color": "#071F3D",
            "theme_color": "#071F3D",
            "prefer_related_applications": False,
            "icons": [
                {
                    "src": "/masar_theme/static/src/img/masar-icon-192.png?v=20261004",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": "/masar_theme/static/src/img/masar-icon-512.png?v=20261004",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any",
                },
            ],
        }
        body = json.dumps(manifest, ensure_ascii=False)
        return request.make_response(
            body,
            headers=[
                ("Content-Type", "application/manifest+json"),
                ("Cache-Control", "no-cache"),
            ],
        )

    @http.route(
        _APPLE_TOUCH_ROUTES,
        type="http",
        auth="public",
        methods=["GET"],
        sitemap=False,
        readonly=True,
    )
    def masar_apple_touch_icon(self, lang=None, **kwargs):
        """Serve MASAR icon for Safari's default apple-touch-icon probes.

        Even with correct <link rel="apple-touch-icon"> tags, iOS still requests
        /apple-touch-icon.png (and under /en/, /ar/). Without this route those
        probes 404 while the real MASAR static icons remain 200.
        """
        del lang, kwargs  # lang prefix is only for URL matching
        with file_open("masar_theme/static/src/img/masar-icon-180.png", "rb") as icon:
            data = icon.read()
        return request.make_response(
            data,
            headers=[
                ("Content-Type", "image/png"),
                ("Cache-Control", "public, max-age=86400"),
            ],
        )

# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSocialMetaSdk(TransactionCase):
    def test_graph_version_v26(self):
        from odoo.addons.social_meta.models.sdk import GRAPH_VERSION

        self.assertEqual(GRAPH_VERSION, "v26.0")

    def test_list_user_pages_maps_page_objects(self):
        from odoo.addons.social_meta.models import sdk as sdk_mod

        page = MagicMock()
        page.get.side_effect = lambda key, default=None: {
            "id": "page-1",
            "name": "MASAR",
            "access_token": "PAGE_TOKEN",
            "instagram_business_account": {"id": "ig-1", "username": "masar"},
        }.get(key, default)

        with patch("facebook_business.adobjects.user.User") as UserCls:
            UserCls.return_value.get_accounts.return_value = [page]
            rows = sdk_mod.list_user_pages(MagicMock())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "page-1")
        self.assertEqual(rows[0]["access_token"], "PAGE_TOKEN")
        self.assertEqual(rows[0]["instagram_business_account"]["id"], "ig-1")

    def test_page_create_feed_uses_page_node(self):
        from odoo.addons.social_meta.models import sdk as sdk_mod

        with patch("facebook_business.adobjects.page.Page") as PageCls:
            PageCls.return_value.create_feed.return_value = {"id": "1_2"}
            result = sdk_mod.page_create_feed(MagicMock(), "1", "Hello")
        self.assertEqual(result["id"], "1_2")
        PageCls.assert_called_once()
        PageCls.return_value.create_feed.assert_called_once_with(params={"message": "Hello"})

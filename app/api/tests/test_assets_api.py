from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from app.assets.models import Asset, Collection


class AssetAPITestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="apiuser", password="pass")
        self.user.is_superuser = True
        self.user.save()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.collection = Collection.objects.create(title="Docs", slug="docs")
        self.asset = Asset.objects.create(
            collection=self.collection,
            title="First asset",
            slug="first",
            visibility="internal",
            text_content="secret",
        )

    def test_list_assets(self):
        resp = self.client.get(reverse("api-assets-list"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "First asset")

    def test_toggle_visibility(self):
        url = reverse("api-assets-toggle-visibility", args=[self.asset.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.visibility, "public")

    def test_create_asset_with_text_content(self):
        payload = {
            "collection": self.collection.id,
            "title": "Note",
            "slug": "note",
            "visibility": "internal",
            "text_content": "hello world",
        }
        resp = self.client.post(reverse("api-assets-list"), payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Asset.objects.count(), 2)
        note = Asset.objects.get(slug="note")
        self.assertEqual(note.text_content, "hello world")

    def test_update_asset_switch_source(self):
        payload = {"url": "https://example.com/asset.pdf"}
        resp = self.client.patch(
            reverse("api-assets-detail", args=[self.asset.id]), payload, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.url, "https://example.com/asset.pdf")
        self.assertEqual(self.asset.text_content, "")

    def test_create_collection_via_api(self):
        payload = {"title": "New Collection", "slug": "new-collection", "visibility_mode": "public"}
        resp = self.client.post(reverse("api-collections-list"), payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Collection.objects.filter(slug="new-collection").exists())

    def test_collection_toggle_visibility(self):
        url = reverse("api-collections-toggle-visibility", args=[self.collection.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.collection.refresh_from_db()
        self.assertEqual(self.collection.visibility_mode, "internal")

    def test_collection_delete(self):
        col = Collection.objects.create(title="Temp", slug="temp")
        url = reverse("api-collections-detail", args=[col.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Collection.objects.filter(id=col.id).exists())

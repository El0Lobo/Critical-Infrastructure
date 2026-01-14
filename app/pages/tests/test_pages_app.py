import json
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from app.assets.models import Asset, Collection
from app.pages.models import Page
from app.setup.models import SiteSettings


class PageRenderContentTests(TestCase):
    def setUp(self):
        self.blocks = [
            {
                "id": "block-1",
                "type": "rich_text",
                "props": {"html": "<p>Builder content</p>"},
            }
        ]

    def test_render_content_prefers_blocks_when_enabled(self):
        page = Page.objects.create(
            title="Story",
            slug="story",
            body="<p>Raw body</p>",
            blocks=self.blocks,
            status=Page.Status.PUBLISHED,
            is_visible=True,
            render_body_only=False,
        )

        rendered = page.render_content()

        self.assertIn("Builder content", rendered)
        self.assertIn("page-block--richtext", rendered)
        self.assertNotIn("Raw body", rendered)

    def test_render_content_respects_render_body_only_toggle(self):
        page = Page.objects.create(
            title="Story",
            slug="story-raw",
            body="<p>Raw body</p>",
            blocks=self.blocks,
            status=Page.Status.PUBLISHED,
            is_visible=True,
            render_body_only=True,
        )

        rendered = page.render_content()

        self.assertIn("Raw body", rendered)
        self.assertNotIn("page-block--richtext", rendered)

    def test_block_styles_render_inline_overrides(self):
        page = Page.objects.create(
            title="Styled story",
            slug="styled-story",
            blocks=[
                {
                    "id": "block-1",
                    "type": "rich_text",
                    "props": {
                        "html": "<p>Content</p>",
                        "style": {
                            "text_color": "#FF0044",
                            "background_color": "#000",
                            "font_family": "display",
                            "font_size": "xxl",
                        },
                    },
                }
            ],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        rendered = page.render_content()

        self.assertIn('color:#ff0044', rendered)
        self.assertIn('background-color:#000000', rendered)
        self.assertIn('font-size:1.6rem', rendered)
        self.assertIn('font-family:&quot;Oswald&quot;', rendered)

    def test_invalid_block_styles_are_ignored(self):
        page = Page.objects.create(
            title="Styled story invalid",
            slug="styled-invalid",
            blocks=[
                {
                    "id": "block-1",
                    "type": "rich_text",
                    "props": {
                        "html": "<p>Content</p>",
                        "style": {
                            "text_color": "rgb(0,0,0)",
                            "background_color": "javascript:alert('x')",
                            "font_family": "unknown",
                            "font_size": "200px",
                        },
                    },
                }
            ],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        rendered = page.render_content()

        self.assertNotIn("rgb(0,0,0)", rendered)
        self.assertNotIn("javascript:alert", rendered)
        self.assertNotIn("200px", rendered)

    def test_style_targets_apply_to_titles(self):
        page = Page.objects.create(
            title="Events",
            slug="events-styled",
            blocks=[
                {
                    "id": "block-1",
                    "type": "events",
                    "props": {
                        "title": "Upcoming",
                        "style_targets": {"title": {"text_color": "#112233", "font_size": "lg"}},
                    },
                }
            ],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        rendered = page.render_content()

        self.assertIn("font-size:1.15rem", rendered)
        self.assertIn("color:#112233", rendered)

    def test_custom_font_assets_render_font_face(self):
        page = Page.objects.create(
            title="Hero fonts",
            slug="hero-fonts",
            blocks=[
                {
                    "id": "hero",
                    "type": "hero",
                    "props": {
                        "title": "Welcome",
                        "style_targets": {
                            "title": {
                                "font_asset": {
                                    "id": 999,
                                    "title": "My Font",
                                    "url": "https://cdn.example.com/fonts/myfont.woff2",
                                    "mime_type": "font/woff2",
                                }
                            }
                        },
                    },
                }
            ],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        rendered = page.render_content()

        self.assertIn("@font-face{font-family:'CMSFont-", rendered)
        self.assertIn("https://cdn.example.com/fonts/myfont.woff2", rendered)

    def test_inline_fonts_emit_font_face(self):
        page = Page.objects.create(
            title="Inline font hero",
            slug="hero-inline-font",
            blocks=[
                {
                    "id": "hero-inline",
                    "type": "hero",
                    "props": {
                        "title": "<span style=\"font-family: CMSInlineFont-demo\">Hey</span>",
                        "inline_fonts": [
                            {
                                "family": "CMSInlineFont-demo",
                                "url": "https://cdn.example.com/fonts/demo.woff2",
                                "format": "woff2",
                            }
                        ],
                    },
                }
            ],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        rendered = page.render_content()

        self.assertIn("@font-face{font-family:'CMSInlineFont-demo'", rendered)
        self.assertIn("https://cdn.example.com/fonts/demo.woff2", rendered)
        self.assertIn("font-family: CMSInlineFont-demo", rendered)


class PreviewHtmlApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("author", "author@example.com", "password123")
        self.client.force_login(self.user)

        # Navigation source so build_nav_payload can resolve the slug.
        self.nav_page = Page.objects.create(
            title="Home",
            slug="home",
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        self.url = reverse("pages_api_preview_html")
        self.blocks = [
            {
                "id": "block-1",
                "type": "rich_text",
                "props": {"html": "<p>Builder preview</p>"},
            }
        ]

    def post_preview(self, **overrides):
        payload = {
            "title": "Preview page",
            "slug": "preview-page",
            "blocks": self.blocks,
            "body": "<p>Raw preview</p>",
            "render_body_only": False,
            "show_navigation_bar": True,
            "custom_nav_items": ["home"],
        }
        payload.update(overrides)
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_preview_html_returns_block_markup_by_default(self):
        data = self.post_preview()

        self.assertIn("page-block--richtext", data["content_html"])
        self.assertIn("Builder preview", data["content_html"])
        # Navigation payload should render at least one link with a URL.
        self.assertIn('<nav class="page-nav__links">', data["html"])

    def test_preview_html_respects_render_body_only_flag(self):
        data = self.post_preview(render_body_only=True)

        self.assertIn("Raw preview", data["content_html"])
        self.assertNotIn("page-block--richtext", data["content_html"])

    def test_preview_html_applies_theme_styles(self):
        theme = {"body": {"background_color": "#112233", "text_color": "#ffffff"}}
        data = self.post_preview(theme=theme)

        self.assertIn("#112233", data["html"])
        self.assertIn("#ffffff", data["html"])


class FontUploadApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("uploader", "font@example.com", "pass12345")
        self.client.force_login(self.user)
        self.url = reverse("pages_api_font_upload")

    def test_requires_permission_to_upload_font(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_uploads_font_into_fonts_collection(self):
        permission = Permission.objects.get(codename="add_asset")
        self.user.user_permissions.add(permission)
        upload = SimpleUploadedFile("display.woff2", b"dummyfont", content_type="font/woff2")
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir):
                response = self.client.post(self.url, {"file": upload, "title": "Display Font"})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["asset"]["kind"], "font")
        self.assertTrue(Collection.objects.filter(slug="fonts").exists())
        self.assertEqual(Asset.objects.count(), 1)


class InlineAssetUploadApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user("builder", "builder@example.com", "pass12345")
        self.client.force_login(self.user)
        self.url = reverse("pages_api_asset_upload")

    def test_requires_permission(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_uploads_image_asset(self):
        permission = Permission.objects.get(codename="add_asset")
        self.user.user_permissions.add(permission)
        upload = SimpleUploadedFile("logo.png", b"fakeimg", content_type="image/png")
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir):
                response = self.client.post(self.url, {"file": upload, "title": "Logo"})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["asset"]["kind"], "image")
        self.assertTrue(Collection.objects.filter(slug="page-builder").exists())
        self.assertEqual(Asset.objects.count(), 1)


class FooterBlockDefaultsTests(TestCase):
    def setUp(self):
        self.settings = SiteSettings.get_solo()
        self.settings.org_name = "Contrast"
        self.settings.address_street = "Josef-Belli-Weg"
        self.settings.address_number = "4"
        self.settings.address_postal_code = "78467"
        self.settings.address_city = "Konstanz"
        self.settings.address_country = "Germany"
        self.settings.social_instagram = "https://instagram.com/contrast"
        self.settings.social_facebook = "https://facebook.com/contrast"
        self.settings.save()

    def test_footer_block_autopopulates_from_site_settings(self):
        page = Page.objects.create(
            title="Home",
            slug="home-footer",
            blocks=[
                {"id": "hero", "type": "rich_text", "props": {"html": "<p>Body</p>"}},
                {"id": "footer-1", "type": "footer", "props": {}},
            ],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        html = page.render_content()

        self.assertIn("Contrast", html)
        self.assertIn("Josef-Belli-Weg 4", html)
        self.assertIn("78467 Konstanz", html)
        self.assertIn('aria-label="Instagram"', html)

    def test_render_content_segments_places_footer_separately(self):
        page = Page.objects.create(
            title="Home",
            slug="home-footer-split",
            blocks=[
                {"id": "hero", "type": "rich_text", "props": {"html": "<p>Body</p>"}},
                {"id": "footer-1", "type": "footer", "props": {}},
            ],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        main_html, footer_html, nav_html, structured_data = page.render_content_segments()

        self.assertIn("Body", main_html)
        self.assertNotIn("page-block--footer", main_html)
        self.assertIn("page-block--footer", footer_html)
        self.assertIn("page-block--navigation", nav_html)
        self.assertIsInstance(structured_data, list)

    def test_set_blocks_for_language_override(self):
        page = Page.objects.create(
            title="Home",
            slug="home",
            blocks=[{"id": "hero", "type": "rich_text", "props": {"html": "<p>Base</p>"}}],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        page.set_blocks_for_language("de", [{"id": "hero", "type": "rich_text", "props": {"html": "<p>DE</p>"}}], override=True)
        self.assertIn("de", page.layout_overrides)
        self.assertEqual(page.get_blocks_for_language("de")[0]["props"]["html"], "<p>DE</p>")

        page.set_blocks_for_language("de", [{"id": "hero", "type": "rich_text", "props": {"html": "<p>Shared</p>"}}], override=False)
        self.assertNotIn("de", page.layout_overrides)
        self.assertEqual(page.get_blocks_for_language("de")[0]["props"]["html"], "<p>Shared</p>")

    def test_shared_layout_updates_from_non_default_language(self):
        page = Page.objects.create(
            title="Home",
            slug="home-shared",
            blocks=[],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )

        page.set_blocks_for_language(
            "de",
            [{"id": "hero", "type": "rich_text", "props": {"html": "<p>DE layout</p>"}}],
            override=False,
        )

        self.assertNotIn("de", page.layout_overrides)
        self.assertEqual(page.get_blocks_for_language("en")[0]["props"]["html"], "<p>DE layout</p>")
        self.assertEqual(page.get_blocks_for_language("fr")[0]["props"]["html"], "<p>DE layout</p>")

    def test_language_translation_used_even_without_override_flag(self):
        page = Page.objects.create(
            title="Home",
            slug="home-legacy",
            blocks=[],
            status=Page.Status.PUBLISHED,
            is_visible=True,
        )
        page.layout_overrides = []
        page.__dict__[page._meta.get_field("blocks").attname] = []
        setattr(
            page,
            "blocks_es",
            [{"id": "hero", "type": "rich_text", "props": {"html": "<p>Legacy ES</p>"}}],
        )

        self.assertEqual(page.get_blocks_for_language("es")[0]["props"]["html"], "<p>Legacy ES</p>")


class LoginDevButtonTests(TestCase):
    @override_settings(ENV="development", DEBUG=False)
    def test_login_page_shows_dev_button_when_dev_env(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.dev_login_enabled = True
        settings_obj.save()

        response = self.client.get(reverse("login"))

        self.assertContains(response, "Force Login (Dev)")

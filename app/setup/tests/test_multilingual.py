"""
Comprehensive tests for multilingual functionality.

Tests cover:
- Model field translations
- URL routing for different languages
- Language switcher behavior
- Template translations
- SiteSettings language enable/disable
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import translation

from app.pages.models import Page
from app.setup.models import SiteSettings

User = get_user_model()


class ModelTranslationTests(TestCase):
    """Test that model fields are properly translated."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_page_title_translation(self):
        """Test that Page title field is translated correctly."""
        page = Page.objects.create(
            title_en="Home",
            title_es="Inicio",
            title_de="Startseite",
            title_fr="Accueil",
            slug_en="home",
            status=Page.Status.PUBLISHED,
            created_by=self.user,
            updated_by=self.user,
        )

        # English
        with translation.override("en"):
            self.assertEqual(page.title, "Home")

        # Spanish
        with translation.override("es"):
            self.assertEqual(page.title, "Inicio")

        # German
        with translation.override("de"):
            self.assertEqual(page.title, "Startseite")

        # French
        with translation.override("fr"):
            self.assertEqual(page.title, "Accueil")

    def test_page_slug_translation(self):
        """Test that Page slug field is translated correctly."""
        page = Page.objects.create(
            title_en="About",
            slug_en="about",
            slug_es="acerca-de",
            slug_de="uber-uns",
            slug_fr="a-propos",
            status=Page.Status.PUBLISHED,
            created_by=self.user,
            updated_by=self.user,
        )

        # English
        with translation.override("en"):
            self.assertEqual(page.slug, "about")

        # Spanish
        with translation.override("es"):
            self.assertEqual(page.slug, "acerca-de")

        # German
        with translation.override("de"):
            self.assertEqual(page.slug, "uber-uns")

        # French
        with translation.override("fr"):
            self.assertEqual(page.slug, "a-propos")

    def test_page_blocks_translation(self):
        """Test that Page blocks field is translated correctly."""
        page = Page.objects.create(
            title_en="Test",
            slug_en="test",
            blocks_en=[{"type": "hero", "props": {"title": "Welcome"}}],
            blocks_es=[{"type": "hero", "props": {"title": "Bienvenido"}}],
            blocks_de=[{"type": "hero", "props": {"title": "Willkommen"}}],
            blocks_fr=[{"type": "hero", "props": {"title": "Bienvenue"}}],
            status=Page.Status.PUBLISHED,
            created_by=self.user,
            updated_by=self.user,
        )

        # English
        with translation.override("en"):
            self.assertEqual(page.blocks[0]["props"]["title"], "Welcome")

        # Spanish
        with translation.override("es"):
            self.assertEqual(page.blocks[0]["props"]["title"], "Bienvenido")

        # German
        with translation.override("de"):
            self.assertEqual(page.blocks[0]["props"]["title"], "Willkommen")

        # French
        with translation.override("fr"):
            self.assertEqual(page.blocks[0]["props"]["title"], "Bienvenue")

    def test_fallback_to_english(self):
        """Test that missing translations fall back to English."""
        page = Page.objects.create(
            title_en="Only English",
            slug_en="only-english",
            status=Page.Status.PUBLISHED,
            created_by=self.user,
            updated_by=self.user,
        )

        # All languages should fall back to English
        with translation.override("es"):
            self.assertEqual(page.title, "Only English")

        with translation.override("de"):
            self.assertEqual(page.title, "Only English")


class URLRoutingTests(TestCase):
    """Test URL routing for different languages."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        # Create test pages
        self.home_page = Page.objects.create(
            title_en="Home",
            title_es="Inicio",
            title_de="Startseite",
            slug_en="home",
            slug_es="inicio",
            slug_de="startseite",
            status=Page.Status.PUBLISHED,
            is_visible=True,
            navigation_order=0,
            created_by=self.user,
            updated_by=self.user,
        )

        self.about_page = Page.objects.create(
            title_en="About",
            title_es="Acerca de",
            title_de="Über uns",
            slug_en="about",
            slug_es="acerca-de",
            slug_de="uber-uns",
            status=Page.Status.PUBLISHED,
            is_visible=True,
            navigation_order=1,
            created_by=self.user,
            updated_by=self.user,
        )

    def test_home_page_routing_all_languages(self):
        """Test that home page is accessible in all languages."""
        # English
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 200)

        # Spanish
        response = self.client.get("/es/")
        self.assertEqual(response.status_code, 200)

        # German
        response = self.client.get("/de/")
        self.assertEqual(response.status_code, 200)

        # French
        response = self.client.get("/fr/")
        self.assertEqual(response.status_code, 200)

    def test_page_routing_with_translated_slugs(self):
        """Test that pages are accessible via their translated slugs."""
        # English - /en/about/
        response = self.client.get("/en/about/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About")

        # Spanish - /es/acerca-de/
        response = self.client.get("/es/acerca-de/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acerca de")

        # German - /de/uber-uns/
        response = self.client.get("/de/uber-uns/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Über uns")

    def test_login_page_same_slug_all_languages(self):
        """Test that login page uses /login slug in all languages."""
        # Create login page with same slug in all languages
        Page.objects.create(
            title_en="Login",
            title_de="Anmelden",
            slug_en="login",
            slug_es="login",
            slug_de="login",
            slug_fr="login",
            status=Page.Status.PUBLISHED,
            is_visible=True,
            navigation_order=99,
            created_by=self.user,
            updated_by=self.user,
        )

        # All languages should use /login
        response = self.client.get("/en/login/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/es/login/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/de/login/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/fr/login/")
        self.assertEqual(response.status_code, 200)


class LanguageSwitcherTests(TestCase):
    """Test language switcher functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_set_language_endpoint_exists(self):
        """Test that set_language endpoint is accessible."""
        response = self.client.post("/i18n/setlang/", {"language": "de"})
        # Should redirect
        self.assertEqual(response.status_code, 302)

    def test_set_language_changes_language(self):
        """Test that posting to set_language actually changes the language."""
        # Switch to German
        response = self.client.post("/i18n/setlang/", {"language": "de"}, follow=False)

        # Check language cookie is set
        self.assertIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "de")

    def test_set_language_redirects_to_home(self):
        """Test that set_language redirects to home for public pages."""
        # Create a home page
        Page.objects.create(
            title_en="Home",
            slug_en="home",
            status=Page.Status.PUBLISHED,
            navigation_order=0,
            created_by=self.user,
            updated_by=self.user,
        )

        # Switch language from an English page (simulate clicking on language switcher on /en/)
        response = self.client.post("/i18n/setlang/", {"language": "de"}, HTTP_REFERER="/en/")

        # Should redirect to German home page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/de/")

    def test_invalid_language_code_ignored(self):
        """Test that invalid language codes are ignored."""
        response = self.client.post("/i18n/setlang/", {"language": "invalid"})

        # Should still redirect but not set invalid language
        self.assertEqual(response.status_code, 302)


class TemplateTranslationTests(TestCase):
    """Test that templates use translation tags correctly."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@example.com"
        )
        # Force login to bypass Axes backend
        self.client.force_login(self.user)

    def test_cms_dashboard_translates(self):
        """Test that CMS dashboard shows translated text."""
        # English
        response = self.client.get("/cms/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

        # Switch to German
        self.client.post("/i18n/setlang/", {"language": "de"})

        response = self.client.get("/cms/dashboard/")
        self.assertEqual(response.status_code, 200)
        # Dashboard is "Dashboard" in German too, but nav items should change
        # Check for a German translation in the nav
        self.assertContains(response, "Hauptmenü")  # "Main" in German

    def test_cms_navigation_translates(self):
        """Test that CMS navigation items are translated."""
        # Switch to German
        self.client.post("/i18n/setlang/", {"language": "de"})

        response = self.client.get("/cms/dashboard/")
        self.assertEqual(response.status_code, 200)

        # Check for German translations
        self.assertContains(response, "Seiten")  # Pages
        self.assertContains(response, "Veranstaltungen")  # Events
        self.assertContains(response, "Einstellungen")  # Settings


class SiteSettingsLanguageTests(TestCase):
    """Test SiteSettings language enable/disable functionality."""

    def test_get_enabled_languages_empty_returns_all(self):
        """Test that empty enabled_languages returns all configured languages."""
        settings_obj = SiteSettings.get_solo()
        settings_obj.enabled_languages = []
        settings_obj.save()

        enabled = settings_obj.get_enabled_languages()

        # Should return all 4 languages
        self.assertEqual(len(enabled), 4)
        codes = [code for code, name in enabled]
        self.assertIn("en", codes)
        self.assertIn("es", codes)
        self.assertIn("de", codes)
        self.assertIn("fr", codes)

    def test_get_enabled_languages_filters_correctly(self):
        """Test that enabled_languages filters to selected languages only."""
        settings_obj = SiteSettings.get_solo()
        settings_obj.enabled_languages = ["en", "de"]
        settings_obj.save()

        enabled = settings_obj.get_enabled_languages()

        # Should return only 2 languages
        self.assertEqual(len(enabled), 2)
        codes = [code for code, name in enabled]
        self.assertIn("en", codes)
        self.assertIn("de", codes)
        self.assertNotIn("es", codes)
        self.assertNotIn("fr", codes)

    def test_get_enabled_languages_returns_tuples(self):
        """Test that get_enabled_languages returns correct format."""
        settings_obj = SiteSettings.get_solo()
        settings_obj.enabled_languages = ["en", "es"]
        settings_obj.save()

        enabled = settings_obj.get_enabled_languages()

        # Check format
        self.assertEqual(enabled[0], ("en", "English"))
        self.assertEqual(enabled[1], ("es", "Español"))

    def test_enabled_languages_in_template_context(self):
        """Test that enabled_languages is available in template context."""
        client = Client()

        # Create a simple page
        user = User.objects.create_user(username="test", password="test123")
        Page.objects.create(
            title_en="Test",
            slug_en="test",
            status=Page.Status.PUBLISHED,
            navigation_order=0,
            created_by=user,
            updated_by=user,
        )

        # Get the page
        response = client.get("/en/")
        self.assertEqual(response.status_code, 200)

        # Check that enabled_languages is in context
        self.assertIn("enabled_languages", response.context)
        self.assertEqual(len(response.context["enabled_languages"]), 4)

    def test_language_switcher_hidden_with_one_language(self):
        """Test that language switcher is hidden when only one language is enabled."""
        settings_obj = SiteSettings.get_solo()
        settings_obj.enabled_languages = ["en"]
        settings_obj.save()

        client = Client()
        user = User.objects.create_user(username="test", password="test123")
        Page.objects.create(
            title_en="Test",
            slug_en="test",
            status=Page.Status.PUBLISHED,
            navigation_order=0,
            created_by=user,
            updated_by=user,
        )

        response = client.get("/en/")
        self.assertEqual(response.status_code, 200)

        # Language switcher should not be visible (checking for the select element)
        self.assertNotContains(response, 'name="language"')



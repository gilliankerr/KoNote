"""Tests for language switching — cookie persistence, login sync, and fallback."""
from cryptography.fernet import Fernet
from django.conf import settings
from django.test import TestCase, Client, override_settings

from apps.auth_app.models import User
import konote.encryption as enc_module


TEST_KEY = Fernet.generate_key().decode()


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY, AUTH_MODE="local")
class SwitchLanguageViewTest(TestCase):
    """Test the custom switch_language view."""

    databases = {"default", "audit"}

    def setUp(self):
        enc_module._fernet = None
        self.http = Client()
        self.user = User.objects.create_user(
            username="languser", password="testpass123", display_name="Lang User"
        )

    def tearDown(self):
        enc_module._fernet = None

    def test_switch_to_french_sets_cookie(self):
        resp = self.http.post("/i18n/switch/", {
            "language": "fr",
            "next": "/auth/login/",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.cookies[settings.LANGUAGE_COOKIE_NAME].value, "fr")

    def test_switch_to_english_sets_cookie(self):
        resp = self.http.post("/i18n/switch/", {
            "language": "en",
            "next": "/auth/login/",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")

    def test_invalid_language_falls_back_to_english(self):
        resp = self.http.post("/i18n/switch/", {
            "language": "xx",
            "next": "/",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")

    def test_get_request_not_allowed(self):
        resp = self.http.get("/i18n/switch/")
        self.assertEqual(resp.status_code, 405)

    def test_authenticated_user_preference_saved(self):
        self.http.login(username="languser", password="testpass123")
        self.http.post("/i18n/switch/", {
            "language": "fr",
            "next": "/",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.preferred_language, "fr")

    def test_anonymous_user_no_db_error(self):
        resp = self.http.post("/i18n/switch/", {
            "language": "fr",
            "next": "/auth/login/",
        })
        self.assertEqual(resp.status_code, 302)

    def test_unsafe_next_url_redirects_to_home(self):
        resp = self.http.post("/i18n/switch/", {
            "language": "en",
            "next": "https://evil.example.com/",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/")

    def test_cookie_max_age_set(self):
        resp = self.http.post("/i18n/switch/", {
            "language": "fr",
            "next": "/",
        })
        cookie = resp.cookies[settings.LANGUAGE_COOKIE_NAME]
        self.assertEqual(cookie["max-age"], settings.LANGUAGE_COOKIE_AGE)


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY, AUTH_MODE="local")
class SyncLanguageOnLoginTest(TestCase):
    """Test the sync_language_on_login utility."""

    databases = {"default", "audit"}

    def setUp(self):
        enc_module._fernet = None
        self.http = Client()

    def tearDown(self):
        enc_module._fernet = None

    def test_login_saves_language_to_new_user(self):
        """First login with no preferred_language saves current lang to profile."""
        user = User.objects.create_user(
            username="newuser", password="testpass123", display_name="New"
        )
        self.assertEqual(user.preferred_language, "")
        resp = self.http.post("/auth/login/", {
            "username": "newuser",
            "password": "testpass123",
        })
        self.assertEqual(resp.status_code, 302)
        user.refresh_from_db()
        # Should have saved the default language
        self.assertIn(user.preferred_language, ["en", "fr"])

    def test_login_restores_saved_preference(self):
        """Login with preferred_language='fr' keeps preference on user."""
        user = User.objects.create_user(
            username="fruser", password="testpass123", display_name="FR User"
        )
        user.preferred_language = "fr"
        user.save(update_fields=["preferred_language"])

        resp = self.http.post("/auth/login/", {
            "username": "fruser",
            "password": "testpass123",
        })
        self.assertEqual(resp.status_code, 302)
        user.refresh_from_db()
        # Preference should still be French (not overwritten)
        self.assertEqual(user.preferred_language, "fr")


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY, AUTH_MODE="local")
class BilingualLoginPageTest(TestCase):
    """Test the conditional bilingual hero on the login page."""

    databases = {"default", "audit"}

    def setUp(self):
        enc_module._fernet = None
        self.http = Client()

    def tearDown(self):
        enc_module._fernet = None

    def test_first_visit_shows_bilingual_hero(self):
        """No language cookie → bilingual hero with English/Fran\u00e7ais buttons."""
        resp = self.http.get("/auth/login/")
        self.assertContains(resp, "Participant Outcome Management")
        self.assertContains(resp, "Gestion des r\u00e9sultats des participants")
        self.assertContains(resp, "lang-chooser")

    def test_return_visit_shows_compact_toggle(self):
        """With language cookie → compact [EN | FR] toggle, no bilingual hero."""
        self.http.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        resp = self.http.get("/auth/login/")
        self.assertNotContains(resp, "lang-chooser")
        self.assertContains(resp, "lang-switcher")

    def test_french_cookie_shows_french_page(self):
        """French cookie → login page rendered in French."""
        self.http.cookies[settings.LANGUAGE_COOKIE_NAME] = "fr"
        resp = self.http.get("/auth/login/")
        # The compact toggle should show FR as bold (current)
        self.assertContains(resp, "<strong>FR</strong>", html=False)

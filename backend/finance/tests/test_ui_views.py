from django.contrib.auth.models import User
from django.test import Client, TestCase


class UIViewSmokeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "Silne!Haslo1"
        User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
            first_name="Jan",
        )

    def _assert_auth_shell(self, response):
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Podaj adres e-mail", content)
        self.assertNotIn('aria-label="Główne widoki"', content)
        self.assertNotIn("Wyloguj", content)

    def test_unauthenticated_routes_render_auth_shell(self):
        for path in ("/", "/categories/", "/stats/"):
            with self.subTest(path=path):
                self._assert_auth_shell(self.client.get(path))

    def test_authenticated_home_renders_placeholder_with_tabs(self):
        self.client.login(username="jan@example.com", password=self.password)
        response = self.client.get("/")
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Widok w budowie", content)
        self.assertIn('aria-label="Główne widoki"', content)
        self.assertIn("Wyloguj", content)
        self.assertNotIn("Zarządzanie", content)

    def test_authenticated_categories_renders_placeholder(self):
        self.client.login(username="jan@example.com", password=self.password)
        response = self.client.get("/categories/")
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Kategorie", content)
        self.assertIn('hx-get="/api/ui/categories"', content)
        self.assertNotIn("Zarządzanie", content)

    def test_authenticated_stats_renders_placeholder(self):
        self.client.login(username="jan@example.com", password=self.password)
        response = self.client.get("/stats/")
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Statystyki", content)
        self.assertIn("Widok w budowie", content)

    def test_auth_email_step_renders_in_shell(self):
        response = self.client.get("/api/auth")
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Podaj adres e-mail", content)

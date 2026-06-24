from django.contrib.auth.models import User
from django.test import Client, TestCase

from finance.models import Account


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

    def test_authenticated_home_renders_account_panel_with_navigation(self):
        self.client.login(username="jan@example.com", password=self.password)
        Account.objects.create(
            user=User.objects.get(username="jan@example.com"),
            name="Główne",
            balance="1000.00",
            currency="PLN",
        )
        response = self.client.get("/")
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="home-content"', content)
        self.assertIn("Główne", content)
        self.assertIn("Ostatnie 30 dni", content)
        self.assertIn("Wydatki", content)
        self.assertIn('aria-label="Poprzednie konto"', content)
        self.assertIn('aria-label="Następne konto"', content)
        self.assertIn('aria-label="Główne widoki"', content)
        self.assertIn("Wyloguj", content)
        self.assertNotIn("Widok w budowie", content)
        self.assertNotIn("Zarządzanie", content)
        self.assertNotIn("home-accounts-scroll", content)

    def test_empty_home_shows_create_slot_with_disabled_arrows(self):
        self.client.login(username="jan@example.com", password=self.password)
        response = self.client.get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Nowe konto", content)
        self.assertIn('aria-label="Dodaj nowe konto"', content)
        self.assertIn('aria-label="Poprzednie konto"', content)
        self.assertIn("disabled", content)

    def test_navigate_account_switches_displayed_account(self):
        user = User.objects.get(username="jan@example.com")
        first = Account.objects.create(user=user, name="Konto A", balance="100.00")
        second = Account.objects.create(user=user, name="Konto B", balance="200.00")
        self.client.login(username="jan@example.com", password=self.password)

        response = self.client.post(
            "/api/ui/home/navigate-account",
            {"direction": "next"},
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Konto B", content)
        self.assertIn("Ostatnie 30 dni", content)
        self.assertNotIn(f">{first.name}</h2>", content)

    def test_select_slot_switches_displayed_account(self):
        user = User.objects.get(username="jan@example.com")
        first = Account.objects.create(user=user, name="Konto A", balance="100.00")
        Account.objects.create(user=user, name="Konto B", balance="200.00")
        self.client.login(username="jan@example.com", password=self.password)

        response = self.client.post("/api/ui/home/select-slot", {"slot_index": 1})
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Konto B", content)
        self.assertNotIn(f">{first.name}</h2>", content)

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

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase

from finance.auth_service import (
    AuthServiceError,
    authenticate_by_email,
    normalize_email,
    register_user_by_email,
)
from finance.auth_utils import get_display_name


class NormalizeEmailTest(TestCase):
    def test_strips_and_lowercases(self):
        self.assertEqual(normalize_email("  Jan@Example.COM "), "jan@example.com")

    def test_rejects_empty_email(self):
        with self.assertRaises(AuthServiceError):
            normalize_email("   ")

    def test_rejects_invalid_email(self):
        with self.assertRaises(AuthServiceError):
            normalize_email("not-an-email")


class GetDisplayNameTest(TestCase):
    def test_uses_first_name(self):
        user = User(username="jan@example.com", first_name="Jan", email="jan@example.com")
        self.assertEqual(get_display_name(user), "Jan")

    def test_falls_back_to_email_local_part(self):
        user = User(username="jan@example.com", first_name="", email="jan@example.com")
        self.assertEqual(get_display_name(user), "jan")


class AuthAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "Silne!Haslo1"

    def test_auth_start_shows_email_step(self):
        response = self.client.get("/api/auth")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Podaj adres e-mail", response.content.decode())

    def test_check_email_existing_user_shows_login_step(self):
        User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
        )
        response = self.client.post("/api/auth/check-email", {"email": "jan@example.com"})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Witaj ponownie", content)
        self.assertIn("/api/auth/login", content)

    def test_check_email_new_user_shows_register_step(self):
        response = self.client.post("/api/auth/check-email", {"email": "nowy@example.com"})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Utwórz konto", content)
        self.assertIn("/api/auth/register", content)

    def test_check_email_invalid_returns_email_step_with_error(self):
        response = self.client.post("/api/auth/check-email", {"email": "zly-email"})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Podaj poprawny adres e-mail", content)

    def test_login_success(self):
        User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
            first_name="Jan",
        )
        response = self.client.post(
            "/api/auth/login",
            {"email": "jan@example.com", "password": self.password},
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="home-content"', content)
        self.assertIn('href="/profile/"', content)
        self.assertIn("Jan", content)

    def test_login_wrong_password(self):
        User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
        )
        response = self.client.post(
            "/api/auth/login",
            {"email": "jan@example.com", "password": "zle_haslo"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Błędny e-mail lub hasło", response.content.decode())

    def test_register_success(self):
        response = self.client.post(
            "/api/auth/register",
            {
                "email": "nowy@example.com",
                "first_name": "Anna",
                "password": self.password,
                "password_confirm": self.password,
            },
        )
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username="nowy@example.com")
        self.assertEqual(user.email, "nowy@example.com")
        self.assertEqual(user.first_name, "Anna")
        self.assertIn("Anna", response.content.decode())

    def test_register_password_mismatch(self):
        response = self.client.post(
            "/api/auth/register",
            {
                "email": "nowy@example.com",
                "first_name": "Anna",
                "password": self.password,
                "password_confirm": "Inne!Haslo2",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hasła nie są zgodne", response.content.decode())
        self.assertFalse(User.objects.filter(username="nowy@example.com").exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
        )
        response = self.client.post(
            "/api/auth/register",
            {
                "email": "jan@example.com",
                "first_name": "Jan",
                "password": self.password,
                "password_confirm": self.password,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("już istnieje", response.content.decode())

    def test_logout(self):
        User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
        )
        self.client.login(username="jan@example.com", password=self.password)
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Podaj adres e-mail", response.content.decode())


class AuthServiceTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.password = "Silne!Haslo1"

    def test_authenticate_by_email_legacy_username(self):
        request = self.factory.get("/")
        User.objects.create_user(
            username="stary_login",
            email="legacy@example.com",
            password=self.password,
        )
        user = authenticate_by_email(request, "legacy@example.com", self.password)
        self.assertEqual(user.username, "stary_login")

    def test_register_user_by_email_creates_user(self):
        user = register_user_by_email(
            "nowy@example.com",
            "Kamil",
            self.password,
            self.password,
        )
        self.assertEqual(user.username, "nowy@example.com")
        self.assertEqual(user.first_name, "Kamil")

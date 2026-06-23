import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from finance.models import Account, Category, Transaction


class AuthAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_creates_user(self):
        response = self.client.post("/api/auth/register", {"username": "nowyuser", "password": "Silne!Haslo1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="nowyuser").exists())

    def test_register_duplicate_username_returns_error(self):
        User.objects.create_user(username="duplikat", password="pass")
        response = self.client.post("/api/auth/register", {"username": "duplikat", "password": "Silne!Haslo1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("już istnieje", response.content.decode())

    def test_login_success(self):
        User.objects.create_user(username="user1", password="Haslo!123")
        response = self.client.post("/api/auth/login", {"username": "user1", "password": "Haslo!123"})
        self.assertEqual(response.status_code, 200)

    def test_login_wrong_password(self):
        User.objects.create_user(username="user2", password="Haslo!123")
        response = self.client.post("/api/auth/login", {"username": "user2", "password": "zle_haslo"})
        self.assertIn("Błędny login", response.content.decode())

    def test_logout(self):
        User.objects.create_user(username="user3", password="Haslo!123")
        self.client.login(username="user3", password="Haslo!123")
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)

    def test_protected_ping_unauthenticated(self):
        response = self.client.get("/api/auth/protected-ping")
        self.assertEqual(response.status_code, 401)

    def test_protected_ping_authenticated(self):
        User.objects.create_user(username="user4", password="Haslo!123")
        self.client.login(username="user4", password="Haslo!123")
        response = self.client.get("/api/auth/protected-ping")
        self.assertEqual(response.status_code, 200)


class AccountAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.client.login(username="testuser", password="pass")

    def test_list_accounts_empty(self):
        response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test_create_account(self):
        response = self.client.post(
            "/api/accounts",
            json.dumps({"name": "Konto główne", "balance": "1000.00", "currency": "PLN"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["name"], "Konto główne")
        self.assertEqual(data["currency"], "PLN")

    def test_cannot_access_other_users_account(self):
        other_account = Account.objects.create(user=self.other_user, name="Cudze konto")
        response = self.client.get(f"/api/accounts/{other_account.pk}")
        self.assertEqual(response.status_code, 404)

    def test_delete_account(self):
        account = Account.objects.create(user=self.user, name="Do usunięcia")
        response = self.client.delete(f"/api/accounts/{account.pk}")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Account.objects.filter(pk=account.pk).exists())

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.get("/api/accounts")
        self.assertEqual(response.status_code, 401)


class TransactionAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")
        self.account = Account.objects.create(user=self.user, name="Konto", balance=Decimal("1000.00"))
        self.category = Category.objects.create(user=self.user, name="Jedzenie")

    def test_create_transaction_updates_account_balance(self):
        response = self.client.post(
            "/api/transactions",
            json.dumps({
                "account_id": self.account.pk,
                "category_id": self.category.pk,
                "amount": "-200.00",
                "title": "Zakupy",
                "description": "",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("800.00"))

    def test_delete_transaction_reverses_balance(self):
        txn = Transaction.objects.create(
            account=self.account, category=None, amount=Decimal("-300.00"), title="Wydatek"
        )
        self.client.delete(f"/api/transactions/{txn.pk}")
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("1300.00"))

    def test_cannot_see_other_users_transactions(self):
        other_user = User.objects.create_user(username="other", password="pass")
        other_account = Account.objects.create(user=other_user, name="Cudze konto")
        other_txn = Transaction.objects.create(
            account=other_account, category=None, amount=Decimal("100.00"), title="Cudza"
        )
        response = self.client.get(f"/api/transactions/{other_txn.pk}")
        self.assertEqual(response.status_code, 404)

    def test_list_transactions_only_own(self):
        Transaction.objects.create(
            account=self.account, category=None, amount=Decimal("50.00"), title="Moja"
        )
        other_user = User.objects.create_user(username="other2", password="pass")
        other_account = Account.objects.create(user=other_user, name="Cudze")
        Transaction.objects.create(
            account=other_account, category=None, amount=Decimal("50.00"), title="Cudza"
        )
        response = self.client.get("/api/transactions")
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Moja")

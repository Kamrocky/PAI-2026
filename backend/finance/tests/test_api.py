import json
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from finance.constants import CATEGORY_COLOR_PALETTE, DEFAULT_CATEGORY_COLOR
from finance.models import Account, Category, Transaction


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

    def test_create_account_rejects_invalid_currency(self):
        response = self.client.post(
            "/api/accounts",
            json.dumps({"name": "Konto", "balance": "0.00", "currency": "XYZ"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)

    def test_put_does_not_change_currency(self):
        account = Account.objects.create(user=self.user, name="Konto", currency="EUR")
        response = self.client.put(
            f"/api/accounts/{account.pk}",
            json.dumps({"name": "Nowa nazwa", "balance": "999.00", "currency": "USD"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertEqual(account.name, "Nowa nazwa")
        self.assertEqual(account.currency, "EUR")

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


class CategoryAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")

    def test_create_category_with_palette_color(self):
        response = self.client.post(
            "/api/categories",
            json.dumps({
                "name": "Jedzenie",
                "color": CATEGORY_COLOR_PALETTE[1],
                "is_income": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["color"], CATEGORY_COLOR_PALETTE[1])
        self.assertNotIn("icon", data)

    def test_create_category_rejects_color_outside_palette(self):
        response = self.client.post(
            "/api/categories",
            json.dumps({"name": "Jedzenie", "color": "#FF0000", "is_income": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)

    def test_create_category_uses_default_color(self):
        response = self.client.post(
            "/api/categories",
            json.dumps({"name": "Domyślna", "is_income": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["color"], DEFAULT_CATEGORY_COLOR)


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

    def test_create_transaction_with_custom_date(self):
        custom_date = datetime(2024, 3, 10, 14, 30, tzinfo=dt_timezone.utc)
        response = self.client.post(
            "/api/transactions",
            json.dumps({
                "account_id": self.account.pk,
                "category_id": None,
                "amount": "50.00",
                "title": "Z datą",
                "description": "",
                "date": custom_date.isoformat(),
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["title"], "Z datą")
        txn = Transaction.objects.get(pk=data["id"])
        self.assertEqual(txn.date, custom_date)

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

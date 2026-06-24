import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from finance.constants import CATEGORY_COLOR_PALETTE
from finance.models import Account, Category, Transaction


class FullUserFlowTest(TestCase):
    """Rejestracja → login → konto → kategoria → transakcja → weryfikacja salda."""

    def setUp(self):
        self.client = Client()

    def test_complete_flow(self):
        self.client.post("/api/auth/register", {"username": "flowuser", "password": "Silne!Haslo1"})
        self.client.post("/api/auth/login", {"username": "flowuser", "password": "Silne!Haslo1"})

        account_resp = self.client.post(
            "/api/accounts",
            json.dumps({"name": "Konto osobiste", "balance": "2000.00", "currency": "PLN"}),
            content_type="application/json",
        )
        self.assertEqual(account_resp.status_code, 201)
        account_id = json.loads(account_resp.content)["id"]

        category_resp = self.client.post(
            "/api/categories",
            json.dumps({"name": "Jedzenie", "color": CATEGORY_COLOR_PALETTE[0], "is_income": False}),
            content_type="application/json",
        )
        self.assertEqual(category_resp.status_code, 201)
        category_id = json.loads(category_resp.content)["id"]

        txn_resp = self.client.post(
            "/api/transactions",
            json.dumps({
                "account_id": account_id,
                "category_id": category_id,
                "amount": "-350.00",
                "title": "Zakupy w Biedronce",
                "description": "",
            }),
            content_type="application/json",
        )
        self.assertEqual(txn_resp.status_code, 201)

        account_resp = self.client.get(f"/api/accounts/{account_id}")
        self.assertEqual(json.loads(account_resp.content)["balance"], "1650.00")

        txns_resp = self.client.get("/api/transactions")
        txns = json.loads(txns_resp.content)
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]["title"], "Zakupy w Biedronce")


class BalanceIntegrityTest(TestCase):
    """Wiele transakcji — saldo końcowe musi się zgadzać z sumą."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client = Client()
        self.client.login(username="testuser", password="pass")
        self.account = Account.objects.create(user=self.user, name="Konto", balance=Decimal("1000.00"))

    def test_multiple_transactions_balance(self):
        amounts = ["500.00", "-200.00", "-150.00", "300.00", "-80.00"]
        for amount in amounts:
            self.client.post(
                "/api/transactions",
                json.dumps({"account_id": self.account.pk, "category_id": None, "amount": amount, "title": "T", "description": ""}),
                content_type="application/json",
            )

        self.account.refresh_from_db()
        expected = Decimal("1000.00") + sum(Decimal(a) for a in amounts)
        self.assertEqual(self.account.balance, expected)

    def test_balance_after_create_update_delete(self):
        resp = self.client.post(
            "/api/transactions",
            json.dumps({"account_id": self.account.pk, "category_id": None, "amount": "-400.00", "title": "Pierwotna", "description": ""}),
            content_type="application/json",
        )
        txn_id = json.loads(resp.content)["id"]

        self.client.put(
            f"/api/transactions/{txn_id}",
            json.dumps({"account_id": self.account.pk, "category_id": None, "amount": "-100.00", "title": "Poprawiona", "description": ""}),
            content_type="application/json",
        )

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("900.00"))

        self.client.delete(f"/api/transactions/{txn_id}")

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("1000.00"))


class TransactionTransferBetweenAccountsTest(TestCase):
    """Przeniesienie transakcji między kontami przez API — oba salda muszą być poprawne."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client = Client()
        self.client.login(username="testuser", password="pass")
        self.account_a = Account.objects.create(user=self.user, name="Konto A", balance=Decimal("1000.00"))
        self.account_b = Account.objects.create(user=self.user, name="Konto B", balance=Decimal("500.00"))

    def test_transfer_adjusts_both_accounts(self):
        resp = self.client.post(
            "/api/transactions",
            json.dumps({"account_id": self.account_a.pk, "category_id": None, "amount": "-200.00", "title": "Zakup", "description": ""}),
            content_type="application/json",
        )
        txn_id = json.loads(resp.content)["id"]

        self.client.put(
            f"/api/transactions/{txn_id}",
            json.dumps({"account_id": self.account_b.pk, "category_id": None, "amount": "-200.00", "title": "Zakup", "description": ""}),
            content_type="application/json",
        )

        self.account_a.refresh_from_db()
        self.account_b.refresh_from_db()
        self.assertEqual(self.account_a.balance, Decimal("1000.00"))
        self.assertEqual(self.account_b.balance, Decimal("300.00"))


class UserDataIsolationTest(TestCase):
    """Dwóch użytkowników — żaden nie może widzieć ani modyfikować danych drugiego."""

    def setUp(self):
        self.user_a = User.objects.create_user(username="user_a", password="pass")
        self.user_b = User.objects.create_user(username="user_b", password="pass")
        self.client_a = Client()
        self.client_b = Client()
        self.client_a.login(username="user_a", password="pass")
        self.client_b.login(username="user_b", password="pass")

    def test_accounts_are_isolated(self):
        self.client_a.post(
            "/api/accounts",
            json.dumps({"name": "Konto A", "balance": "0.00", "currency": "PLN"}),
            content_type="application/json",
        )
        self.client_b.post(
            "/api/accounts",
            json.dumps({"name": "Konto B", "balance": "0.00", "currency": "PLN"}),
            content_type="application/json",
        )

        resp_a = json.loads(self.client_a.get("/api/accounts").content)
        resp_b = json.loads(self.client_b.get("/api/accounts").content)

        self.assertEqual(len(resp_a), 1)
        self.assertEqual(resp_a[0]["name"], "Konto A")
        self.assertEqual(len(resp_b), 1)
        self.assertEqual(resp_b[0]["name"], "Konto B")

    def test_cannot_delete_other_users_account(self):
        account_b = Account.objects.create(user=self.user_b, name="Cudze konto")
        resp = self.client_a.delete(f"/api/accounts/{account_b.pk}")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Account.objects.filter(pk=account_b.pk).exists())

    def test_transactions_are_isolated(self):
        account_a = Account.objects.create(user=self.user_a, name="Konto A")
        account_b = Account.objects.create(user=self.user_b, name="Konto B")
        Transaction.objects.create(account=account_a, category=None, amount=Decimal("100.00"), title="Transakcja A")
        Transaction.objects.create(account=account_b, category=None, amount=Decimal("200.00"), title="Transakcja B")

        resp_a = json.loads(self.client_a.get("/api/transactions").content)
        resp_b = json.loads(self.client_b.get("/api/transactions").content)

        self.assertEqual(len(resp_a), 1)
        self.assertEqual(resp_a[0]["title"], "Transakcja A")
        self.assertEqual(len(resp_b), 1)
        self.assertEqual(resp_b[0]["title"], "Transakcja B")

    def test_cannot_update_other_users_transaction(self):
        account_b = Account.objects.create(user=self.user_b, name="Konto B")
        txn_b = Transaction.objects.create(account=account_b, category=None, amount=Decimal("100.00"), title="Cudza")

        resp = self.client_a.put(
            f"/api/transactions/{txn_b.pk}",
            json.dumps({"account_id": account_b.pk, "category_id": None, "amount": "999.00", "title": "Zhackowana", "description": ""}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)
        txn_b.refresh_from_db()
        self.assertEqual(txn_b.title, "Cudza")


class CascadeDeleteTest(TestCase):
    """Usunięcie konta przez API kasuje transakcje i nie psuje sald innych kont."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client = Client()
        self.client.login(username="testuser", password="pass")

    def test_deleting_account_removes_its_transactions(self):
        account = Account.objects.create(user=self.user, name="Do usunięcia", balance=Decimal("0.00"))
        other_account = Account.objects.create(user=self.user, name="Zostaje", balance=Decimal("1000.00"))
        Transaction.objects.create(account=account, category=None, amount=Decimal("-100.00"), title="T1")
        Transaction.objects.create(account=account, category=None, amount=Decimal("-200.00"), title="T2")
        Transaction.objects.create(account=other_account, category=None, amount=Decimal("-50.00"), title="T3")

        self.client.delete(f"/api/accounts/{account.pk}")

        self.assertFalse(Account.objects.filter(pk=account.pk).exists())
        self.assertEqual(Transaction.objects.filter(account=account).count(), 0)
        self.assertEqual(Transaction.objects.filter(account=other_account).count(), 1)

        other_account.refresh_from_db()
        self.assertEqual(other_account.balance, Decimal("950.00"))

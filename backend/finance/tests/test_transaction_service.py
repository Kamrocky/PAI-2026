from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from finance.models import Account, Category, Transaction
from finance.transaction_service import create_transaction, delete_transaction, update_transaction


class CreateTransactionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.account = Account.objects.create(user=self.user, name="Konto", balance=Decimal("1000.00"))
        self.category = Category.objects.create(user=self.user, name="Jedzenie")

    def test_creates_transaction_and_updates_balance(self):
        create_transaction(
            account=self.account,
            category=self.category,
            amount=Decimal("-150.00"),
            title="Zakupy",
            description="",
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("850.00"))
        self.assertEqual(Transaction.objects.count(), 1)

    def test_income_increases_balance(self):
        create_transaction(
            account=self.account,
            category=None,
            amount=Decimal("500.00"),
            title="Przelew",
            description="",
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("1500.00"))

    def test_transaction_without_category(self):
        txn = create_transaction(
            account=self.account,
            category=None,
            amount=Decimal("100.00"),
            title="Bez kategorii",
            description="",
        )
        self.assertIsNone(txn.category)

    def test_create_with_custom_date(self):
        custom_date = datetime(2024, 6, 15, 12, 30, tzinfo=dt_timezone.utc)
        txn = create_transaction(
            account=self.account,
            category=None,
            amount=Decimal("10.00"),
            title="Z datą",
            description="",
            date=custom_date,
        )
        self.assertEqual(txn.date, custom_date)


class UpdateTransactionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.account = Account.objects.create(user=self.user, name="Konto", balance=Decimal("800.00"))
        self.txn = Transaction.objects.create(
            account=self.account,
            category=None,
            amount=Decimal("-200.00"),
            title="Stara transakcja",
        )

    def test_update_amount_adjusts_balance(self):
        update_transaction(
            self.txn,
            account=self.account,
            category=None,
            amount=Decimal("-100.00"),
            title="Stara transakcja",
            description="",
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("900.00"))

    def test_update_moves_to_other_account(self):
        other_account = Account.objects.create(user=self.user, name="Inne konto", balance=Decimal("0.00"))
        update_transaction(
            self.txn,
            account=other_account,
            category=None,
            amount=Decimal("-200.00"),
            title="Przeniesiona",
            description="",
        )
        self.account.refresh_from_db()
        other_account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("1000.00"))
        self.assertEqual(other_account.balance, Decimal("-200.00"))

    def test_update_date(self):
        new_date = datetime(2023, 1, 1, 8, 0, tzinfo=dt_timezone.utc)
        update_transaction(
            self.txn,
            account=self.account,
            category=None,
            amount=Decimal("-200.00"),
            title="Stara transakcja",
            description="",
            date=new_date,
        )
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.date, new_date)


class DeleteTransactionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.account = Account.objects.create(user=self.user, name="Konto", balance=Decimal("500.00"))

    def test_delete_reverses_balance(self):
        txn = Transaction.objects.create(
            account=self.account,
            category=None,
            amount=Decimal("-300.00"),
            title="Wydatek",
        )
        delete_transaction(txn)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("800.00"))
        self.assertEqual(Transaction.objects.count(), 0)

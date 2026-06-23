from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from finance.constants import DEFAULT_CATEGORY_COLOR
from finance.models import Account, Category, Transaction


class AccountModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")

    def test_create_account_with_defaults(self):
        account = Account.objects.create(user=self.user, name="Konto główne")
        self.assertEqual(account.balance, Decimal("0.00"))
        self.assertEqual(account.currency, "PLN")
        self.assertEqual(account.user, self.user)

    def test_account_str(self):
        account = Account.objects.create(user=self.user, name="Oszczędności", balance=Decimal("1500.00"))
        self.assertIn("Oszczędności", str(account))
        self.assertIn("1500.00", str(account))

    def test_account_belongs_to_user(self):
        other_user = User.objects.create_user(username="other", password="pass")
        Account.objects.create(user=self.user, name="Moje konto")
        Account.objects.create(user=other_user, name="Cudze konto")
        self.assertEqual(Account.objects.filter(user=self.user).count(), 1)


class CategoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")

    def test_create_expense_category(self):
        category = Category.objects.create(user=self.user, name="Jedzenie")
        self.assertFalse(category.is_income)
        self.assertEqual(category.color, DEFAULT_CATEGORY_COLOR)

    def test_create_income_category(self):
        category = Category.objects.create(user=self.user, name="Wynagrodzenie", is_income=True)
        self.assertTrue(category.is_income)

    def test_category_deletion_sets_transaction_null(self):
        account = Account.objects.create(user=self.user, name="Konto")
        category = Category.objects.create(user=self.user, name="Do usunięcia")
        txn = Transaction.objects.create(
            account=account, category=category, amount=Decimal("100.00"), title="Test"
        )
        category.delete()
        txn.refresh_from_db()
        self.assertIsNone(txn.category)


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.account = Account.objects.create(user=self.user, name="Konto")
        self.category = Category.objects.create(user=self.user, name="Jedzenie")

    def test_create_transaction(self):
        txn = Transaction.objects.create(
            account=self.account,
            category=self.category,
            amount=Decimal("49.99"),
            title="Zakupy spożywcze",
        )
        self.assertEqual(txn.amount, Decimal("49.99"))
        self.assertEqual(txn.account, self.account)
        self.assertIsNotNone(txn.date)

    def test_transaction_without_category(self):
        txn = Transaction.objects.create(
            account=self.account,
            category=None,
            amount=Decimal("10.00"),
            title="Bez kategorii",
        )
        self.assertIsNone(txn.category)

    def test_cascade_delete_with_account(self):
        Transaction.objects.create(
            account=self.account, category=None, amount=Decimal("50.00"), title="Test"
        )
        self.account.delete()
        self.assertEqual(Transaction.objects.count(), 0)

from datetime import date, datetime, time
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from finance.models import Account, Category
from finance.transaction_forms import (
    parse_transaction_date,
    validate_category_amount_type,
    validate_transaction_form,
)


class ParseTransactionDateTest(TestCase):
    def test_parses_date_only_as_local_midnight(self):
        parsed = parse_transaction_date("2024-06-15")

        self.assertIsNotNone(parsed)
        expected = timezone.make_aware(
            datetime.combine(date(2024, 6, 15), time.min),
            timezone.get_current_timezone(),
        )
        self.assertEqual(parsed, expected)

    def test_parses_datetime_for_backward_compatibility(self):
        parsed = parse_transaction_date("2024-06-15T14:30:00")

        self.assertIsNotNone(parsed)
        expected = timezone.make_aware(
            datetime(2024, 6, 15, 14, 30, 0),
            timezone.get_current_timezone(),
        )
        self.assertEqual(parsed, expected)

    def test_empty_value_returns_none(self):
        self.assertIsNone(parse_transaction_date(""))
        self.assertIsNone(parse_transaction_date("   "))

    def test_invalid_value_returns_none(self):
        self.assertIsNone(parse_transaction_date("nie-data"))


class ValidateCategoryAmountTypeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jan@example.com", password="pass")
        self.expense = Category.objects.create(user=self.user, name="Jedzenie", is_income=False)
        self.income = Category.objects.create(user=self.user, name="Wynagrodzenie", is_income=True)

    def test_expense_category_rejected_for_positive_amount(self):
        error = validate_category_amount_type(self.expense, Decimal("100.00"))
        self.assertEqual(error, "Dla wpływu wybierz kategorię wpływów.")

    def test_income_category_rejected_for_negative_amount(self):
        error = validate_category_amount_type(self.income, Decimal("-50.00"))
        self.assertEqual(error, "Dla wydatku wybierz kategorię wydatków.")

    def test_matching_category_types_are_allowed(self):
        self.assertIsNone(validate_category_amount_type(self.expense, Decimal("-50.00")))
        self.assertIsNone(validate_category_amount_type(self.income, Decimal("100.00")))
        self.assertIsNone(validate_category_amount_type(None, Decimal("100.00")))


class ValidateTransactionFormCategoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jan@example.com", password="pass")
        self.account = Account.objects.create(
            user=self.user, name="Główne", balance=Decimal("0.00")
        )
        self.expense = Category.objects.create(user=self.user, name="Jedzenie", is_income=False)

    def test_rejects_wrong_category_type_in_form(self):
        _, error = validate_transaction_form(
            self.user,
            str(self.account.pk),
            str(self.expense.pk),
            "100.00",
            "Wpływ",
            "",
            "2024-06-15",
        )

        self.assertEqual(error, "Dla wpływu wybierz kategorię wpływów.")


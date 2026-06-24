from datetime import date, datetime, time

from django.test import TestCase
from django.utils import timezone

from finance.transaction_forms import parse_transaction_date


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

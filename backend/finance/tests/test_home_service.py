from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.utils import timezone

from finance.home_service import (
    HOME_ACCOUNT_SESSION_KEY,
    HOME_SLOT_NEW,
    get_account_period_stats,
    get_comparison_labels,
    get_home_context,
    get_home_navigation,
    get_month_over_month_comparison,
    go_to_carousel_slot,
    navigate_home_slot,
    resolve_active_account,
    resolve_home_slot,
    set_active_account_id,
    set_home_create_slot,
)
from finance.models import Account, Transaction


class HomeServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jan@example.com", password="pass")
        self.account = Account.objects.create(
            user=self.user,
            name="Główne",
            balance=Decimal("1000.00"),
            currency="PLN",
        )
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get("/")
        request.session = self.client.session
        return request

    def test_period_stats_sums_income_and_expenses(self):
        now = timezone.now()
        Transaction.objects.create(
            account=self.account,
            amount=Decimal("200.00"),
            title="Wypłata",
            date=now - timedelta(days=5),
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal("-50.00"),
            title="Zakupy",
            date=now - timedelta(days=3),
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal("-20.00"),
            title="Stare",
            date=now - timedelta(days=40),
        )

        stats = get_account_period_stats(self.account, period_days=30)
        self.assertEqual(stats.income, Decimal("200.00"))
        self.assertEqual(stats.expenses, Decimal("50.00"))

    def test_period_stats_empty_account(self):
        stats = get_account_period_stats(self.account)
        self.assertEqual(stats.income, Decimal("0.00"))
        self.assertEqual(stats.expenses, Decimal("0.00"))

    def test_month_comparison_without_previous_data(self):
        now = timezone.now()
        Transaction.objects.create(
            account=self.account,
            amount=Decimal("-10.00"),
            title="Bieżący",
            date=now,
        )

        comparison = get_month_over_month_comparison(self.account)
        labels = get_comparison_labels(comparison)

        self.assertFalse(comparison.has_previous_data)
        self.assertEqual(labels["expense_label"], "Brak danych za poprzedni miesiąc.")

    def test_month_comparison_with_previous_data(self):
        now = timezone.now()
        current_start = now.replace(day=1, hour=12, minute=0, second=0, microsecond=0)
        if current_start.month == 1:
            previous = current_start.replace(year=current_start.year - 1, month=12, day=15)
        else:
            previous = current_start.replace(month=current_start.month - 1, day=15)

        Transaction.objects.create(
            account=self.account,
            amount=Decimal("-100.00"),
            title="Poprzedni miesiąc",
            date=previous,
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal("-50.00"),
            title="Bieżący miesiąc",
            date=current_start,
        )

        comparison = get_month_over_month_comparison(self.account)
        labels = get_comparison_labels(comparison)

        self.assertTrue(comparison.has_previous_data)
        self.assertEqual(comparison.expense_change_pct, Decimal("-50.0"))
        self.assertIn("wydatków", labels["expense_label"])

    def test_month_comparison_unchanged_shows_same_message(self):
        now = timezone.now()
        current_start = now.replace(day=1, hour=12, minute=0, second=0, microsecond=0)
        if current_start.month == 1:
            previous = current_start.replace(year=current_start.year - 1, month=12, day=15)
        else:
            previous = current_start.replace(month=current_start.month - 1, day=15)

        Transaction.objects.create(
            account=self.account,
            amount=Decimal("-100.00"),
            title="Poprzedni miesiąc",
            date=previous,
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal("-100.00"),
            title="Bieżący miesiąc",
            date=current_start,
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal("200.00"),
            title="Wpływ poprzedni",
            date=previous,
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal("200.00"),
            title="Wpływ bieżący",
            date=current_start,
        )

        comparison = get_month_over_month_comparison(self.account)
        labels = get_comparison_labels(comparison)

        self.assertEqual(comparison.expense_change_pct, Decimal("0.0"))
        self.assertEqual(comparison.income_change_pct, Decimal("0.0"))
        self.assertEqual(
            labels["expense_label"],
            "Twoje wydatki są takie same jak w poprzednim miesiącu.",
        )
        self.assertEqual(
            labels["income_label"],
            "Twoje wpływy są takie same jak w poprzednim miesiącu.",
        )

    def test_resolve_active_account_uses_session(self):
        other = Account.objects.create(user=self.user, name="Oszczędności")
        request = self._request()
        set_active_account_id(request, other.pk)

        active = resolve_active_account(request, self.user)
        self.assertEqual(active.pk, other.pk)

    def test_get_home_context_includes_active_account(self):
        request = self._request()
        context = get_home_context(self.user, request)

        self.assertEqual(context["active_account"].pk, self.account.pk)
        self.assertEqual(len(context["accounts"]), 1)
        self.assertIsNotNone(context["period_stats"])
        self.assertEqual(context["period_days"], 30)
        self.assertEqual(request.session[HOME_ACCOUNT_SESSION_KEY], self.account.pk)

    def test_empty_accounts_default_to_create_slot(self):
        self.account.delete()
        request = self._request()
        context = get_home_context(self.user, request)

        self.assertTrue(context["is_create_slot"])
        self.assertFalse(context["can_go_prev"])
        self.assertFalse(context["can_go_next"])
        self.assertIsNone(context["active_account"])

    def test_navigate_next_reaches_create_slot(self):
        other = Account.objects.create(user=self.user, name="Nowsze")
        request = self._request()
        set_active_account_id(request, other.pk)

        navigate_home_slot(request, self.user, "next")

        self.assertEqual(resolve_home_slot(request, self.user), HOME_SLOT_NEW)
        navigation = get_home_navigation(request, self.user)
        self.assertTrue(navigation["is_create_slot"])
        self.assertTrue(navigation["can_go_prev"])
        self.assertFalse(navigation["can_go_next"])

    def test_navigate_prev_from_create_slot_shows_newest_account(self):
        other = Account.objects.create(user=self.user, name="Nowsze")
        request = self._request()
        set_home_create_slot(request)

        navigate_home_slot(request, self.user, "prev")

        self.assertEqual(resolve_active_account(request, self.user).pk, other.pk)

    def test_go_to_carousel_slot_selects_account_by_index(self):
        other = Account.objects.create(user=self.user, name="Nowsze")
        request = self._request()

        go_to_carousel_slot(request, self.user, 1)

        self.assertEqual(resolve_active_account(request, self.user).pk, other.pk)
        self.assertEqual(get_home_navigation(request, self.user)["carousel_slot_index"], 1)

    def test_go_to_carousel_slot_selects_create_slot(self):
        Account.objects.create(user=self.user, name="Nowsze")
        request = self._request()

        go_to_carousel_slot(request, self.user, 2)

        self.assertEqual(resolve_home_slot(request, self.user), HOME_SLOT_NEW)
        self.assertTrue(get_home_navigation(request, self.user)["is_create_slot"])

    def test_accounts_ordered_oldest_first(self):
        older = self.account
        newer = Account.objects.create(user=self.user, name="Nowsze")
        request = self._request()
        request.session.pop(HOME_ACCOUNT_SESSION_KEY, None)

        context = get_home_context(self.user, request)

        self.assertEqual(context["accounts"][0].pk, older.pk)
        self.assertEqual(context["accounts"][1].pk, newer.pk)
        self.assertEqual(context["active_account"].pk, older.pk)

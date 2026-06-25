"""Agregacja danych do strony Statystyki (wykresy ApexCharts).

Wszystko liczone PER KONTO (jedna waluta), więc nie mieszamy walut.
Wykorzystuje pomocnicze funkcje z home_service tam, gdzie to możliwe.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Sum
from django.http import HttpRequest
from django.utils import timezone

from .constants import CATEGORY_COLOR_PALETTE
from .home_service import _sum_income_and_expenses, get_user_accounts
from .models import Account, Transaction

STATS_ACCOUNT_SESSION_KEY = "stats_account_id"
STATS_PERIOD_SESSION_KEY = "stats_period"

INCOME_COLOR = "#4DB6A0"
EXPENSE_COLOR = "#D97B8C"
UNCATEGORIZED_COLOR = "#7C9EB2"

# (klucz, etykieta, liczba_dni) — None dla "bieżący miesiąc"
PERIOD_OPTIONS = [
    ("month", "Ten miesiąc", None),
    ("30", "30 dni", 30),
    ("90", "3 miesiące", 90),
    ("180", "6 miesięcy", 180),
    ("365", "Rok", 365),
]
DEFAULT_PERIOD = "30"
MONTHLY_TREND_MONTHS = 6
POLISH_MONTHS_SHORT = [
    "sty", "lut", "mar", "kwi", "maj", "cze",
    "lip", "sie", "wrz", "paź", "lis", "gru",
]


@dataclass(frozen=True)
class StatsNavigation:
    accounts: list[Account]
    active_account: Account | None
    active_index: int
    can_go_prev: bool
    can_go_next: bool


# ----------------------------------------------------------------------------
# Wybór konta (osobny stan sesji, by nie kolidować z karuzelą na Home)
# ----------------------------------------------------------------------------
def resolve_stats_account(request: HttpRequest, user: AbstractBaseUser) -> Account | None:
    accounts = get_user_accounts(user)
    if not accounts:
        return None

    stored = request.session.get(STATS_ACCOUNT_SESSION_KEY)
    for account in accounts:
        if account.pk == stored:
            return account

    request.session[STATS_ACCOUNT_SESSION_KEY] = accounts[0].pk
    return accounts[0]


def set_stats_account(request: HttpRequest, account_id: int) -> None:
    request.session[STATS_ACCOUNT_SESSION_KEY] = account_id


def navigate_stats_account(request: HttpRequest, user: AbstractBaseUser, direction: str) -> None:
    accounts = get_user_accounts(user)
    if not accounts:
        return
    active = resolve_stats_account(request, user)
    index = next((i for i, a in enumerate(accounts) if a.pk == active.pk), 0)
    if direction == "prev" and index > 0:
        set_stats_account(request, accounts[index - 1].pk)
    elif direction == "next" and index < len(accounts) - 1:
        set_stats_account(request, accounts[index + 1].pk)


def select_stats_slot(request: HttpRequest, user: AbstractBaseUser, slot_index: int) -> None:
    accounts = get_user_accounts(user)
    if 0 <= slot_index < len(accounts):
        set_stats_account(request, accounts[slot_index].pk)


def get_stats_navigation(request: HttpRequest, user: AbstractBaseUser) -> StatsNavigation:
    accounts = get_user_accounts(user)
    active = resolve_stats_account(request, user)
    if active is None:
        return StatsNavigation([], None, 0, False, False)
    index = next((i for i, a in enumerate(accounts) if a.pk == active.pk), 0)
    return StatsNavigation(
        accounts=accounts,
        active_account=active,
        active_index=index,
        can_go_prev=index > 0,
        can_go_next=index < len(accounts) - 1,
    )


# ----------------------------------------------------------------------------
# Wybór okresu
# ----------------------------------------------------------------------------
def resolve_stats_period(request: HttpRequest) -> str:
    period = request.session.get(STATS_PERIOD_SESSION_KEY, DEFAULT_PERIOD)
    valid = {key for key, _, _ in PERIOD_OPTIONS}
    return period if period in valid else DEFAULT_PERIOD


def set_stats_period(request: HttpRequest, period: str) -> None:
    valid = {key for key, _, _ in PERIOD_OPTIONS}
    if period in valid:
        request.session[STATS_PERIOD_SESSION_KEY] = period


def _period_start(period: str, now: datetime) -> datetime:
    for key, _, days in PERIOD_OPTIONS:
        if key == period:
            if days is None:  # bieżący miesiąc
                return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return now - timedelta(days=days)
    return now - timedelta(days=30)


# ----------------------------------------------------------------------------
# Budowanie danych do wykresów
# ----------------------------------------------------------------------------
def _category_breakdown(transactions, *, income: bool) -> list[dict]:
    if income:
        qs = transactions.filter(amount__gt=0)
    else:
        qs = transactions.filter(amount__lt=0)

    grouped = (
        qs.values("category__name", "category__color")
        .annotate(total=Sum("amount"))
        .order_by("-total" if income else "total")
    )

    result = []
    for row in grouped:
        value = abs(float(row["total"] or 0))
        if value == 0:
            continue
        result.append({
            "name": row["category__name"] or "Bez kategorii",
            "color": row["category__color"] or UNCATEGORIZED_COLOR,
            "value": round(value, 2),
        })
    return result


def _balance_over_time(account: Account, since: datetime, now: datetime) -> dict:
    txns = list(
        Transaction.objects.filter(account=account, date__gte=since, date__lte=now)
        .order_by("date")
        .values_list("date", "amount")
    )
    total_in_period = sum((amount for _, amount in txns), Decimal("0.00"))
    start_balance = account.balance - total_in_period

    per_day: dict = defaultdict(Decimal)
    for date, amount in txns:
        per_day[timezone.localtime(date).date()] += amount

    labels: list[str] = []
    values: list[float] = []
    running = start_balance
    cursor = timezone.localtime(since).date()
    end = timezone.localtime(now).date()
    while cursor <= end:
        running += per_day.get(cursor, Decimal("0.00"))
        labels.append(cursor.isoformat())
        values.append(round(float(running), 2))
        cursor += timedelta(days=1)

    return {"labels": labels, "values": values}


def _monthly_trend(account: Account, now: datetime, months: int = MONTHLY_TREND_MONTHS) -> dict:
    labels: list[str] = []
    income_series: list[float] = []
    expense_series: list[float] = []

    # zaczynamy od najstarszego miesiąca
    year = now.year
    month = now.month
    buckets: list[tuple[int, int]] = []
    for _ in range(months):
        buckets.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    buckets.reverse()

    for y, m in buckets:
        start = datetime(y, m, 1, tzinfo=now.tzinfo)
        if m == 12:
            end = datetime(y + 1, 1, 1, tzinfo=now.tzinfo)
        else:
            end = datetime(y, m + 1, 1, tzinfo=now.tzinfo)
        txns = Transaction.objects.filter(account=account, date__gte=start, date__lt=end)
        income, expenses = _sum_income_and_expenses(txns)
        labels.append(POLISH_MONTHS_SHORT[m - 1])
        income_series.append(round(float(income), 2))
        expense_series.append(round(float(expenses), 2))

    return {"labels": labels, "income": income_series, "expenses": expense_series}


def _year_over_year(account: Account, now: datetime) -> dict:
    def month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
        start = datetime(year, month, 1, tzinfo=now.tzinfo)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=now.tzinfo)
        else:
            end = datetime(year, month + 1, 1, tzinfo=now.tzinfo)
        return start, end

    cur_start, cur_end = month_bounds(now.year, now.month)
    prev_start, prev_end = month_bounds(now.year - 1, now.month)

    cur_txns = Transaction.objects.filter(account=account, date__gte=cur_start, date__lt=cur_end)
    prev_txns = Transaction.objects.filter(account=account, date__gte=prev_start, date__lt=prev_end)

    cur_income, cur_expenses = _sum_income_and_expenses(cur_txns)
    prev_income, prev_expenses = _sum_income_and_expenses(prev_txns)

    month_label = POLISH_MONTHS_SHORT[now.month - 1]
    return {
        "labels": [f"{month_label} {now.year - 1}", f"{month_label} {now.year}"],
        "income": [round(float(prev_income), 2), round(float(cur_income), 2)],
        "expenses": [round(float(prev_expenses), 2), round(float(cur_expenses), 2)],
    }


def build_chart_data(account: Account, period: str) -> dict:
    now = timezone.now()
    since = _period_start(period, now)
    period_txns = Transaction.objects.filter(account=account, date__gte=since, date__lte=now)
    income, expenses = _sum_income_and_expenses(period_txns)

    return {
        "currency": account.currency,
        "balance": round(float(account.balance), 2),
        "income": round(float(income), 2),
        "expenses": round(float(expenses), 2),
        "net": round(float(income - expenses), 2),
        "incomeVsExpense": {
            "income": round(float(income), 2),
            "expenses": round(float(expenses), 2),
            "incomeColor": INCOME_COLOR,
            "expenseColor": EXPENSE_COLOR,
        },
        "expenseByCategory": _category_breakdown(period_txns, income=False),
        "incomeByCategory": _category_breakdown(period_txns, income=True),
        "balanceOverTime": _balance_over_time(account, since, now),
        "monthlyTrend": _monthly_trend(account, now),
        "yearOverYear": _year_over_year(account, now),
        "incomeColor": INCOME_COLOR,
        "expenseColor": EXPENSE_COLOR,
        "palette": list(CATEGORY_COLOR_PALETTE),
    }


def get_stats_context(request: HttpRequest, user: AbstractBaseUser) -> dict:
    from .auth_utils import get_display_name

    navigation = get_stats_navigation(request, user)
    period = resolve_stats_period(request)

    context: dict = {
        "display_name": get_display_name(user),
        "active_tab": "stats",
        "accounts": navigation.accounts,
        "active_account": navigation.active_account,
        "active_index": navigation.active_index,
        "can_go_prev": navigation.can_go_prev,
        "can_go_next": navigation.can_go_next,
        "period_options": PERIOD_OPTIONS,
        "active_period": period,
        "chart_data": None,
        "has_data": False,
    }

    if navigation.active_account is not None:
        chart_data = build_chart_data(navigation.active_account, period)
        context["chart_data"] = chart_data
        context["has_data"] = (
            chart_data["income"] > 0
            or chart_data["expenses"] > 0
            or bool(chart_data["balanceOverTime"]["values"])
        )

    return context

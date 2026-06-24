from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpRequest
from django.utils import timezone

from .constants import ALLOWED_CURRENCIES, CURRENCY_LABELS
from .models import Account, Category, Transaction

HOME_ACCOUNT_SESSION_KEY = "home_account_id"
HOME_SLOT_NEW = "new"
HOME_TXN_EXPANDED_KEY = "home_txn_expanded"
PERIOD_DAYS = 30
COLLAPSED_TXN_LIMIT = 5
EXPANDED_TXN_PAGE_SIZE = 10


@dataclass(frozen=True)
class PeriodStats:
    income: Decimal
    expenses: Decimal


@dataclass(frozen=True)
class MonthComparison:
    income_change_pct: Decimal | None
    expense_change_pct: Decimal | None
    has_previous_data: bool


@dataclass(frozen=True)
class AccountTransactionsPage:
    transactions: list[Transaction]
    page: int
    num_pages: int
    total_count: int
    has_more: bool
    expanded: bool
    page_size: int
    page_numbers: list[int]


def clear_transactions_view_state(request: HttpRequest) -> None:
    request.session.pop(HOME_TXN_EXPANDED_KEY, None)


def set_transactions_expanded(request: HttpRequest, expanded: bool) -> None:
    if expanded:
        request.session[HOME_TXN_EXPANDED_KEY] = True
    else:
        request.session.pop(HOME_TXN_EXPANDED_KEY, None)


def is_transactions_expanded(request: HttpRequest) -> bool:
    return bool(request.session.get(HOME_TXN_EXPANDED_KEY))


def get_account_transactions(
    account: Account,
    page: int = 1,
    *,
    expanded: bool = False,
) -> AccountTransactionsPage:
    queryset = (
        Transaction.objects.filter(account=account)
        .select_related("category")
        .order_by("-date", "-id")
    )
    total_count = queryset.count()

    if not expanded:
        return AccountTransactionsPage(
            transactions=list(queryset[:COLLAPSED_TXN_LIMIT]),
            page=1,
            num_pages=1,
            total_count=total_count,
            has_more=total_count > COLLAPSED_TXN_LIMIT,
            expanded=False,
            page_size=COLLAPSED_TXN_LIMIT,
            page_numbers=[1],
        )

    paginator = Paginator(queryset, EXPANDED_TXN_PAGE_SIZE)
    page_obj = paginator.get_page(page)
    return AccountTransactionsPage(
        transactions=list(page_obj.object_list),
        page=page_obj.number,
        num_pages=paginator.num_pages,
        total_count=total_count,
        has_more=total_count > COLLAPSED_TXN_LIMIT,
        expanded=True,
        page_size=EXPANDED_TXN_PAGE_SIZE,
        page_numbers=list(paginator.page_range),
    )


def get_user_categories(user: AbstractBaseUser) -> list[Category]:
    return list(Category.objects.filter(user=user).order_by("name", "id"))


def get_home_transactions_context(
    user: AbstractBaseUser,
    request: HttpRequest,
    active_account: Account | None,
) -> dict:
    if active_account is None:
        return {
            "transactions_page": None,
            "transactions_expanded": False,
            "categories": [],
        }

    expanded = is_transactions_expanded(request)
    page = max(1, int(request.GET.get("page", 1)))
    return {
        "transactions_page": get_account_transactions(
            active_account,
            page=page,
            expanded=expanded,
        ),
        "transactions_expanded": expanded,
        "categories": get_user_categories(user),
    }


def get_user_accounts(user: AbstractBaseUser) -> list[Account]:
    return list(Account.objects.filter(user=user).order_by("id"))


def set_home_slot(request: HttpRequest, slot: int | str) -> None:
    if request.session.get(HOME_ACCOUNT_SESSION_KEY) != slot:
        clear_transactions_view_state(request)
    request.session[HOME_ACCOUNT_SESSION_KEY] = slot


def set_active_account_id(request: HttpRequest, account_id: int) -> None:
    set_home_slot(request, account_id)


def set_home_create_slot(request: HttpRequest) -> None:
    set_home_slot(request, HOME_SLOT_NEW)


def _normalize_slot_value(slot) -> int | str | None:
    if slot == HOME_SLOT_NEW:
        return HOME_SLOT_NEW
    if isinstance(slot, int):
        return slot
    if isinstance(slot, str) and slot.isdigit():
        return int(slot)
    return None


def resolve_home_slot(request: HttpRequest, user: AbstractBaseUser) -> int | str:
    accounts = get_user_accounts(user)
    if not accounts:
        return HOME_SLOT_NEW

    slot = _normalize_slot_value(request.session.get(HOME_ACCOUNT_SESSION_KEY))
    if slot == HOME_SLOT_NEW:
        return HOME_SLOT_NEW
    if slot is not None and any(account.pk == slot for account in accounts):
        return slot

    oldest = accounts[0]
    set_home_slot(request, oldest.pk)
    return oldest.pk


def get_active_account(user: AbstractBaseUser, account_id: int | None) -> Account | None:
    if account_id is None:
        return None
    return Account.objects.filter(user=user, pk=account_id).first()


def resolve_active_account(request: HttpRequest, user: AbstractBaseUser) -> Account | None:
    slot = resolve_home_slot(request, user)
    if slot == HOME_SLOT_NEW:
        return None
    return get_active_account(user, slot)


def get_home_navigation(request: HttpRequest, user: AbstractBaseUser) -> dict[str, bool | int | list[int]]:
    accounts = get_user_accounts(user)
    slot = resolve_home_slot(request, user)
    is_create_slot = slot == HOME_SLOT_NEW

    if not accounts:
        return {
            "is_create_slot": True,
            "can_go_prev": False,
            "can_go_next": False,
            "carousel_slot_index": 0,
            "carousel_slot_count": 1,
            "carousel_dots": [0],
        }

    slot_count = len(accounts) + 1
    if is_create_slot:
        slot_index = len(accounts)
        return {
            "is_create_slot": True,
            "can_go_prev": True,
            "can_go_next": False,
            "carousel_slot_index": slot_index,
            "carousel_slot_count": slot_count,
            "carousel_dots": list(range(slot_count)),
        }

    index = next(i for i, account in enumerate(accounts) if account.pk == slot)
    return {
        "is_create_slot": False,
        "can_go_prev": index > 0,
        "can_go_next": True,
        "carousel_slot_index": index,
        "carousel_slot_count": slot_count,
        "carousel_dots": list(range(slot_count)),
    }


def navigate_home_slot(request: HttpRequest, user: AbstractBaseUser, direction: str) -> None:
    accounts = get_user_accounts(user)
    if not accounts:
        set_home_create_slot(request)
        return

    current = resolve_home_slot(request, user)
    if direction == "prev":
        if current == HOME_SLOT_NEW:
            set_home_slot(request, accounts[-1].pk)
            return
        index = next(i for i, account in enumerate(accounts) if account.pk == current)
        if index > 0:
            set_home_slot(request, accounts[index - 1].pk)
        return

    if direction == "next":
        if current == HOME_SLOT_NEW:
            return
        index = next(i for i, account in enumerate(accounts) if account.pk == current)
        if index == len(accounts) - 1:
            set_home_create_slot(request)
        else:
            set_home_slot(request, accounts[index + 1].pk)


def go_to_carousel_slot(request: HttpRequest, user: AbstractBaseUser, slot_index: int) -> None:
    accounts = get_user_accounts(user)
    if not accounts:
        set_home_create_slot(request)
        return

    last_index = len(accounts)
    if slot_index < 0 or slot_index > last_index:
        return

    if slot_index == last_index:
        set_home_create_slot(request)
    else:
        set_home_slot(request, accounts[slot_index].pk)


def _sum_income_and_expenses(transactions) -> tuple[Decimal, Decimal]:
    income = transactions.filter(amount__gt=0).aggregate(total=Sum("amount"))["total"]
    expenses_raw = transactions.filter(amount__lt=0).aggregate(total=Sum("amount"))["total"]
    income_total = income or Decimal("0.00")
    expenses_total = abs(expenses_raw or Decimal("0.00"))
    return income_total, expenses_total


def get_account_period_stats(account: Account, period_days: int = PERIOD_DAYS) -> PeriodStats:
    since = timezone.now() - timedelta(days=period_days)
    transactions = Transaction.objects.filter(account=account, date__gte=since)
    income, expenses = _sum_income_and_expenses(transactions)
    return PeriodStats(income=income, expenses=expenses)


def _month_start(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_month_over_month_comparison(account: Account) -> MonthComparison:
    now = timezone.now()
    current_start = _month_start(now)
    if current_start.month == 1:
        previous_start = current_start.replace(year=current_start.year - 1, month=12)
    else:
        previous_start = current_start.replace(month=current_start.month - 1)

    current_transactions = Transaction.objects.filter(
        account=account,
        date__gte=current_start,
        date__lte=now,
    )
    previous_transactions = Transaction.objects.filter(
        account=account,
        date__gte=previous_start,
        date__lt=current_start,
    )

    current_income, current_expenses = _sum_income_and_expenses(current_transactions)
    previous_income, previous_expenses = _sum_income_and_expenses(previous_transactions)

    def percent_change(current: Decimal, previous: Decimal) -> Decimal | None:
        if previous == 0:
            return None
        return ((current - previous) / previous * Decimal("100")).quantize(Decimal("0.1"))

    return MonthComparison(
        income_change_pct=percent_change(current_income, previous_income),
        expense_change_pct=percent_change(current_expenses, previous_expenses),
        has_previous_data=previous_transactions.exists(),
    )


def _format_expense_change_label(change_pct: Decimal | None) -> str:
    if change_pct is None:
        return "Brak wydatków w poprzednim miesiącu do porównania."
    if change_pct > 0:
        return f"+{change_pct}% wydatków względem poprzedniego miesiąca."
    if change_pct < 0:
        return f"{change_pct}% wydatków względem poprzedniego miesiąca."
    return "Twoje wydatki są takie same jak w poprzednim miesiącu."


def _format_income_change_label(change_pct: Decimal | None) -> str:
    if change_pct is None:
        return "Brak wpływów w poprzednim miesiącu do porównania."
    if change_pct > 0:
        return f"+{change_pct}% wpływów względem poprzedniego miesiąca."
    if change_pct < 0:
        return f"{change_pct}% wpływów względem poprzedniego miesiąca."
    return "Twoje wpływy są takie same jak w poprzednim miesiącu."


def get_comparison_labels(comparison: MonthComparison) -> dict[str, str]:
    if not comparison.has_previous_data:
        message = "Brak danych za poprzedni miesiąc."
        return {"income_label": message, "expense_label": message}

    return {
        "income_label": _format_income_change_label(comparison.income_change_pct),
        "expense_label": _format_expense_change_label(comparison.expense_change_pct),
    }


def get_home_context(user: AbstractBaseUser, request: HttpRequest) -> dict:
    from .auth_utils import get_display_name

    accounts = get_user_accounts(user)
    active_account = resolve_active_account(request, user)
    navigation = get_home_navigation(request, user)

    context: dict = {
        "display_name": get_display_name(user),
        "accounts": accounts,
        "active_account": active_account,
        "active_tab": "home",
        "allowed_currencies": ALLOWED_CURRENCIES,
        "currency_choices": [
            (code, CURRENCY_LABELS.get(code, code)) for code in ALLOWED_CURRENCIES
        ],
        "period_days": PERIOD_DAYS,
        "period_stats": None,
        "month_comparison": None,
        "comparison_labels": None,
        **navigation,
    }

    if active_account is not None:
        comparison = get_month_over_month_comparison(active_account)
        context["period_stats"] = get_account_period_stats(active_account)
        context["month_comparison"] = comparison
        context["comparison_labels"] = get_comparison_labels(comparison)
        context.update(get_home_transactions_context(user, request, active_account))

    return context

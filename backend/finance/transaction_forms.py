from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from django.utils import timezone
from pydantic import ValidationError as PydanticValidationError

from .api_accounts import get_user_account
from .api_transactions import resolve_category
from .schemas import TransactionIn


def parse_optional_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _aware_local_midnight(parsed_date: date) -> datetime:
    local_midnight = datetime.combine(parsed_date, time.min)
    return timezone.make_aware(local_midnight, timezone.get_current_timezone())


def parse_transaction_date(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None

    try:
        parsed_date = date.fromisoformat(value)
    except ValueError:
        parsed_date = None

    if parsed_date is not None:
        return _aware_local_midnight(parsed_date)

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def validate_transaction_form(
    account_id: str,
    category_id: str,
    amount: str,
    title: str,
    description: str,
    date: str,
) -> tuple[TransactionIn | None, str | None]:
    parsed_account_id = parse_optional_int(account_id)
    if parsed_account_id is None:
        return None, "Wybierz konto."

    try:
        amount_decimal = Decimal(amount)
    except InvalidOperation:
        return None, "Nieprawidłowa kwota."

    parsed_date = parse_transaction_date(date)
    if date.strip() and parsed_date is None:
        return None, "Nieprawidłowa data transakcji."

    try:
        payload = TransactionIn(
            account_id=parsed_account_id,
            category_id=parse_optional_int(category_id),
            amount=amount_decimal,
            title=title,
            description=description or "",
            date=parsed_date,
        )
    except PydanticValidationError as exc:
        messages = [err["msg"] for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None


def apply_transaction_payload(user, payload: TransactionIn):
    account = get_user_account(user, payload.account_id)
    category = resolve_category(user, payload.category_id)
    data = payload.model_dump()
    return account, category, data

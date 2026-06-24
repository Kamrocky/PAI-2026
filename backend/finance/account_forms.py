from decimal import Decimal, InvalidOperation

from pydantic import ValidationError as PydanticValidationError

from .schemas import AccountIn, AccountUpdate


def validate_account_create(
    name: str,
    currency: str,
    balance: str,
) -> tuple[AccountIn | None, str | None]:
    try:
        balance_decimal = Decimal(balance or "0.00")
    except InvalidOperation:
        return None, "Nieprawidłowe saldo początkowe."

    try:
        payload = AccountIn(name=name, currency=currency, balance=balance_decimal)
    except PydanticValidationError as exc:
        messages = [err["msg"] for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None


def validate_account_edit(name: str) -> tuple[AccountUpdate | None, str | None]:
    try:
        payload = AccountUpdate(name=name)
    except PydanticValidationError as exc:
        messages = [err["msg"] for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None

from decimal import Decimal, InvalidOperation

from pydantic import ValidationError as PydanticValidationError
from ninja import Form, Router

from .api_accounts import get_user_account
from .auth_utils import get_authenticated_user
from .models import Account
from .schemas import AccountIn, AccountUpdate
from .ui_utils import TRANSACTIONS_SECTION, render_section_response

router = Router(tags=["accounts-ui"])

SECTION_TEMPLATE = "partials/accounts_section.html"


def _validate_account_create(
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


def _validate_account_edit(
    name: str,
    currency: str,
) -> tuple[AccountUpdate | None, str | None]:
    try:
        payload = AccountUpdate(name=name, currency=currency)
    except PydanticValidationError as exc:
        messages = [err["msg"] for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None


@router.get("")
def accounts_section(request):
    user = get_authenticated_user(request)
    return render_section_response(request, user, SECTION_TEMPLATE)


@router.post("")
def create_account_ui(
    request,
    name: str = Form(...),
    currency: str = Form("PLN"),
    balance: str = Form("0.00"),
):
    user = get_authenticated_user(request)
    payload, error = _validate_account_create(name, currency, balance)
    if error:
        return render_section_response(request, user, SECTION_TEMPLATE, error=error)

    Account.objects.create(user=user, **payload.model_dump())
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Konto zostało dodane.",
        refresh_summary=True,
        refresh_sections=[TRANSACTIONS_SECTION],
    )


@router.get("/{account_id}/edit")
def edit_account_form(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        extra_context={"editing_account": account},
    )


@router.post("/{account_id}/edit")
def update_account_ui(
    request,
    account_id: int,
    name: str = Form(...),
    currency: str = Form("PLN"),
):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    payload, error = _validate_account_edit(name, currency)
    if error:
        return render_section_response(
            request,
            user,
            SECTION_TEMPLATE,
            error=error,
            extra_context={"editing_account": account},
        )

    account.name = payload.name
    account.currency = payload.currency
    account.save(update_fields=["name", "currency"])
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Konto zostało zaktualizowane.",
        refresh_summary=True,
        refresh_sections=[TRANSACTIONS_SECTION],
    )


@router.delete("/{account_id}")
def delete_account_ui(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    account.delete()
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Konto zostało usunięte.",
        refresh_summary=True,
        refresh_sections=[TRANSACTIONS_SECTION],
    )

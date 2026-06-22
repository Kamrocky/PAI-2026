from decimal import Decimal, InvalidOperation

from pydantic import ValidationError as PydanticValidationError
from ninja import Form, Router

from .api_accounts import get_user_account
from .api_transactions import get_user_transaction, resolve_category
from .auth_utils import get_authenticated_user
from .schemas import TransactionIn
from .transaction_service import (
    create_transaction,
    delete_transaction,
    update_transaction,
)
from .ui_utils import render_section_response

router = Router(tags=["transactions-ui"])

SECTION_TEMPLATE = "partials/transactions_section.html"


def _parse_optional_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _validate_transaction_form(
    account_id: str,
    category_id: str,
    amount: str,
    title: str,
    description: str,
) -> tuple[TransactionIn | None, str | None]:
    parsed_account_id = _parse_optional_int(account_id)
    if parsed_account_id is None:
        return None, "Wybierz konto."

    try:
        amount_decimal = Decimal(amount)
    except InvalidOperation:
        return None, "Nieprawidłowa kwota."

    try:
        payload = TransactionIn(
            account_id=parsed_account_id,
            category_id=_parse_optional_int(category_id),
            amount=amount_decimal,
            title=title,
            description=description or "",
        )
    except PydanticValidationError as exc:
        messages = [err["msg"] for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None


def _apply_transaction_payload(user, payload: TransactionIn):
    account = get_user_account(user, payload.account_id)
    category = resolve_category(user, payload.category_id)
    data = payload.model_dump()
    return account, category, data


@router.get("")
def transactions_section(request):
    user = get_authenticated_user(request)
    return render_section_response(request, user, SECTION_TEMPLATE)


@router.post("")
def create_transaction_ui(
    request,
    account_id: str = Form(...),
    category_id: str = Form(""),
    amount: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
):
    user = get_authenticated_user(request)
    payload, error = _validate_transaction_form(
        account_id, category_id, amount, title, description
    )
    if error:
        return render_section_response(request, user, SECTION_TEMPLATE, error=error)

    account, category, data = _apply_transaction_payload(user, payload)
    create_transaction(
        account=account,
        category=category,
        amount=data["amount"],
        title=data["title"],
        description=data["description"],
    )
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Transakcja została dodana.",
        refresh_summary=True,
    )


@router.get("/{transaction_id}/edit")
def edit_transaction_form(request, transaction_id: int):
    user = get_authenticated_user(request)
    txn = get_user_transaction(user, transaction_id)
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        extra_context={"editing_transaction": txn},
    )


@router.post("/{transaction_id}/edit")
def update_transaction_ui(
    request,
    transaction_id: int,
    account_id: str = Form(...),
    category_id: str = Form(""),
    amount: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
):
    user = get_authenticated_user(request)
    txn = get_user_transaction(user, transaction_id)
    payload, error = _validate_transaction_form(
        account_id, category_id, amount, title, description
    )
    if error:
        return render_section_response(
            request,
            user,
            SECTION_TEMPLATE,
            error=error,
            extra_context={"editing_transaction": txn},
        )

    account, category, data = _apply_transaction_payload(user, payload)
    update_transaction(
        txn,
        account=account,
        category=category,
        amount=data["amount"],
        title=data["title"],
        description=data["description"],
    )
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Transakcja została zaktualizowana.",
        refresh_summary=True,
    )


@router.delete("/{transaction_id}")
def delete_transaction_ui(request, transaction_id: int):
    user = get_authenticated_user(request)
    txn = get_user_transaction(user, transaction_id)
    delete_transaction(txn)
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Transakcja została usunięta.",
        refresh_summary=True,
    )

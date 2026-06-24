from ninja import Form, Router

from .api_transactions import get_user_transaction
from .auth_utils import get_authenticated_user
from .transaction_forms import apply_transaction_payload, validate_transaction_form
from .transaction_service import (
    create_transaction,
    delete_transaction,
    update_transaction,
)
from .ui_utils import render_section_response

router = Router(tags=["transactions-ui"])

SECTION_TEMPLATE = "partials/transactions_section.html"


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
    date: str = Form(""),
):
    user = get_authenticated_user(request)
    payload, error = validate_transaction_form(
        user, account_id, category_id, amount, title, description, date
    )
    if error:
        return render_section_response(request, user, SECTION_TEMPLATE, error=error)

    account, category, data = apply_transaction_payload(user, payload)
    create_transaction(
        account=account,
        category=category,
        amount=data["amount"],
        title=data["title"],
        description=data["description"],
        date=data["date"],
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
    date: str = Form(...),
):
    user = get_authenticated_user(request)
    txn = get_user_transaction(user, transaction_id)
    payload, error = validate_transaction_form(
        user, account_id, category_id, amount, title, description, date
    )
    if error:
        return render_section_response(
            request,
            user,
            SECTION_TEMPLATE,
            error=error,
            extra_context={"editing_transaction": txn},
        )

    account, category, data = apply_transaction_payload(user, payload)
    update_transaction(
        txn,
        account=account,
        category=category,
        amount=data["amount"],
        title=data["title"],
        description=data["description"],
        date=data["date"],
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

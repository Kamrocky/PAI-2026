from ninja import Router
from ninja.errors import HttpError

from .auth_utils import get_authenticated_user
from .models import Transaction
from .queries import (
    get_user_account_or_404,
    get_user_category_or_404,
    get_user_transaction_or_404,
)
from .schemas import TransactionIn, TransactionOut, TransactionUpdate
from .transaction_forms import validate_category_amount_type
from .transaction_service import create_transaction, delete_transaction, update_transaction

router = Router(tags=["transactions"])


def resolve_category(user, category_id: int | None):
    if category_id is None:
        return None
    return get_user_category_or_404(user, category_id)


@router.get("", response=list[TransactionOut])
def list_transactions(request):
    user = get_authenticated_user(request)
    return Transaction.objects.filter(account__user=user).order_by("-date", "-id")


@router.post("", response={201: TransactionOut})
def create_transaction_endpoint(request, payload: TransactionIn):
    user = get_authenticated_user(request)
    account = get_user_account_or_404(user, payload.account_id)
    category = resolve_category(user, payload.category_id)
    data = payload.model_dump()
    category_error = validate_category_amount_type(category, data["amount"])
    if category_error:
        raise HttpError(422, category_error)
    return create_transaction(
        account=account,
        category=category,
        amount=data["amount"],
        title=data["title"],
        description=data["description"],
        date=data["date"],
    )


@router.get("/{transaction_id}", response=TransactionOut)
def get_transaction(request, transaction_id: int):
    user = get_authenticated_user(request)
    return get_user_transaction_or_404(user, transaction_id)


@router.put("/{transaction_id}", response=TransactionOut)
def update_transaction_endpoint(request, transaction_id: int, payload: TransactionIn):
    user = get_authenticated_user(request)
    txn = get_user_transaction_or_404(user, transaction_id)
    account = get_user_account_or_404(user, payload.account_id)
    category = resolve_category(user, payload.category_id)
    data = payload.model_dump()
    category_error = validate_category_amount_type(category, data["amount"])
    if category_error:
        raise HttpError(422, category_error)
    return update_transaction(
        txn,
        account=account,
        category=category,
        amount=data["amount"],
        title=data["title"],
        description=data["description"],
        date=data["date"],
    )


@router.patch("/{transaction_id}", response=TransactionOut)
def partial_update_transaction(
    request,
    transaction_id: int,
    payload: TransactionUpdate,
):
    user = get_authenticated_user(request)
    txn = get_user_transaction_or_404(user, transaction_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HttpError(400, "Brak pól do aktualizacji.")

    account = txn.account
    if "account_id" in updates:
        account = get_user_account_or_404(user, updates["account_id"])

    category = txn.category
    if "category_id" in updates:
        category = resolve_category(user, updates["category_id"])

    amount = updates.get("amount", txn.amount)
    category_error = validate_category_amount_type(category, amount)
    if category_error:
        raise HttpError(422, category_error)

    return update_transaction(
        txn,
        account=account,
        category=category,
        amount=amount,
        title=updates.get("title", txn.title),
        description=updates.get("description", txn.description),
        date=updates.get("date"),
    )


@router.delete("/{transaction_id}", response={204: None})
def delete_transaction_endpoint(request, transaction_id: int):
    user = get_authenticated_user(request)
    txn = get_user_transaction_or_404(user, transaction_id)
    delete_transaction(txn)
    return 204, None

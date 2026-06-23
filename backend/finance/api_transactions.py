from ninja import Router
from ninja.errors import HttpError

from .api_accounts import get_user_account
from .auth_utils import get_authenticated_user
from .models import Transaction
from .schemas import TransactionIn, TransactionOut, TransactionUpdate
from .transaction_service import (
    create_transaction,
    delete_transaction,
    get_user_category,
    update_transaction,
)

router = Router(tags=["transactions"])


def get_user_transaction(user, transaction_id: int) -> Transaction:
    try:
        return Transaction.objects.select_related("account", "category").get(
            pk=transaction_id,
            account__user=user,
        )
    except Transaction.DoesNotExist:
        raise HttpError(404, "Transakcja nie istnieje.")


def resolve_category(user, category_id: int | None):
    if category_id is None:
        return None
    category = get_user_category(user, category_id)
    if category is None:
        raise HttpError(404, "Kategoria nie istnieje.")
    return category


@router.get("", response=list[TransactionOut])
def list_transactions(request):
    user = get_authenticated_user(request)
    return Transaction.objects.filter(account__user=user).order_by("-date", "-id")


@router.post("", response={201: TransactionOut})
def create_transaction_endpoint(request, payload: TransactionIn):
    user = get_authenticated_user(request)
    account = get_user_account(user, payload.account_id)
    category = resolve_category(user, payload.category_id)
    data = payload.model_dump()
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
    return get_user_transaction(user, transaction_id)


@router.put("/{transaction_id}", response=TransactionOut)
def update_transaction_endpoint(request, transaction_id: int, payload: TransactionIn):
    user = get_authenticated_user(request)
    txn = get_user_transaction(user, transaction_id)
    account = get_user_account(user, payload.account_id)
    category = resolve_category(user, payload.category_id)
    data = payload.model_dump()
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
    txn = get_user_transaction(user, transaction_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HttpError(400, "Brak pól do aktualizacji.")

    account = txn.account
    if "account_id" in updates:
        account = get_user_account(user, updates["account_id"])

    category = txn.category
    if "category_id" in updates:
        category = resolve_category(user, updates["category_id"])

    return update_transaction(
        txn,
        account=account,
        category=category,
        amount=updates.get("amount", txn.amount),
        title=updates.get("title", txn.title),
        description=updates.get("description", txn.description),
        date=updates.get("date"),
    )


@router.delete("/{transaction_id}", response={204: None})
def delete_transaction_endpoint(request, transaction_id: int):
    user = get_authenticated_user(request)
    txn = get_user_transaction(user, transaction_id)
    delete_transaction(txn)
    return 204, None

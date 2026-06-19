from ninja import Router
from ninja.errors import HttpError

from .auth_utils import get_authenticated_user
from .models import Account
from .schemas import AccountIn, AccountOut, AccountUpdate

router = Router(tags=["accounts"])


def get_user_account(user, account_id: int) -> Account:
    try:
        return Account.objects.get(pk=account_id, user=user)
    except Account.DoesNotExist:
        raise HttpError(404, "Konto nie istnieje.")


@router.get("", response=list[AccountOut])
def list_accounts(request):
    user = get_authenticated_user(request)
    return Account.objects.filter(user=user).order_by("name")


@router.post("", response={201: AccountOut})
def create_account(request, payload: AccountIn):
    user = get_authenticated_user(request)
    return Account.objects.create(user=user, **payload.model_dump())


@router.get("/{account_id}", response=AccountOut)
def get_account(request, account_id: int):
    user = get_authenticated_user(request)
    return get_user_account(user, account_id)


@router.put("/{account_id}", response=AccountOut)
def update_account(request, account_id: int, payload: AccountIn):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    for field, value in payload.model_dump().items():
        setattr(account, field, value)
    account.save()
    return account


@router.patch("/{account_id}", response=AccountOut)
def partial_update_account(request, account_id: int, payload: AccountUpdate):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HttpError(400, "Brak pól do aktualizacji.")
    for field, value in updates.items():
        setattr(account, field, value)
    account.save()
    return account


@router.delete("/{account_id}", response={204: None})
def delete_account(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    account.delete()
    return 204, None

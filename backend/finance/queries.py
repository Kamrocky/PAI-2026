from django.contrib.auth.models import AbstractBaseUser
from ninja.errors import HttpError

from .models import Account, Category, Transaction


def get_user_accounts(user: AbstractBaseUser) -> list[Account]:
    return list(Account.objects.filter(user=user).order_by("id"))


def get_user_account(user: AbstractBaseUser, account_id: int) -> Account | None:
    return Account.objects.filter(user=user, pk=account_id).first()


def get_user_account_or_404(user: AbstractBaseUser, account_id: int) -> Account:
    account = get_user_account(user, account_id)
    if account is None:
        raise HttpError(404, "Konto nie istnieje.")
    return account


def get_user_category(user: AbstractBaseUser, category_id: int | None) -> Category | None:
    if category_id is None:
        return None
    return Category.objects.filter(user=user, pk=category_id).first()


def get_user_category_or_404(user: AbstractBaseUser, category_id: int) -> Category:
    category = get_user_category(user, category_id)
    if category is None:
        raise HttpError(404, "Kategoria nie istnieje.")
    return category


def get_user_transaction(user: AbstractBaseUser, transaction_id: int) -> Transaction | None:
    return (
        Transaction.objects.select_related("account", "category")
        .filter(pk=transaction_id, account__user=user)
        .first()
    )


def get_user_transaction_or_404(user: AbstractBaseUser, transaction_id: int) -> Transaction:
    txn = get_user_transaction(user, transaction_id)
    if txn is None:
        raise HttpError(404, "Transakcja nie istnieje.")
    return txn

from datetime import datetime
from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import F
from django.utils import timezone

from .models import Account, Category, Transaction


def adjust_account_balance(account_id: int, delta: Decimal) -> None:
    Account.objects.filter(pk=account_id).update(balance=F("balance") + delta)


def get_user_category(user, category_id: int | None) -> Category | None:
    if category_id is None:
        return None
    try:
        return Category.objects.get(pk=category_id, user=user)
    except Category.DoesNotExist:
        return None


@db_transaction.atomic
def create_transaction(
    *,
    account: Account,
    category: Category | None,
    amount: Decimal,
    title: str,
    description: str,
    date: datetime | None = None,
) -> Transaction:
    txn = Transaction.objects.create(
        account=account,
        category=category,
        amount=amount,
        title=title,
        description=description,
        date=date or timezone.now(),
    )
    adjust_account_balance(account.pk, amount)
    return txn


@db_transaction.atomic
def update_transaction(
    txn: Transaction,
    *,
    account: Account,
    category: Category | None,
    amount: Decimal,
    title: str,
    description: str,
    date: datetime | None = None,
) -> Transaction:
    old_account_id = txn.account_id
    old_amount = txn.amount

    txn.account = account
    txn.category = category
    txn.amount = amount
    txn.title = title
    txn.description = description
    if date is not None:
        txn.date = date
    txn.save()

    if old_account_id == account.pk:
        adjust_account_balance(account.pk, amount - old_amount)
    else:
        adjust_account_balance(old_account_id, -old_amount)
        adjust_account_balance(account.pk, amount)

    return txn


@db_transaction.atomic
def delete_transaction(txn: Transaction) -> None:
    adjust_account_balance(txn.account_id, -txn.amount)
    txn.delete()

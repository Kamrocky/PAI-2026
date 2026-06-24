from django.contrib.auth.models import User

from .models import Account, Category


def clear_user_finance_data(user: User) -> None:
    Account.objects.filter(user=user).delete()
    Category.objects.filter(user=user).delete()


def delete_user_account(user: User) -> None:
    user.delete()

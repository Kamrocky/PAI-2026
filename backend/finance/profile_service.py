from django.contrib.auth.models import User

from .auth_utils import get_display_name
from .models import Account, Category


def get_profile_context(
    user: User,
    *,
    error: str | None = None,
    success: str | None = None,
) -> dict:
    context = {"user": user, "display_name": get_display_name(user)}
    if error:
        context["error"] = error
    if success:
        context["success"] = success
    return context


def clear_user_finance_data(user: User) -> None:
    Account.objects.filter(user=user).delete()
    Category.objects.filter(user=user).delete()


def delete_user_account(user: User) -> None:
    user.delete()

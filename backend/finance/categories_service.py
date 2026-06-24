from django.contrib.auth.models import AbstractBaseUser

from .constants import CATEGORY_COLOR_PALETTE
from .models import Category


def get_categories_context(user: AbstractBaseUser) -> dict:
    categories = list(Category.objects.filter(user_id=user.pk).order_by("name"))
    return {
        "expense_categories": [category for category in categories if not category.is_income],
        "income_categories": [category for category in categories if category.is_income],
        "category_color_palette": CATEGORY_COLOR_PALETTE,
    }

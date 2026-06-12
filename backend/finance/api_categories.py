from ninja import Router
from ninja.errors import HttpError

from .auth_utils import get_authenticated_user
from .models import Category
from .schemas import CategoryIn, CategoryOut, CategoryUpdate

router = Router(tags=["categories"])


def get_user_category(user, category_id: int) -> Category:
    try:
        return Category.objects.get(pk=category_id, user=user)
    except Category.DoesNotExist:
        raise HttpError(404, "Kategoria nie istnieje.")


@router.get("", response=list[CategoryOut])
def list_categories(request):
    user = get_authenticated_user(request)
    return Category.objects.filter(user=user).order_by("name")


@router.post("", response={201: CategoryOut})
def create_category(request, payload: CategoryIn):
    user = get_authenticated_user(request)
    return Category.objects.create(user=user, **payload.model_dump())


@router.get("/{category_id}", response=CategoryOut)
def get_category(request, category_id: int):
    user = get_authenticated_user(request)
    return get_user_category(user, category_id)


@router.put("/{category_id}", response=CategoryOut)
def update_category(request, category_id: int, payload: CategoryIn):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    for field, value in payload.model_dump().items():
        setattr(category, field, value)
    category.save()
    return category


@router.patch("/{category_id}", response=CategoryOut)
def partial_update_category(request, category_id: int, payload: CategoryUpdate):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HttpError(400, "Brak pól do aktualizacji.")
    for field, value in updates.items():
        setattr(category, field, value)
    category.save()
    return category


@router.delete("/{category_id}", response={204: None})
def delete_category(request, category_id: int):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    category.delete()
    return 204, None

from pydantic import ValidationError as PydanticValidationError
from ninja import Form, Router

from .api_categories import get_user_category
from .auth_utils import get_authenticated_user
from .constants import DEFAULT_CATEGORY_COLOR
from .models import Category
from .schemas import CategoryIn
from .ui_utils import TRANSACTIONS_SECTION, render_section_response

router = Router(tags=["categories-ui"])

SECTION_TEMPLATE = "partials/categories_section.html"


def _parse_is_income(value: str) -> bool:
    return value.lower() in ("true", "on", "1")


def _validate_category_form(
    name: str,
    color: str,
    is_income: str,
) -> tuple[CategoryIn | None, str | None]:
    try:
        payload = CategoryIn(
            name=name,
            color=color or DEFAULT_CATEGORY_COLOR,
            is_income=_parse_is_income(is_income),
        )
    except PydanticValidationError as exc:
        messages = [err["msg"] for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None


@router.get("")
def categories_section(request):
    user = get_authenticated_user(request)
    return render_section_response(request, user, SECTION_TEMPLATE)


@router.post("")
def create_category_ui(
    request,
    name: str = Form(...),
    color: str = Form(DEFAULT_CATEGORY_COLOR),
    is_income: str = Form(""),
):
    user = get_authenticated_user(request)
    payload, error = _validate_category_form(name, color, is_income)
    if error:
        return render_section_response(request, user, SECTION_TEMPLATE, error=error)

    Category.objects.create(user=user, **payload.model_dump())
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Kategoria została dodana.",
        refresh_summary=True,
    )


@router.get("/{category_id}/edit")
def edit_category_form(request, category_id: int):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        extra_context={"editing_category": category},
    )


@router.post("/{category_id}/edit")
def update_category_ui(
    request,
    category_id: int,
    name: str = Form(...),
    color: str = Form(DEFAULT_CATEGORY_COLOR),
    is_income: str = Form(""),
):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    payload, error = _validate_category_form(name, color, is_income)
    if error:
        return render_section_response(
            request,
            user,
            SECTION_TEMPLATE,
            error=error,
            extra_context={"editing_category": category},
        )

    for field, value in payload.model_dump().items():
        setattr(category, field, value)
    category.save()
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Kategoria została zaktualizowana.",
        refresh_summary=True,
        refresh_sections=[TRANSACTIONS_SECTION],
    )


@router.delete("/{category_id}")
def delete_category_ui(request, category_id: int):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    category.delete()
    return render_section_response(
        request,
        user,
        SECTION_TEMPLATE,
        success="Kategoria została usunięta.",
        refresh_summary=True,
        refresh_sections=[TRANSACTIONS_SECTION],
    )

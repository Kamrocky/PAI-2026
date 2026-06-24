from django.http import HttpResponse
from django.template.loader import render_to_string
from ninja import Form, Router

from .api_categories import get_user_category
from .auth_utils import get_authenticated_user
from .categories_service import get_categories_context
from .category_forms import validate_category_form
from .constants import DEFAULT_CATEGORY_COLOR
from .models import Category
from .ui_utils import inject_oob_outer_swap

router = Router(tags=["categories-ui"])

MODAL_CLOSE_HTML = '<div id="home-modal" hx-swap-oob="innerHTML"></div>'


def render_categories_content(
    request,
    user,
    *,
    success: str | None = None,
    error: str | None = None,
) -> str:
    context = get_categories_context(user)
    if success:
        context["success"] = success
    if error:
        context["error"] = error
    return render_to_string(
        "partials/categories/categories_content.html",
        context,
        request=request,
    )


def render_categories_modal(
    request,
    user,
    template_name: str,
    *,
    error: str | None = None,
    extra_context: dict | None = None,
) -> str:
    context = {**get_categories_context(user), **(extra_context or {})}
    if error:
        context["error"] = error
    return render_to_string(template_name, context, request=request)


def render_categories_refresh_response(
    request,
    user,
    *,
    success: str | None = None,
    error: str | None = None,
) -> HttpResponse:
    parts = [
        MODAL_CLOSE_HTML,
        inject_oob_outer_swap(
            render_categories_content(request, user, success=success, error=error),
            "categories-content",
        ),
    ]
    return HttpResponse("".join(parts))


@router.get("")
def categories_content(request):
    user = get_authenticated_user(request)
    return HttpResponse(render_categories_content(request, user))


@router.get("/create")
def create_category_modal(request):
    user = get_authenticated_user(request)
    return HttpResponse(
        render_categories_modal(request, user, "partials/categories/category_create_modal.html")
    )


@router.post("")
def create_category_ui(
    request,
    name: str = Form(...),
    color: str = Form(DEFAULT_CATEGORY_COLOR),
    is_income: str = Form(""),
):
    user = get_authenticated_user(request)
    payload, error = validate_category_form(name, color, is_income)
    if error:
        return HttpResponse(
            render_categories_modal(
                request,
                user,
                "partials/categories/category_create_modal.html",
                error=error,
            )
        )

    Category.objects.create(user=user, **payload.model_dump())
    return render_categories_refresh_response(request, user, success="Kategoria została dodana.")


@router.get("/{category_id}/delete-confirm")
def delete_category_confirm_modal(request, category_id: int):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    return HttpResponse(
        render_categories_modal(
            request,
            user,
            "partials/categories/category_delete_confirm_modal.html",
            extra_context={"editing_category": category},
        )
    )


@router.get("/{category_id}/edit")
def edit_category_modal(request, category_id: int):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    return HttpResponse(
        render_categories_modal(
            request,
            user,
            "partials/categories/category_form_modal.html",
            extra_context={"editing_category": category},
        )
    )


@router.post("/{category_id}/edit")
def update_category_ui(
    request,
    category_id: int,
    name: str = Form(...),
    color: str = Form(DEFAULT_CATEGORY_COLOR),
):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    payload, error = validate_category_form(name, color, "true" if category.is_income else "")
    if error:
        return HttpResponse(
            render_categories_modal(
                request,
                user,
                "partials/categories/category_form_modal.html",
                error=error,
                extra_context={"editing_category": category},
            )
        )

    category.name = payload.name
    category.color = payload.color
    category.save(update_fields=["name", "color"])
    return render_categories_refresh_response(request, user, success="Kategoria została zaktualizowana.")


@router.delete("/{category_id}")
def delete_category_ui(request, category_id: int):
    user = get_authenticated_user(request)
    category = get_user_category(user, category_id)
    category.delete()
    return render_categories_refresh_response(request, user, success="Kategoria została usunięta.")

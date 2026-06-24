from django.http import HttpResponse
from django.template.loader import render_to_string
from ninja import Form, Router

from .account_forms import validate_account_create, validate_account_edit
from .api_accounts import get_user_account
from .auth_utils import get_authenticated_user
from .home_service import (
    HOME_ACCOUNT_SESSION_KEY,
    get_active_account,
    get_home_context,
    go_to_carousel_slot,
    navigate_home_slot,
    set_active_account_id,
)
from .models import Account
from .ui_utils import inject_oob_outer_swap

router = Router(tags=["home-ui"])

MODAL_CLOSE_HTML = '<div id="home-modal" hx-swap-oob="innerHTML"></div>'


def render_home_content(request, user) -> str:
    return render_to_string(
        "partials/home/home_content.html",
        get_home_context(user, request),
        request=request,
    )


def render_home_modal(
    request,
    user,
    template_name: str,
    *,
    error: str | None = None,
    extra_context: dict | None = None,
) -> str:
    context = {**get_home_context(user, request), **(extra_context or {})}
    if error:
        context["error"] = error
    return render_to_string(template_name, context, request=request)


def render_home_refresh_response(request, user) -> HttpResponse:
    parts = [
        MODAL_CLOSE_HTML,
        inject_oob_outer_swap(render_home_content(request, user), "home-content"),
    ]
    return HttpResponse("".join(parts))


def clear_active_account_if_matches(request, account_id: int) -> None:
    if request.session.get(HOME_ACCOUNT_SESSION_KEY) == account_id:
        del request.session[HOME_ACCOUNT_SESSION_KEY]


@router.get("/modal/close")
def close_modal(request):
    get_authenticated_user(request)
    return HttpResponse("")


@router.post("/navigate-account")
def navigate_account(request, direction: str = Form(...)):
    user = get_authenticated_user(request)
    if direction not in {"prev", "next"}:
        return HttpResponse("Nieprawidłowy kierunek.", status=400)

    navigate_home_slot(request, user, direction)
    return HttpResponse(render_home_content(request, user))


@router.post("/select-slot")
def select_slot(request, slot_index: int = Form(...)):
    user = get_authenticated_user(request)
    go_to_carousel_slot(request, user, slot_index)
    return HttpResponse(render_home_content(request, user))


@router.post("/select-account")
def select_account(request, account_id: int = Form(...)):
    user = get_authenticated_user(request)
    account = get_active_account(user, account_id)
    if account is None:
        return HttpResponse("Konto nie istnieje.", status=404)

    set_active_account_id(request, account_id)
    return HttpResponse(render_home_content(request, user))


@router.get("/accounts/create")
def create_account_modal(request):
    user = get_authenticated_user(request)
    return HttpResponse(
        render_home_modal(request, user, "partials/home/account_create_modal.html")
    )


@router.post("/accounts")
def create_account_ui(
    request,
    name: str = Form(...),
    currency: str = Form("PLN"),
    balance: str = Form("0.00"),
):
    user = get_authenticated_user(request)
    payload, error = validate_account_create(name, currency, balance)
    if error:
        return HttpResponse(
            render_home_modal(
                request,
                user,
                "partials/home/account_create_modal.html",
                error=error,
            )
        )

    account = Account.objects.create(user=user, **payload.model_dump())
    set_active_account_id(request, account.pk)
    return render_home_refresh_response(request, user)


@router.get("/accounts/{account_id}/delete-confirm")
def delete_account_confirm_modal(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    return HttpResponse(
        render_home_modal(
            request,
            user,
            "partials/home/account_delete_confirm_modal.html",
            extra_context={"editing_account": account},
        )
    )


@router.get("/accounts/{account_id}/edit")
def edit_account_modal(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    return HttpResponse(
        render_home_modal(
            request,
            user,
            "partials/home/account_form_modal.html",
            extra_context={"editing_account": account},
        )
    )


@router.post("/accounts/{account_id}/edit")
def update_account_ui(
    request,
    account_id: int,
    name: str = Form(...),
):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    payload, error = validate_account_edit(name)
    if error:
        return HttpResponse(
            render_home_modal(
                request,
                user,
                "partials/home/account_form_modal.html",
                error=error,
                extra_context={"editing_account": account},
            )
        )

    account.name = payload.name
    account.save(update_fields=["name"])
    return render_home_refresh_response(request, user)


@router.delete("/accounts/{account_id}")
def delete_account_ui(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    clear_active_account_if_matches(request, account_id)
    account.delete()
    return render_home_refresh_response(request, user)

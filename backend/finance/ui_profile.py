from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.loader import render_to_string
from ninja import Form, Router

from .auth_utils import get_authenticated_user, get_display_name, render_logout_success
from .profile_service import clear_user_finance_data, delete_user_account

router = Router(tags=["profile-ui"])

SECTION_TEMPLATE = "partials/profile_section.html"
NAV_GREETING_TEMPLATE = "partials/nav_greeting.html"
MODAL_CLOSE_HTML = '<div id="home-modal" hx-swap-oob="innerHTML"></div>'


def _profile_context(user, *, error: str | None = None, success: str | None = None) -> dict:
    context = {"user": user, "display_name": get_display_name(user)}
    if error:
        context["error"] = error
    if success:
        context["success"] = success
    return context


def _render_profile_section(request, user, *, error=None, success=None, refresh_nav=False):
    context = _profile_context(user, error=error, success=success)
    section_html = render_to_string(SECTION_TEMPLATE, context, request=request)
    if refresh_nav:
        nav_html = render_to_string(NAV_GREETING_TEMPLATE, context, request=request)
        nav_oob = nav_html.replace(
            'id="nav-user-greeting"',
            'id="nav-user-greeting" hx-swap-oob="outerHTML"',
            1,
        )
        return HttpResponse(nav_oob + section_html)
    return HttpResponse(section_html)


@router.get("")
def profile_section(request):
    user = get_authenticated_user(request)
    return _render_profile_section(request, user)


@router.post("/name")
def update_name(request, first_name: str = Form(...)):
    user = get_authenticated_user(request)
    first_name = first_name.strip()
    if not first_name:
        return _render_profile_section(request, user, error="Imię nie może być puste.")
    User.objects.filter(pk=user.pk).update(first_name=first_name)
    user.first_name = first_name
    return _render_profile_section(request, user, success="Imię zostało zaktualizowane.", refresh_nav=True)


@router.post("/password")
def update_password(
    request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    user = get_authenticated_user(request)
    if not user.check_password(current_password):
        return _render_profile_section(request, user, error="Aktualne hasło jest nieprawidłowe.")
    if new_password != confirm_password:
        return _render_profile_section(request, user, error="Nowe hasła nie są identyczne.")
    if len(new_password) < 8:
        return _render_profile_section(request, user, error="Hasło musi mieć co najmniej 8 znaków.")
    user.set_password(new_password)
    user.save()
    return _render_profile_section(request, user, success="Hasło zostało zmienione.")


@router.get("/clear-data/confirm")
def clear_data_confirm(request):
    get_authenticated_user(request)
    modal_html = render_to_string(
        "partials/profile/clear_data_confirm_modal.html",
        {},
        request=request,
    )
    return HttpResponse(modal_html)


@router.post("/clear-data")
def clear_data(request):
    user = get_authenticated_user(request)
    clear_user_finance_data(user)
    response = _render_profile_section(
        request,
        user,
        success="Wszystkie konta, transakcje i kategorie zostały usunięte.",
    )
    return HttpResponse(MODAL_CLOSE_HTML + response.content.decode())


@router.get("/delete-account/confirm")
def delete_account_confirm(request):
    user = get_authenticated_user(request)
    modal_html = render_to_string(
        "partials/profile/delete_account_confirm_modal.html",
        {"user": user},
        request=request,
    )
    return HttpResponse(modal_html)


@router.delete("/account")
def delete_account(request):
    user = get_authenticated_user(request)
    user_pk = user.pk
    logout(request)
    delete_user_account(User.objects.get(pk=user_pk))
    response = render_logout_success(request)
    response.content = (MODAL_CLOSE_HTML + response.content.decode()).encode()
    response["HX-Push-Url"] = "/"
    return response

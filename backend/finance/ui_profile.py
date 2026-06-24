from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.loader import render_to_string
from ninja import Form, Router

from .auth_utils import get_authenticated_user, get_display_name

router = Router(tags=["profile-ui"])

SECTION_TEMPLATE = "partials/profile_section.html"
NAV_GREETING_TEMPLATE = "partials/nav_greeting.html"


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


@router.post("/email")
def update_email(request, email: str = Form(...)):
    user = get_authenticated_user(request)
    email = email.strip().lower()
    if not email:
        return _render_profile_section(request, user, error="E-mail nie może być pusty.")
    if User.objects.filter(email=email).exclude(pk=user.pk).exists():
        return _render_profile_section(request, user, error="Ten adres e-mail jest już zajęty.")
    User.objects.filter(pk=user.pk).update(email=email, username=email)
    user.email = email
    return _render_profile_section(request, user, success="Adres e-mail został zaktualizowany.")


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

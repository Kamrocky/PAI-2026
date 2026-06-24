from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from ninja.errors import HttpError


from .home_service import get_home_context


def get_display_name(user) -> str:
    first_name = (getattr(user, "first_name", "") or "").strip()
    if first_name:
        return first_name

    email = (getattr(user, "email", "") or getattr(user, "username", "") or "").strip()
    if "@" in email:
        return email.split("@", 1)[0]
    return email or "Użytkowniku"


def render_user_info(request, *, logged_in: bool) -> str:
    template = (
        "partials/user_info_logged_in.html"
        if logged_in
        else "partials/user_info_logged_out.html"
    )
    return render_to_string(
        template,
        {"user": request.user, "display_name": get_display_name(request.user)},
        request=request,
    )


def render_auth_step(
    request,
    *,
    step: str,
    email: str | None = None,
    error: str | None = None,
) -> HttpResponse:
    body = render_to_string(
        "partials/auth_forms.html",
        {
            "error": error,
            "email": email or "",
            "auth_step": step,
        },
        request=request,
    )
    return HttpResponse(body)


def render_auth_success(request, user) -> HttpResponse:
    content_html = render_to_string(
        "partials/home_panel.html",
        get_home_context(user, request),
        request=request,
    )
    user_info_html = render_user_info(request, logged_in=True)
    response = HttpResponse(f"{user_info_html}{content_html}")
    response["HX-Push-Url"] = "/"
    return response


def render_logout_success(request) -> HttpResponse:
    auth_html = render_to_string(
        "partials/auth_forms.html",
        {"error": None, "email": "", "auth_step": "email"},
        request=request,
    )
    user_info_html = render_user_info(request, logged_in=False)
    return HttpResponse(f"{user_info_html}{auth_html}")


def format_validation_error(exc: ValidationError) -> str:
    if hasattr(exc, "message_dict"):
        parts = []
        for field, messages in exc.message_dict.items():
            for message in messages:
                parts.append(f"{field}: {message}")
        return " ".join(parts)
    return "; ".join(exc.messages)


def require_authenticated_user(
    request: HttpRequest,
) -> AbstractBaseUser | HttpResponse:
    user = request.user
    if not user.is_authenticated or isinstance(user, AnonymousUser):
        return HttpResponse("Wymagane logowanie.", status=401)
    return user


def get_authenticated_user(request: HttpRequest) -> AbstractBaseUser:
    user = require_authenticated_user(request)
    if isinstance(user, HttpResponse):
        raise HttpError(401, "Wymagane logowanie.")
    return user

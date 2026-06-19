from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from ninja.errors import HttpError

from .models import Account, Transaction


def get_dashboard_context(user):
    return {
        "username": user.username,
        "accounts": Account.objects.filter(user=user),
        "transactions": Transaction.objects.filter(account__user=user),
    }


def render_user_info(request, *, logged_in: bool) -> str:
    template = (
        "partials/user_info_logged_in.html"
        if logged_in
        else "partials/user_info_logged_out.html"
    )
    return render_to_string(template, {"user": request.user}, request=request)


def render_auth_page(request, error: str | None = None) -> HttpResponse:
    body = render_to_string(
        "partials/auth_forms.html",
        {"error": error},
        request=request,
    )
    return HttpResponse(body)


def render_auth_success(request, user) -> HttpResponse:
    dashboard_html = render_to_string(
        "dashboard_partial.html",
        get_dashboard_context(user),
        request=request,
    )
    user_info_html = render_user_info(request, logged_in=True)
    return HttpResponse(f"{user_info_html}{dashboard_html}")


def render_logout_success(request) -> HttpResponse:
    auth_html = render_to_string(
        "partials/auth_forms.html",
        {"error": None},
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

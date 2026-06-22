from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string

from .models import Account, Category, Transaction

RECENT_TRANSACTIONS_LIMIT = 20


def get_ui_context(user: AbstractBaseUser) -> dict:
    return {
        "username": user.username,
        "accounts": Account.objects.filter(user=user).order_by("name"),
        "categories": Category.objects.filter(user=user).order_by("name"),
        "transactions": (
            Transaction.objects.filter(account__user=user)
            .select_related("account", "category")
            .order_by("-date", "-id")[:RECENT_TRANSACTIONS_LIMIT]
        ),
    }


def render_dashboard_summary(
    request: HttpRequest,
    user: AbstractBaseUser,
    *,
    oob: bool = False,
) -> str:
    inner = render_to_string(
        "partials/dashboard_summary.html",
        get_ui_context(user),
        request=request,
    )
    if oob:
        return f'<div id="dashboard-summary" hx-swap-oob="innerHTML">{inner}</div>'
    return inner


def render_dashboard(
    request: HttpRequest,
    user: AbstractBaseUser,
    *,
    error: str | None = None,
) -> HttpResponse:
    context = get_ui_context(user)
    if error:
        context["error"] = error
    body = render_to_string("dashboard_partial.html", context, request=request)
    return HttpResponse(body)


def render_section(
    request: HttpRequest,
    user: AbstractBaseUser,
    template_name: str,
    *,
    error: str | None = None,
    extra_context: dict | None = None,
) -> str:
    context = {**get_ui_context(user), **(extra_context or {})}
    if error:
        context["error"] = error
    return render_to_string(template_name, context, request=request)


def render_section_response(
    request: HttpRequest,
    user: AbstractBaseUser,
    template_name: str,
    *,
    error: str | None = None,
    extra_context: dict | None = None,
    refresh_summary: bool = False,
) -> HttpResponse:
    section_html = render_section(
        request,
        user,
        template_name,
        error=error,
        extra_context=extra_context,
    )
    if refresh_summary:
        summary_oob = render_dashboard_summary(request, user, oob=True)
        return HttpResponse(f"{summary_oob}{section_html}")
    return HttpResponse(section_html)

from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string

from .constants import ALLOWED_CURRENCIES, CATEGORY_COLOR_PALETTE
from .models import Account, Category, Transaction

RECENT_TRANSACTIONS_LIMIT = 20

SECTION_TEMPLATE_IDS = {
    "partials/categories_section.html": "categories-section",
    "partials/accounts_section.html": "accounts-section",
    "partials/transactions_section.html": "transactions-section",
}

TRANSACTIONS_SECTION = "partials/transactions_section.html"


def get_ui_context(user: AbstractBaseUser) -> dict:
    accounts = list(Account.objects.filter(user=user).order_by("name"))
    categories = list(Category.objects.filter(user=user).order_by("name"))
    transactions = list(
        Transaction.objects.filter(account__user=user)
        .select_related("account", "category")
        .order_by("-date", "-id")[:RECENT_TRANSACTIONS_LIMIT]
    )

    totals_by_currency: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for account in accounts:
        totals_by_currency[account.currency] += account.balance

    from .auth_utils import get_display_name

    return {
        "display_name": get_display_name(user),
        "accounts": accounts,
        "categories": categories,
        "transactions": transactions,
        "totals_by_currency": dict(totals_by_currency),
        "allowed_currencies": ALLOWED_CURRENCIES,
        "category_color_palette": CATEGORY_COLOR_PALETTE,
    }


def inject_oob_outer_swap(html: str, element_id: str) -> str:
    needle = f'id="{element_id}"'
    replacement = f'id="{element_id}" hx-swap-oob="outerHTML"'
    if needle not in html:
        return html
    return html.replace(needle, replacement, 1)


def _inject_oob_swap(html: str, element_id: str) -> str:
    return inject_oob_outer_swap(html, element_id)


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
    success: str | None = None,
    extra_context: dict | None = None,
) -> str:
    context = {**get_ui_context(user), **(extra_context or {})}
    if error:
        context["error"] = error
    if success:
        context["success"] = success
    return render_to_string(template_name, context, request=request)


def render_section_response(
    request: HttpRequest,
    user: AbstractBaseUser,
    template_name: str,
    *,
    error: str | None = None,
    success: str | None = None,
    extra_context: dict | None = None,
    refresh_summary: bool = False,
    refresh_sections: list[str] | None = None,
) -> HttpResponse:
    parts: list[str] = []

    if refresh_summary:
        parts.append(render_dashboard_summary(request, user, oob=True))

    for section_template in refresh_sections or []:
        if section_template == template_name:
            continue
        section_html = render_section(request, user, section_template)
        element_id = SECTION_TEMPLATE_IDS.get(section_template)
        if element_id:
            parts.append(_inject_oob_swap(section_html, element_id))

    parts.append(
        render_section(
            request,
            user,
            template_name,
            error=error,
            success=success,
            extra_context=extra_context,
        )
    )
    return HttpResponse("".join(parts))

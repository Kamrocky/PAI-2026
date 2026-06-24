from django.shortcuts import render

from .auth_utils import get_display_name
from .home_service import get_home_context

AUTH_SHELL_TEMPLATE = "auth.html"
VIEW_TEMPLATES = {
    "home": "home.html",
    "categories": "categories.html",
    "stats": "stats.html",
}


def _authenticated_context(request):
    return {"display_name": get_display_name(request.user)}


def _render_auth_shell(request):
    return render(request, AUTH_SHELL_TEMPLATE, {})


def _render_authenticated_view(request, view_name: str):
    if not request.user.is_authenticated:
        return _render_auth_shell(request)

    if view_name == "home":
        return render(request, "home.html", get_home_context(request.user, request))

    return render(
        request,
        VIEW_TEMPLATES[view_name],
        _authenticated_context(request),
    )


def home(request):
    return _render_authenticated_view(request, "home")


def categories(request):
    return _render_authenticated_view(request, "categories")


def stats(request):
    return _render_authenticated_view(request, "stats")

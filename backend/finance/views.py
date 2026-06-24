from django.shortcuts import render

from .auth_utils import get_display_name
from .home_service import get_home_context

AUTH_SHELL_TEMPLATE = "auth.html"
VIEW_TEMPLATES = {
    "home": "home.html",
    "categories": "categories.html",
    "stats": "stats.html",
    "profile": "profile.html",
}


def _authenticated_context(request):
    return {"display_name": get_display_name(request.user)}


def _render_auth_shell(request):
    return render(request, AUTH_SHELL_TEMPLATE, {})


def _render_authenticated_view(request, view_name: str, extra_context: dict | None = None):
    if not request.user.is_authenticated:
        return _render_auth_shell(request)

def _render_authenticated_view(request, view_name: str, extra_context: dict | None = None):
    if not request.user.is_authenticated:
        return _render_auth_shell(request)

    if view_name == "home":
        return render(request, "home.html", get_home_context(request.user, request))

    ctx = {**_authenticated_context(request), **(extra_context or {})}
    return render(request, VIEW_TEMPLATES[view_name], ctx)


def home(request):
    return _render_authenticated_view(request, "home")


def categories(request):
    return _render_authenticated_view(request, "categories")


def stats(request):
    return _render_authenticated_view(request, "stats")


def profile(request):
    back_url = request.META.get("HTTP_REFERER", "/")
    return _render_authenticated_view(request, "profile", extra_context={"back_url": back_url})

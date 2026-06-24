from django.shortcuts import render

from .auth_utils import get_display_name


def _authenticated_context(request):
    return {"display_name": get_display_name(request.user)}


def _render_auth_shell(request):
    return render(request, "index.html", {})


def home(request):
    if not request.user.is_authenticated:
        return _render_auth_shell(request)

    return render(request, "home.html", _authenticated_context(request))


def categories(request):
    if not request.user.is_authenticated:
        return _render_auth_shell(request)

    return render(request, "categories.html", _authenticated_context(request))


def stats(request):
    if not request.user.is_authenticated:
        return _render_auth_shell(request)

    return render(request, "stats.html", _authenticated_context(request))

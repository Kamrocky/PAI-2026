from django.shortcuts import render

from .auth_utils import get_dashboard_context, get_display_name


def home(request):
    context = {}
    if request.user.is_authenticated:
        context["dashboard_context"] = get_dashboard_context(request.user)
        context["display_name"] = get_display_name(request.user)
    return render(request, "index.html", context)

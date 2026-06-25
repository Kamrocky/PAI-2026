from django.http import HttpResponse
from django.template.loader import render_to_string
from ninja import Form, Router

from .auth_utils import get_authenticated_user
from .stats_service import (
    get_stats_context,
    navigate_stats_account,
    select_stats_slot,
    set_stats_period,
)

router = Router(tags=["stats-ui"])

CONTENT_TEMPLATE = "partials/stats/stats_content.html"


def _render_stats_content(request, user) -> HttpResponse:
    context = get_stats_context(request, user)
    return HttpResponse(render_to_string(CONTENT_TEMPLATE, context, request=request))


@router.get("")
def stats_content(request):
    user = get_authenticated_user(request)
    return _render_stats_content(request, user)


@router.post("/navigate-account")
def navigate_account(request, direction: str = Form(...)):
    user = get_authenticated_user(request)
    if direction in {"prev", "next"}:
        navigate_stats_account(request, user, direction)
    return _render_stats_content(request, user)


@router.post("/select-slot")
def select_slot(request, slot_index: int = Form(...)):
    user = get_authenticated_user(request)
    select_stats_slot(request, user, slot_index)
    return _render_stats_content(request, user)


@router.post("/period")
def select_period(request, period: str = Form(...)):
    user = get_authenticated_user(request)
    set_stats_period(request, period)
    return _render_stats_content(request, user)

from django.http import HttpResponse
from django.template.loader import render_to_string
from ninja import Form, Router

from .account_forms import validate_account_create, validate_account_edit
from .api_accounts import get_user_account
from .api_transactions import get_user_transaction
from .auth_utils import get_authenticated_user
from .home_service import (
    HOME_ACCOUNT_SESSION_KEY,
    get_home_context,
    go_to_carousel_slot,
    navigate_home_slot,
    resolve_active_account,
    set_active_account_id,
    set_transactions_expanded,
)
from .models import Account
from .transaction_forms import apply_transaction_payload, validate_transaction_form
from .transaction_service import create_transaction, delete_transaction, update_transaction
from .ui_utils import inject_oob_outer_swap

router = Router(tags=["home-ui"])

MODAL_CLOSE_HTML = '<div id="home-modal" hx-swap-oob="innerHTML"></div>'


def render_home_content(request, user) -> str:
    return render_to_string(
        "partials/home/home_content.html",
        get_home_context(user, request),
        request=request,
    )


def render_home_modal(
    request,
    user,
    template_name: str,
    *,
    error: str | None = None,
    extra_context: dict | None = None,
) -> str:
    context = {**get_home_context(user, request), **(extra_context or {})}
    if error:
        context["error"] = error
    return render_to_string(template_name, context, request=request)


def render_home_refresh_response(request, user) -> HttpResponse:
    parts = [
        MODAL_CLOSE_HTML,
        inject_oob_outer_swap(render_home_content(request, user), "home-content"),
    ]
    return HttpResponse("".join(parts))


def render_home_transactions(
    request,
    user,
    *,
    error: str | None = None,
    extra_context: dict | None = None,
) -> str:
    context = {**get_home_context(user, request), **(extra_context or {})}
    if error:
        context["error"] = error
    return render_to_string(
        "partials/home/home_transactions.html",
        context,
        request=request,
    )


def _get_active_account_or_404(request, user) -> Account | HttpResponse:
    account = resolve_active_account(request, user)
    if account is None:
        return HttpResponse("Brak aktywnego konta.", status=404)
    return account


def clear_active_account_if_matches(request, account_id: int) -> None:
    if request.session.get(HOME_ACCOUNT_SESSION_KEY) == account_id:
        del request.session[HOME_ACCOUNT_SESSION_KEY]


@router.get("/modal/close")
def close_modal(request):
    get_authenticated_user(request)
    return HttpResponse("")


@router.post("/navigate-account")
def navigate_account(request, direction: str = Form(...)):
    user = get_authenticated_user(request)
    if direction not in {"prev", "next"}:
        return HttpResponse("Nieprawidłowy kierunek.", status=400)

    navigate_home_slot(request, user, direction)
    return HttpResponse(render_home_content(request, user))


@router.post("/select-slot")
def select_slot(request, slot_index: int = Form(...)):
    user = get_authenticated_user(request)
    go_to_carousel_slot(request, user, slot_index)
    return HttpResponse(render_home_content(request, user))


@router.get("/accounts/create")
def create_account_modal(request):
    user = get_authenticated_user(request)
    return HttpResponse(
        render_home_modal(request, user, "partials/home/account_create_modal.html")
    )


@router.post("/accounts")
def create_account_ui(
    request,
    name: str = Form(...),
    currency: str = Form("PLN"),
    balance: str = Form("0.00"),
):
    user = get_authenticated_user(request)
    payload, error = validate_account_create(name, currency, balance)
    if error:
        return HttpResponse(
            render_home_modal(
                request,
                user,
                "partials/home/account_create_modal.html",
                error=error,
            )
        )

    account = Account.objects.create(user=user, **payload.model_dump())
    set_active_account_id(request, account.pk)
    return render_home_refresh_response(request, user)


@router.get("/accounts/{account_id}/delete-confirm")
def delete_account_confirm_modal(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    return HttpResponse(
        render_home_modal(
            request,
            user,
            "partials/home/account_delete_confirm_modal.html",
            extra_context={"editing_account": account},
        )
    )


@router.get("/accounts/{account_id}/edit")
def edit_account_modal(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    return HttpResponse(
        render_home_modal(
            request,
            user,
            "partials/home/account_form_modal.html",
            extra_context={"editing_account": account},
        )
    )


@router.post("/accounts/{account_id}/edit")
def update_account_ui(
    request,
    account_id: int,
    name: str = Form(...),
):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    payload, error = validate_account_edit(name)
    if error:
        return HttpResponse(
            render_home_modal(
                request,
                user,
                "partials/home/account_form_modal.html",
                error=error,
                extra_context={"editing_account": account},
            )
        )

    account.name = payload.name
    account.save(update_fields=["name"])
    return render_home_refresh_response(request, user)


@router.delete("/accounts/{account_id}")
def delete_account_ui(request, account_id: int):
    user = get_authenticated_user(request)
    account = get_user_account(user, account_id)
    clear_active_account_if_matches(request, account_id)
    account.delete()
    return render_home_refresh_response(request, user)


@router.get("/transactions/create")
def create_transaction_modal(request):
    user = get_authenticated_user(request)
    account = _get_active_account_or_404(request, user)
    if isinstance(account, HttpResponse):
        return account
    return HttpResponse(
        render_home_modal(request, user, "partials/home/transaction_form_modal.html")
    )


@router.post("/transactions")
def create_transaction_ui(
    request,
    account_id: str = Form(...),
    category_id: str = Form(""),
    amount: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    date: str = Form(""),
):
    user = get_authenticated_user(request)
    account = _get_active_account_or_404(request, user)
    if isinstance(account, HttpResponse):
        return account

    payload, error = validate_transaction_form(
        user, account_id, category_id, amount, title, description, date
    )
    if error:
        return HttpResponse(
            render_home_modal(
                request,
                user,
                "partials/home/transaction_form_modal.html",
                error=error,
            )
        )

    applied_account, category, data = apply_transaction_payload(user, payload)
    if applied_account.pk != account.pk:
        return HttpResponse(
            render_home_modal(
                request,
                user,
                "partials/home/transaction_form_modal.html",
                error="Transakcja musi należeć do aktywnego konta.",
            )
        )

    create_transaction(
        account=applied_account,
        category=category,
        amount=data["amount"],
        title=data["title"],
        description=data["description"],
        date=data["date"],
    )
    return render_home_refresh_response(request, user)


@router.get("/transactions")
def transactions_list(request):
    user = get_authenticated_user(request)
    account = _get_active_account_or_404(request, user)
    if isinstance(account, HttpResponse):
        return account
    return HttpResponse(render_home_transactions(request, user))


@router.post("/transactions/expand")
def expand_transactions(request):
    user = get_authenticated_user(request)
    account = _get_active_account_or_404(request, user)
    if isinstance(account, HttpResponse):
        return account
    set_transactions_expanded(request, True)
    return HttpResponse(render_home_transactions(request, user))


@router.get("/transactions/{transaction_id}")
def transaction_detail(request, transaction_id: int):
    user = get_authenticated_user(request)
    account = _get_active_account_or_404(request, user)
    if isinstance(account, HttpResponse):
        return account
    txn = get_user_transaction(user, transaction_id)
    if txn.account_id != account.pk:
        return HttpResponse("Transakcja nie należy do aktywnego konta.", status=404)
    return HttpResponse(
        render_home_modal(
            request,
            user,
            "partials/home/transaction_detail_modal.html",
            extra_context={"viewing_transaction": txn},
        )
    )


@router.get("/transactions/{transaction_id}/edit")
def edit_transaction_modal(request, transaction_id: int):
    user = get_authenticated_user(request)
    account = _get_active_account_or_404(request, user)
    if isinstance(account, HttpResponse):
        return account
    txn = get_user_transaction(user, transaction_id)
    if txn.account_id != account.pk:
        return HttpResponse("Transakcja nie należy do aktywnego konta.", status=404)
    return HttpResponse(
        render_home_modal(
            request,
            user,
            "partials/home/transaction_form_modal.html",
            extra_context={"editing_transaction": txn},
        )
    )


@router.get("/transactions/{transaction_id}/delete-confirm")
def delete_transaction_confirm_modal(request, transaction_id: int, back: str = ""):
    user = get_authenticated_user(request)
    account = resolve_active_account(request, user)
    txn = get_user_transaction(user, transaction_id)
    if account is None or txn.account_id != account.pk:
        return HttpResponse("Transakcja nie istnieje.", status=404)
    return HttpResponse(
        render_home_modal(
            request,
            user,
            "partials/home/transaction_delete_confirm_modal.html",
            extra_context={
                "transaction": txn,
                "delete_cancel_returns_to_edit": back == "edit",
            },
        )
    )


@router.post("/transactions/{transaction_id}/edit")
def update_transaction_ui(
    request,
    transaction_id: int,
    account_id: str = Form(...),
    category_id: str = Form(""),
    amount: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    date: str = Form(...),
):
    user = get_authenticated_user(request)
    account = resolve_active_account(request, user)
    txn = get_user_transaction(user, transaction_id)
    if account is None or txn.account_id != account.pk:
        return HttpResponse("Transakcja nie istnieje.", status=404)

    payload, error = validate_transaction_form(
        user, account_id, category_id, amount, title, description, date
    )
    if error:
        return HttpResponse(
            render_home_modal(
                request,
                user,
                "partials/home/transaction_form_modal.html",
                error=error,
                extra_context={"editing_transaction": txn},
            )
        )

    applied_account, category, data = apply_transaction_payload(user, payload)
    if applied_account.pk != account.pk:
        return HttpResponse(
            render_home_modal(
                request,
                user,
                "partials/home/transaction_form_modal.html",
                error="Transakcja musi należeć do aktywnego konta.",
                extra_context={"editing_transaction": txn},
            )
        )

    update_transaction(
        txn,
        account=applied_account,
        category=category,
        amount=data["amount"],
        title=data["title"],
        description=data["description"],
        date=data["date"],
    )
    return render_home_refresh_response(request, user)


@router.delete("/transactions/{transaction_id}")
def delete_transaction_ui(request, transaction_id: int):
    user = get_authenticated_user(request)
    account = resolve_active_account(request, user)
    txn = get_user_transaction(user, transaction_id)
    if account is None or txn.account_id != account.pk:
        return HttpResponse("Transakcja nie istnieje.", status=404)
    delete_transaction(txn)
    return render_home_refresh_response(request, user)

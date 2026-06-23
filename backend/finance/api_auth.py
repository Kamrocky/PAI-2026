from django.contrib.auth import login, logout
from django.http import HttpResponse
from ninja import Form, Router

from .auth_service import (
    AuthServiceError,
    authenticate_by_email,
    normalize_email,
    register_user_by_email,
    user_exists_by_email,
)
from .auth_utils import (
    get_display_name,
    render_auth_step,
    render_auth_success,
    render_logout_success,
    require_authenticated_user,
)

router = Router(tags=["auth"])


@router.get("")
def auth_start(request):
    return render_auth_step(request, step="email")


@router.post("/check-email")
def check_email(request, email: str = Form(...)):
    try:
        normalized = normalize_email(email)
    except AuthServiceError as exc:
        return render_auth_step(request, step="email", error=exc.message)

    if user_exists_by_email(normalized):
        return render_auth_step(request, step="login", email=normalized)
    return render_auth_step(request, step="register", email=normalized)


@router.post("/login")
def login_user(request, email: str = Form(...), password: str = Form(...)):
    try:
        user = authenticate_by_email(request, email, password)
    except AuthServiceError as exc:
        normalized = email.strip().lower()
        return render_auth_step(request, step="login", email=normalized, error=exc.message)

    login(request, user)
    request.session.cycle_key()
    return render_auth_success(request, user)


@router.post("/register")
def register_user(
    request,
    email: str = Form(...),
    first_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    try:
        user = register_user_by_email(email, first_name, password, password_confirm)
    except AuthServiceError as exc:
        normalized = email.strip().lower()
        return render_auth_step(request, step="register", email=normalized, error=exc.message)

    login(request, user)
    request.session.cycle_key()
    return render_auth_success(request, user)


@router.post("/logout")
def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
    return render_logout_success(request)


@router.get("/me")
def check_me(request):
    if request.user.is_authenticated:
        return HttpResponse(
            f'<span class="text-white/90">Zalogowany jako: {get_display_name(request.user)}</span>',
        )
    return HttpResponse('<span class="text-white/80">Niezalogowany</span>')


@router.get("/protected-ping")
def protected_ping(request):
    user = require_authenticated_user(request)
    if isinstance(user, HttpResponse):
        return user
    return HttpResponse(f"OK — witaj, {get_display_name(user)}")

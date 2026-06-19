from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponse
from ninja import Form, NinjaAPI

from .api_accounts import router as accounts_router
from .api_categories import router as categories_router
from .auth_utils import (
    format_validation_error,
    render_auth_page,
    render_auth_success,
    render_logout_success,
    require_authenticated_user,
)

api = NinjaAPI()
api.add_router("/categories", categories_router)
api.add_router("/accounts", accounts_router)


@api.post("/auth/login")
def login_user(request, username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    if not username or not password:
        return render_auth_page(request, error="Podaj login i hasło.")

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        request.session.cycle_key()
        return render_auth_success(request, user)

    return render_auth_page(request, error="Błędny login lub hasło.")


@api.get("/auth/me")
def check_me(request):
    if request.user.is_authenticated:
        return HttpResponse(
            f'<span class="text-white/90">Zalogowany jako: {request.user.username}</span>',
        )
    return HttpResponse('<span class="text-white/80">Niezalogowany</span>')


@api.post("/auth/register")
def register_user(
    request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(""),
):
    username = username.strip()
    email = (email or "").strip()

    if not username or not password:
        return render_auth_page(request, error="Podaj login i hasło.")

    try:
        validate_password(password, user=User(username=username, email=email))
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )
        login(request, user)
        request.session.cycle_key()
        return render_auth_success(request, user)
    except ValidationError as exc:
        return render_auth_page(request, error=format_validation_error(exc))
    except IntegrityError:
        return render_auth_page(
            request,
            error="Użytkownik o takiej nazwie lub adresie e-mail już istnieje.",
        )


@api.post("/auth/logout")
def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
    return render_logout_success(request)


@api.get("/auth/protected-ping")
def protected_ping(request):
    user = require_authenticated_user(request)
    if isinstance(user, HttpResponse):
        return user
    return HttpResponse(f"OK — witaj, {user.username}")

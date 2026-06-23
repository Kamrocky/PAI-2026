from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.http import HttpRequest

from .auth_utils import format_validation_error


class AuthServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not email:
        raise AuthServiceError("Podaj adres e-mail.")
    try:
        validate_email(email)
    except ValidationError:
        raise AuthServiceError("Podaj poprawny adres e-mail.") from None
    return email


def find_user_by_email(email: str) -> User | None:
    normalized = normalize_email(email)
    user = User.objects.filter(username=normalized).first()
    if user is not None:
        return user
    return User.objects.filter(email__iexact=normalized).first()


def user_exists_by_email(email: str) -> bool:
    return find_user_by_email(email) is not None


def authenticate_by_email(request: HttpRequest, email: str, password: str) -> User:
    normalized = normalize_email(email)
    if not password:
        raise AuthServiceError("Podaj hasło.")

    user = authenticate(request, username=normalized, password=password)
    if user is not None:
        return user

    legacy_user = User.objects.filter(email__iexact=normalized).first()
    if legacy_user is not None:
        user = authenticate(request, username=legacy_user.username, password=password)
        if user is not None:
            return user

    raise AuthServiceError("Błędny e-mail lub hasło.")


def register_user_by_email(
    email: str,
    first_name: str,
    password: str,
    password_confirm: str,
) -> User:
    normalized = normalize_email(email)
    first_name = first_name.strip()

    if not first_name:
        raise AuthServiceError("Podaj imię.")
    if not password:
        raise AuthServiceError("Podaj hasło.")
    if password != password_confirm:
        raise AuthServiceError("Hasła nie są zgodne.")
    if user_exists_by_email(normalized):
        raise AuthServiceError("Konto z tym adresem e-mail już istnieje.")

    try:
        validate_password(
            password,
            user=User(username=normalized, email=normalized, first_name=first_name),
        )
        return User.objects.create_user(
            username=normalized,
            email=normalized,
            first_name=first_name,
            password=password,
        )
    except ValidationError as exc:
        raise AuthServiceError(format_validation_error(exc)) from exc
    except IntegrityError:
        raise AuthServiceError("Konto z tym adresem e-mail już istnieje.") from None

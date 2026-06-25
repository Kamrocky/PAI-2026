from pydantic import BaseModel, field_validator
from pydantic import ValidationError as PydanticValidationError


class ProfileNameIn(BaseModel):
    first_name: str

    @field_validator("first_name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Imię nie może być puste.")
        if len(value) > 50:
            raise ValueError("Imię nie może być dłuższe niż 50 znaków.")
        return value


class ProfilePasswordIn(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def password_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Hasło musi mieć co najmniej 8 znaków.")
        return value

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if "new_password" in info.data and value != info.data["new_password"]:
            raise ValueError("Nowe hasła nie są identyczne.")
        return value


def validate_profile_name(first_name: str) -> tuple[ProfileNameIn | None, str | None]:
    try:
        payload = ProfileNameIn(first_name=first_name)
    except PydanticValidationError as exc:
        messages = [err["msg"].removeprefix("Value error, ") for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None


def validate_profile_password(
    current_password: str,
    new_password: str,
    confirm_password: str,
) -> tuple[ProfilePasswordIn | None, str | None]:
    try:
        payload = ProfilePasswordIn(
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )
    except PydanticValidationError as exc:
        messages = [err["msg"].removeprefix("Value error, ") for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None

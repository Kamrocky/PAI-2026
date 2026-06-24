from pydantic import ValidationError as PydanticValidationError

from .constants import DEFAULT_CATEGORY_COLOR
from .schemas import CategoryIn


def _parse_is_income(value: str) -> bool:
    return value.lower() in ("true", "on", "1")


def validate_category_form(
    name: str,
    color: str,
    is_income: str,
) -> tuple[CategoryIn | None, str | None]:
    try:
        payload = CategoryIn(
            name=name,
            color=color or DEFAULT_CATEGORY_COLOR,
            is_income=_parse_is_income(is_income),
        )
    except PydanticValidationError as exc:
        messages = [err["msg"] for err in exc.errors()]
        return None, "; ".join(messages)
    return payload, None

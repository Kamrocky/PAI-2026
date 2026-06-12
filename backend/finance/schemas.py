from pydantic import ConfigDict, field_validator

from ninja import Schema


class CategoryIn(Schema):
    name: str
    icon: str = ""
    color: str = "#4CAF50"
    is_income: bool = False

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nazwa kategorii nie może być pusta.")
        return value

    @field_validator("color")
    @classmethod
    def color_format(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("#") or len(value) != 7:
            raise ValueError("Kolor musi być w formacie #RRGGBB.")
        return value


class CategoryUpdate(Schema):
    name: str | None = None
    icon: str | None = None
    color: str | None = None
    is_income: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Nazwa kategorii nie może być pusta.")
        return value

    @field_validator("color")
    @classmethod
    def color_format(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value.startswith("#") or len(value) != 7:
            raise ValueError("Kolor musi być w formacie #RRGGBB.")
        return value


class CategoryOut(Schema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str
    color: str
    is_income: bool

from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict, field_validator

from ninja import Schema

from .constants import ALLOWED_CURRENCIES, CATEGORY_COLOR_PALETTE, DEFAULT_CATEGORY_COLOR


class CategoryIn(Schema):
    name: str
    color: str = DEFAULT_CATEGORY_COLOR
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
    def color_in_palette(cls, value: str) -> str:
        value = value.strip()
        if value not in CATEGORY_COLOR_PALETTE:
            raise ValueError("Kolor musi być wybrany z predefiniowanej palety.")
        return value


class CategoryUpdate(Schema):
    name: str | None = None
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
    def color_in_palette(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if value not in CATEGORY_COLOR_PALETTE:
            raise ValueError("Kolor musi być wybrany z predefiniowanej palety.")
        return value


class CategoryOut(Schema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    is_income: bool


class AccountIn(Schema):
    name: str
    balance: Decimal = Decimal("0.00")
    currency: str = "PLN"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nazwa konta nie może być pusta.")
        return value

    @field_validator("currency")
    @classmethod
    def currency_allowed(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in ALLOWED_CURRENCIES:
            raise ValueError("Waluta musi być wybrana z predefiniowanej listy.")
        return value


class AccountUpdate(Schema):
    name: str | None = None
    balance: Decimal | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Nazwa konta nie może być pusta.")
        return value


class AccountOut(Schema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    balance: Decimal
    currency: str


class TransactionIn(Schema):
    account_id: int
    category_id: int | None = None
    amount: Decimal
    title: str
    description: str = ""
    date: datetime | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tytuł transakcji nie może być pusty.")
        return value


class TransactionUpdate(Schema):
    account_id: int | None = None
    category_id: int | None = None
    amount: Decimal | None = None
    title: str | None = None
    description: str | None = None
    date: datetime | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Tytuł transakcji nie może być pusty.")
        return value


class TransactionOut(Schema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    category_id: int | None
    amount: Decimal
    title: str
    description: str
    date: datetime

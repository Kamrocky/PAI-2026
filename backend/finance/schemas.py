from datetime import datetime
from decimal import Decimal

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
    def currency_format(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Waluta musi być trzyliterowym kodem ISO, np. PLN.")
        return value


class AccountUpdate(Schema):
    name: str | None = None
    balance: Decimal | None = None
    currency: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Nazwa konta nie może być pusta.")
        return value

    @field_validator("currency")
    @classmethod
    def currency_format(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Waluta musi być trzyliterowym kodem ISO, np. PLN.")
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

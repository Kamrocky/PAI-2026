from decimal import Decimal

from django.db.models import Sum


def sum_income_and_expenses(transactions) -> tuple[Decimal, Decimal]:
    income = transactions.filter(amount__gt=0).aggregate(total=Sum("amount"))["total"]
    expenses_raw = transactions.filter(amount__lt=0).aggregate(total=Sum("amount"))["total"]
    income_total = income or Decimal("0.00")
    expenses_total = abs(expenses_raw or Decimal("0.00"))
    return income_total, expenses_total

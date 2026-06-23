from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .constants import DEFAULT_CATEGORY_COLOR


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default="PLN")

    def __str__(self):
        return f"{self.name} ({self.balance} {self.currency})"


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default=DEFAULT_CATEGORY_COLOR)
    is_income = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)

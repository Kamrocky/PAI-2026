from ninja import NinjaAPI, Schema
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from .models import Transaction, Account
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db import IntegrityError

api = NinjaAPI()

@api.post("/auth/login")
def login_user(request, username: str = None, password: str = None):
    
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return render(request, "dashboard_partial.html", {
            "username": user.username,
            "accounts": Account.objects.filter(user=user),
            "transactions": Transaction.objects.filter(account__user=user)
        })
    return HttpResponse("<p class='text-red-500'>Błędny login lub hasło!</p>")

@api.get("/auth/me")
def check_me(request):
    if request.user.is_authenticated:
        return f"Zalogowany jako: {request.user.username}"
    return "Niezalogowany"

@api.post("/auth/register")
def register_user(request, username: str = None, password: str = None, email: str = None):
    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        login(request, user)
        return "Konto utworzone! Możesz teraz przejść do Dashboardu."
    except IntegrityError:
        return HttpResponse("<p class='text-red-500'>Użytkownik o takiej nazwie już istnieje!</p>", status=400)
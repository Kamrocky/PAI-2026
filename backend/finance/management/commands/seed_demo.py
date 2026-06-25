import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction
from django.utils import timezone

from finance.models import Account, Category
from finance.profile_service import clear_user_finance_data
from finance.transaction_service import create_transaction

RANDOM_SEED = 2026

# (nazwa, waluta) — konta demo w róznych walutach
ACCOUNTS = [
    ("Konto główne", "PLN"),
    ("Oszczędności", "EUR"),
    ("Konto walutowe", "USD"),
    ("Portfel podróżny", "GBP"),
]

# (nazwa, kolor_index, is_income)
EXPENSE_CATEGORIES = [
    ("Jedzenie", 1),
    ("Transport", 3),
    ("Mieszkanie", 4),
    ("Rozrywka", 5),
    ("Zdrowie", 6),
    ("Ubrania", 7),
    ("Rachunki", 8),
    ("Restauracje", 11),
]
INCOME_CATEGORIES = [
    ("Wynagrodzenie", 1),
    ("Freelance", 2),
    ("Zwroty", 9),
    ("Prezenty", 10),
]

# Tytuły transakcji dla kazdej kategorii wydatków
EXPENSE_TITLES = {
    "Jedzenie": ["Zakupy spożywcze", "Biedronka", "Lidl", "Warzywniak", "Piekarnia"],
    "Transport": ["Bilet miesięczny", "Paliwo", "Taxi", "Parking", "Przejazd Uber"],
    "Mieszkanie": ["Czynsz", "Prąd", "Internet", "Woda"],
    "Rozrywka": ["Kino", "Netflix", "Spotify", "Koncert", "Gra na Steam"],
    "Zdrowie": ["Apteka", "Wizyta u lekarza", "Suplementy", "Dentysta"],
    "Ubrania": ["Buty", "Kurtka", "Koszula", "Zara"],
    "Rachunki": ["Telefon", "Ubezpieczenie", "Abonament RTV", "Subskrypcja"],
    "Restauracje": ["Obiad w mieście", "Pizza", "Sushi", "Kawa", "Burger"],
}
INCOME_TITLES = {
    "Wynagrodzenie": ["Pensja", "Wynagrodzenie miesięczne"],
    "Freelance": ["Projekt freelance", "Zlecenie", "Konsultacje"],
    "Zwroty": ["Zwrot podatku", "Zwrot zakupu", "Cashback"],
    "Prezenty": ["Prezent urodzinowy", "Prezent rodzinny"],
}

# Mnożniki kwot wzgledem PLN (zeby kwoty w innych walutach były realistyczne)
CURRENCY_SCALE = {
    "PLN": Decimal("1"),
    "EUR": Decimal("0.23"),
    "USD": Decimal("0.25"),
    "GBP": Decimal("0.20"),
}


class Command(BaseCommand):
    help = "Wypełnia bazę przykładowymi danymi demo dla wskazanego użytkownika."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            required=True,
            help="Adres e-mail (username) istniejącego użytkownika, dla którego tworzymy dane.",
        )
        parser.add_argument(
            "--months",
            type=int,
            default=5,
            help="Na ile miesięcy wstecz rozłożyć transakcje (domyślnie 5).",
        )

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        months = options["months"]

        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            raise CommandError(
                f"Użytkownik '{email}' nie istnieje. Najpierw zarejestruj konto w aplikacji."
            )

        random.seed(RANDOM_SEED)

        with db_transaction.atomic():
            clear_user_finance_data(user)
            categories = self._create_categories(user)
            accounts = self._create_accounts(user)
            count = self._create_transactions(accounts, categories, months)

        num_categories = len(categories["expense"]) + len(categories["income"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Gotowe. Dla '{email}' utworzono: "
                f"{len(accounts)} konta, {num_categories} kategorii, {count} transakcji."
            )
        )

    def _create_categories(self, user):
        from finance.constants import CATEGORY_COLOR_PALETTE

        categories = {"expense": [], "income": []}
        for name, color_idx in EXPENSE_CATEGORIES:
            cat = Category.objects.create(
                user=user,
                name=name,
                color=CATEGORY_COLOR_PALETTE[color_idx],
                is_income=False,
            )
            categories["expense"].append(cat)
        for name, color_idx in INCOME_CATEGORIES:
            cat = Category.objects.create(
                user=user,
                name=name,
                color=CATEGORY_COLOR_PALETTE[color_idx],
                is_income=True,
            )
            categories["income"].append(cat)
        return categories

    def _create_accounts(self, user):
        accounts = []
        for name, currency in ACCOUNTS:
            account = Account.objects.create(
                user=user, name=name, balance=Decimal("0.00"), currency=currency
            )
            accounts.append(account)
        return accounts

    def _scaled(self, amount_pln: Decimal, currency: str) -> Decimal:
        scaled = amount_pln * CURRENCY_SCALE[currency]
        return scaled.quantize(Decimal("0.01"))

    def _create_transactions(self, accounts, categories, months):
        now = timezone.now()
        count = 0

        for account in accounts:
            currency = account.currency
            # Wynagrodzenie tylko na koncie głównym (PLN); inne konta mają mniej ruchu
            is_main = account.currency == "PLN" and account.name == "Konto główne"

            for month_offset in range(months):
                month_start = now - timedelta(days=30 * month_offset)

                if is_main:
                    count += self._add_income(
                        account, categories, "Wynagrodzenie",
                        Decimal("8500"), month_start, day=5,
                    )
                else:
                    # Konta poboczne: gwarantowany miesięczny wpływ, by saldo było dodatnie
                    cat_name = random.choice(["Freelance", "Zwroty", "Prezenty"])
                    base = Decimal(random.randint(2000, 4000))
                    count += self._add_income(
                        account, categories, cat_name,
                        self._scaled(base, currency), month_start,
                        day=random.randint(3, 10),
                    )

                # Okazjonalny dodatkowy przychód freelance / zwroty
                if random.random() < 0.4:
                    cat_name = random.choice(["Freelance", "Zwroty", "Prezenty"])
                    base = Decimal(random.randint(300, 2500))
                    count += self._add_income(
                        account, categories, cat_name,
                        self._scaled(base, currency), month_start,
                        day=random.randint(8, 25),
                    )

                # Wydatki — kilka-kilkanaście na miesiąc
                num_expenses = random.randint(6, 12) if is_main else random.randint(2, 5)
                for _ in range(num_expenses):
                    cat = random.choice(categories["expense"])
                    base = Decimal(random.randint(20, 600))
                    amount = -self._scaled(base, currency)
                    title = random.choice(EXPENSE_TITLES[cat.name])
                    date = month_start - timedelta(
                        days=random.randint(0, 27),
                        hours=random.randint(0, 23),
                    )
                    create_transaction(
                        account=account,
                        category=cat,
                        amount=amount,
                        title=title,
                        description="",
                        date=date,
                    )
                    count += 1

        return count

    def _add_income(self, account, categories, cat_name, amount, month_start, day):
        cat = next(c for c in categories["income"] if c.name == cat_name)
        title = random.choice(INCOME_TITLES[cat_name])
        date = month_start.replace(day=min(day, 28))
        create_transaction(
            account=account,
            category=cat,
            amount=amount,
            title=title,
            description="",
            date=date,
        )
        return 1

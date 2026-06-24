from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from finance.models import Account, Transaction


class HomeAccountUiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "Silne!Haslo1"
        self.user = User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
            first_name="Jan",
        )
        self.client.login(username="jan@example.com", password=self.password)

    def test_create_account_appears_in_carousel(self):
        response = self.client.post(
            "/api/ui/home/accounts",
            {"name": "Oszczędności", "currency": "EUR", "balance": "500.00"},
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Oszczędności", content)
        self.assertIn("EUR", content)
        self.assertIn('id="home-content"', content)
        self.assertTrue(Account.objects.filter(user=self.user, name="Oszczędności").exists())

    def test_rename_account_updates_carousel(self):
        account = Account.objects.create(
            user=self.user,
            name="Stara nazwa",
            balance=Decimal("100.00"),
            currency="PLN",
        )

        response = self.client.post(
            f"/api/ui/home/accounts/{account.pk}/edit",
            {"name": "Nowa nazwa"},
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Nowa nazwa", content)
        self.assertNotIn("Stara nazwa", content)
        account.refresh_from_db()
        self.assertEqual(account.name, "Nowa nazwa")

    def test_delete_account_removes_transactions_and_switches_active(self):
        first = Account.objects.create(
            user=self.user,
            name="Konto A",
            balance=Decimal("100.00"),
            currency="PLN",
        )
        second = Account.objects.create(
            user=self.user,
            name="Konto B",
            balance=Decimal("200.00"),
            currency="PLN",
        )
        Transaction.objects.create(
            account=first,
            amount=Decimal("-25.00"),
            title="Zakupy",
            date=timezone.now(),
        )

        response = self.client.delete(f"/api/ui/home/accounts/{first.pk}")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Konto A", content)
        self.assertIn("Konto B", content)
        self.assertIn("Wydatki", content)
        self.assertFalse(Account.objects.filter(pk=first.pk).exists())
        self.assertFalse(Transaction.objects.filter(account_id=first.pk).exists())

    def test_delete_confirm_modal_renders(self):
        account = Account.objects.create(
            user=self.user,
            name="Główne",
            balance=Decimal("1000.00"),
            currency="PLN",
        )

        response = self.client.get(f"/api/ui/home/accounts/{account.pk}/delete-confirm")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Usunąć konto?", content)
        self.assertIn("Główne", content)
        self.assertIn("Tak, usuń konto", content)
        self.assertIn("nie można cofnąć", content)
        self.assertNotIn("hx-confirm", content)

    def test_edit_modal_renders_for_account(self):
        account = Account.objects.create(
            user=self.user,
            name="Główne",
            balance=Decimal("1000.00"),
            currency="PLN",
        )

        response = self.client.get(f"/api/ui/home/accounts/{account.pk}/edit")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Edytuj konto", content)
        self.assertIn('name="name"', content)
        self.assertIn("Główne", content)
        self.assertIn("Usuń konto", content)
        self.assertNotIn("hx-confirm", content)

    def test_create_modal_renders_currency_select(self):
        response = self.client.get("/api/ui/home/accounts/create")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Nowe konto", content)
        self.assertIn('name="currency"', content)
        self.assertIn("data-currency-picker", content)
        self.assertIn("Polski złoty", content)
        self.assertIn("PLN", content)

from django.contrib.auth.models import User
from django.test import Client, TestCase

from finance.models import Account, Category, Transaction


class ProfileUITest(TestCase):
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

    def _seed_finance_data(self):
        account = Account.objects.create(user=self.user, name="Główne", balance="100.00")
        category = Category.objects.create(user=self.user, name="Jedzenie", is_income=False)
        Transaction.objects.create(
            account=account,
            category=category,
            amount="-10.00",
            title="Obiad",
        )
        return account, category

    def test_profile_section_shows_readonly_email(self):
        response = self.client.get("/api/ui/profile")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("jan@example.com", content)
        self.assertNotIn("/api/ui/profile/email", content)
        self.assertNotIn("Zapisz e-mail", content)

    def test_clear_data_removes_accounts_transactions_and_categories(self):
        self._seed_finance_data()
        self.assertEqual(Account.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Category.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)

        response = self.client.post("/api/ui/profile/clear-data")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("zostały usunięte", content)
        self.assertEqual(Account.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Category.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_account_logs_out_and_removes_user(self):
        self._seed_finance_data()
        response = self.client.delete("/api/ui/profile/account")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Podaj adres e-mail", content)
        self.assertIn('id="home-modal" hx-swap-oob="innerHTML"', content)
        self.assertEqual(response["HX-Push-Url"], "/")
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertEqual(Account.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)

    def test_clear_data_confirm_modal(self):
        response = self.client.get("/api/ui/profile/clear-data/confirm")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Wyczyścić wszystkie dane?", content)
        self.assertIn("/api/ui/profile/clear-data", content)

    def test_delete_account_confirm_modal(self):
        response = self.client.get("/api/ui/profile/delete-account/confirm")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Usunąć konto użytkownika?", content)
        self.assertIn("/api/ui/profile/account", content)

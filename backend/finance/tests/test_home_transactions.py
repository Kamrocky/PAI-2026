from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, RequestFactory, TestCase
from django.utils import timezone

from finance.home_service import (
    COLLAPSED_TXN_LIMIT,
    EXPANDED_TXN_PAGE_SIZE,
    get_account_transactions,
    get_home_transactions_context,
    is_transactions_expanded,
    set_transactions_expanded,
)
from finance.models import Account, Category, Transaction
from finance.transaction_service import create_transaction


class HomeTransactionsServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jan@example.com", password="pass")
        self.account = Account.objects.create(
            user=self.user,
            name="Główne",
            balance=Decimal("1000.00"),
            currency="PLN",
        )
        self.factory = RequestFactory()
        self.client = Client()

    def _request(self):
        request = self.factory.get("/")
        request.session = self.client.session
        return request

    def _create_transactions(self, count: int) -> None:
        for index in range(count):
            Transaction.objects.create(
                account=self.account,
                amount=Decimal(f"-{index + 1}.00"),
                title=f"Transakcja {index + 1}",
                date=timezone.now() - timedelta(hours=index),
            )

    def test_collapsed_list_limits_to_five(self):
        self._create_transactions(7)
        page = get_account_transactions(self.account, expanded=False)

        self.assertEqual(len(page.transactions), COLLAPSED_TXN_LIMIT)
        self.assertTrue(page.has_more)
        self.assertFalse(page.expanded)

    def test_expanded_list_uses_pagination(self):
        self._create_transactions(12)
        page = get_account_transactions(self.account, page=2, expanded=True)

        self.assertEqual(page.page, 2)
        self.assertEqual(page.num_pages, 2)
        self.assertEqual(len(page.transactions), 2)
        self.assertEqual(page.page_size, EXPANDED_TXN_PAGE_SIZE)

    def test_transactions_context_respects_expanded_session(self):
        self._create_transactions(3)
        request = self._request()
        set_transactions_expanded(request, True)

        context = get_home_transactions_context(self.user, request, self.account)

        self.assertTrue(context["transactions_expanded"])
        self.assertTrue(is_transactions_expanded(request))


class HomeTransactionsUiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "Silne!Haslo1"
        self.user = User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
        )
        self.account = Account.objects.create(
            user=self.user,
            name="Główne",
            balance=Decimal("1000.00"),
            currency="PLN",
        )
        self.category = Category.objects.create(
            user=self.user,
            name="Jedzenie",
            color="#4DB6A0",
        )
        self.client.login(username="jan@example.com", password=self.password)

    def test_home_shows_transactions_for_active_account(self):
        Transaction.objects.create(
            account=self.account,
            category=self.category,
            amount=Decimal("-25.00"),
            title="Zakupy",
            date=timezone.now(),
        )
        other_account = Account.objects.create(
            user=self.user,
            name="Inne",
            balance=Decimal("0.00"),
        )
        Transaction.objects.create(
            account=other_account,
            amount=Decimal("-99.00"),
            title="Obce",
            date=timezone.now(),
        )

        response = self.client.get("/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Transakcje", content)
        self.assertIn("Zakupy", content)
        self.assertNotIn("Obce", content)
        self.assertIn("#4DB6A0", content)
        self.assertIn('aria-label="Dodaj transakcję"', content)

    def test_expand_transactions_shows_pagination_controls(self):
        for index in range(12):
            Transaction.objects.create(
                account=self.account,
                amount=Decimal(f"-{index + 1}.00"),
                title=f"Tx {index}",
                date=timezone.now() - timedelta(minutes=index),
            )

        response = self.client.post("/api/ui/home/transactions/expand")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Zwiń", content)
        self.assertIn('aria-label="Paginacja transakcji"', content)

    def test_transaction_detail_modal_and_edit_updates_balance(self):
        txn = create_transaction(
            account=self.account,
            category=self.category,
            amount=Decimal("-50.00"),
            title="Kino",
            description="Bilet",
        )
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("950.00"))

        detail = self.client.get(f"/api/ui/home/transactions/{txn.pk}")
        detail_content = detail.content.decode()
        self.assertEqual(detail.status_code, 200)
        self.assertIn('role="dialog"', detail_content)
        self.assertIn("Szczegóły transakcji", detail_content)
        self.assertIn("Bilet", detail_content)
        self.assertIn(f"/api/ui/home/transactions/{txn.pk}/edit", detail_content)

        edit_modal = self.client.get(f"/api/ui/home/transactions/{txn.pk}/edit")
        self.assertEqual(edit_modal.status_code, 200)
        self.assertIn("Edytuj transakcję", edit_modal.content.decode())

        response = self.client.post(
            f"/api/ui/home/transactions/{txn.pk}/edit",
            {
                "account_id": self.account.pk,
                "category_id": self.category.pk,
                "amount": "-30.00",
                "title": "Kino poprawione",
                "description": "",
                "date": txn.date.strftime("%Y-%m-%dT%H:%M"),
            },
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Kino poprawione", content)
        self.assertIn('id="home-modal"', content)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("970.00"))

    def test_create_transaction_modal_adds_to_list(self):
        create_modal = self.client.get("/api/ui/home/transactions/create")
        self.assertEqual(create_modal.status_code, 200)
        self.assertIn("Dodaj transakcję", create_modal.content.decode())

        response = self.client.post(
            "/api/ui/home/transactions",
            {
                "account_id": self.account.pk,
                "category_id": self.category.pk,
                "amount": "-15.00",
                "title": "Kawa",
                "description": "Rano",
                "date": "",
            },
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Kawa", content)
        self.assertTrue(Transaction.objects.filter(title="Kawa").exists())
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("985.00"))

    def test_delete_transaction_shows_confirm_modal_and_updates_balance(self):
        txn = create_transaction(
            account=self.account,
            category=None,
            amount=Decimal("-40.00"),
            title="Do usunięcia",
            description="",
        )
        self.account.refresh_from_db()

        confirm = self.client.get(f"/api/ui/home/transactions/{txn.pk}/delete-confirm")
        confirm_content = confirm.content.decode()
        self.assertEqual(confirm.status_code, 200)
        self.assertIn("Usunąć transakcję?", confirm_content)
        self.assertIn("Do usunięcia", confirm_content)

        response = self.client.delete(f"/api/ui/home/transactions/{txn.pk}")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Do usunięcia", content)
        self.assertFalse(Transaction.objects.filter(pk=txn.pk).exists())
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("1000.00"))

    def test_cannot_view_transaction_from_other_account(self):
        other = Account.objects.create(user=self.user, name="Inne", balance=Decimal("0.00"))
        txn = Transaction.objects.create(
            account=other,
            amount=Decimal("-10.00"),
            title="Obca",
        )

        response = self.client.get(f"/api/ui/home/transactions/{txn.pk}")

        self.assertEqual(response.status_code, 404)

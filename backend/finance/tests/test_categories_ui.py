from django.contrib.auth.models import User
from django.test import Client, TestCase

from finance.constants import CATEGORY_COLOR_PALETTE
from finance.models import Category


class CategoriesUiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "Silne!Haslo1"
        self.user = User.objects.create_user(
            username="jan@example.com",
            email="jan@example.com",
            password=self.password,
        )
        self.client.login(username="jan@example.com", password=self.password)

    def test_create_expense_category_refreshes_list(self):
        response = self.client.post(
            "/api/ui/categories",
            {
                "name": "Jedzenie",
                "color": CATEGORY_COLOR_PALETTE[1],
                "is_income": "",
            },
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="categories-content"', content)
        self.assertIn("Kategoria została dodana.", content)
        self.assertIn("alert-auto-dismiss", content)
        self.assertIn("Jedzenie", content)
        self.assertIn("Wydatki", content)
        category = Category.objects.get(user=self.user, name="Jedzenie")
        self.assertFalse(category.is_income)

    def test_create_income_category(self):
        response = self.client.post(
            "/api/ui/categories",
            {
                "name": "Pensja",
                "color": CATEGORY_COLOR_PALETTE[0],
                "is_income": "on",
            },
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Pensja", content)
        self.assertTrue(Category.objects.get(user=self.user, name="Pensja").is_income)

    def test_edit_category_updates_name(self):
        category = Category.objects.create(user=self.user, name="Stara", color=CATEGORY_COLOR_PALETTE[0])
        response = self.client.post(
            f"/api/ui/categories/{category.pk}/edit",
            {"name": "Nowa", "color": CATEGORY_COLOR_PALETTE[2]},
        )
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Kategoria została zaktualizowana.", content)
        self.assertIn("alert-auto-dismiss", content)
        self.assertIn("Nowa", content)
        self.assertNotIn("Stara", content)
        category.refresh_from_db()
        self.assertEqual(category.name, "Nowa")
        self.assertEqual(category.color, CATEGORY_COLOR_PALETTE[2])

    def test_delete_category_removes_from_list(self):
        category = Category.objects.create(user=self.user, name="Do usunięcia", color=CATEGORY_COLOR_PALETTE[0])
        response = self.client.delete(f"/api/ui/categories/{category.pk}")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Kategoria została usunięta.", content)
        self.assertIn("alert-auto-dismiss", content)
        self.assertNotIn("Do usunięcia", content)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_create_modal_renders(self):
        response = self.client.get("/api/ui/categories/create")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('role="dialog"', content)
        self.assertIn("Nowa kategoria", content)
        self.assertIn('name="is_income"', content)

    def test_categories_page_shows_existing_on_full_load(self):
        Category.objects.create(
            user=self.user,
            name="Istniejąca",
            color=CATEGORY_COLOR_PALETTE[0],
            is_income=False,
        )

        response = self.client.get("/categories/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Istniejąca", content)
        self.assertIn("Wydatki", content)

    def test_categories_api_lists_existing_categories(self):
        Category.objects.create(
            user=self.user,
            name="Z API",
            color=CATEGORY_COLOR_PALETTE[0],
            is_income=False,
        )

        response = self.client.get("/api/ui/categories")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Z API", content)
        self.assertIn('id="categories-content"', content)

    def test_cannot_edit_other_users_category(self):
        other = User.objects.create_user(username="other@example.com", password="pass")
        category = Category.objects.create(user=other, name="Cudza", color=CATEGORY_COLOR_PALETTE[0])

        response = self.client.get(f"/api/ui/categories/{category.pk}/edit")

        self.assertEqual(response.status_code, 404)

from html import unescape
import os
import sqlite3
import tempfile
import unittest

import app as localmart
from werkzeug.security import check_password_hash


class LocalMartTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = localmart.DATABASE
        localmart.DATABASE = os.path.join(self.temp_dir.name, "test.db")
        localmart.init_db()
        localmart.app.config.update(TESTING=True)
        self.client = localmart.app.test_client()

    def tearDown(self):
        localmart.DATABASE = self.database_path
        self.temp_dir.cleanup()

    def register(self, email="alex@example.com", role="customer"):
        return self.client.post(
            "/register",
            data={
                "name": "Alex Customer",
                "email": email,
                "role": role,
                "password": "secure-pass-123",
                "confirm_password": "secure-pass-123",
            },
        )

    def test_registration_signs_in_and_shows_persisted_profile(self):
        response = self.register(email="Alex@Example.com", role="seller")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/profile")

        profile = self.client.get(response.headers["Location"])
        self.assertEqual(profile.status_code, 200)
        self.assertIn(b"Alex Customer", profile.data)
        self.assertIn(b"Seller", profile.data)

        connection = sqlite3.connect(localmart.DATABASE)
        try:
            row = connection.execute(
                "SELECT email, password_hash, role FROM users"
            ).fetchone()
        finally:
            connection.close()

        self.assertEqual(row[0], "alex@example.com")
        self.assertTrue(check_password_hash(row[1], "secure-pass-123"))
        self.assertNotEqual(row[1], "secure-pass-123")
        self.assertEqual(row[2], "seller")

    def test_duplicate_email_is_rejected_without_creating_another_account(self):
        self.register()
        self.client.post("/logout")

        response = self.register(email="ALEX@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"This email is already registered.", response.data)

        connection = sqlite3.connect(localmart.DATABASE)
        try:
            count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 1)

    def test_login_and_profile_require_valid_credentials(self):
        self.register()
        self.client.post("/logout")

        denied = self.client.post(
            "/login",
            data={"email": "alex@example.com", "password": "incorrect"},
        )
        self.assertEqual(denied.status_code, 200)
        self.assertIn(b"Email or password is incorrect.", denied.data)
        self.assertEqual(self.client.get("/profile").status_code, 302)

        accepted = self.client.post(
            "/login",
            data={"email": "ALEX@example.com", "password": "secure-pass-123"},
        )
        self.assertEqual(accepted.status_code, 302)
        self.assertEqual(accepted.headers["Location"], "/profile")
        self.assertEqual(self.client.get("/profile").status_code, 200)

    def test_business_pages_and_unknown_business_response(self):
        for business in localmart.BUSINESSES:
            response = self.client.get(f"/business/{business['slug']}")
            self.assertEqual(response.status_code, 200)
            self.assertIn(business["name"].encode(), response.data)
            self.assertEqual(len(business["products"]), 25)
            self.assertEqual(response.data.count(b'class="product-card"'), 25)
            self.assertEqual(
                response.data.count(b'class="product-availability">Available</span>'),
                25,
            )
            rendered_page = unescape(response.get_data(as_text=True))
            for product in business["products"]:
                self.assertIn(product, rendered_page)
            self.assertIn(b"openstreetmap.org/export/embed.html", response.data)

        self.assertEqual(self.client.get("/business/not-a-business").status_code, 404)

    def test_category_pages_show_related_products_and_empty_categories(self):
        food = self.client.get("/category/food")
        self.assertEqual(food.status_code, 200)
        self.assertIn(b"Fresh Bakery", food.data)
        self.assertIn(b"White Sandwich Bread", food.data)
        self.assertIn(b"/business/fresh-bakery#products-heading", food.data)

        empty_category = self.client.get("/category/electronics")
        self.assertEqual(empty_category.status_code, 200)
        self.assertIn(b"no businesses or products", empty_category.data.lower())
        self.assertEqual(self.client.get("/category/not-a-category").status_code, 404)

    def test_cart_add_update_remove_and_clear(self):
        added = self.client.post(
            "/business/fresh-bakery/cart",
            data={
                "products": ["White Sandwich Bread", "Garlic Bread"],
                "quantity_1": "2",
                "quantity_4": "3",
            },
        )
        self.assertEqual(added.status_code, 302)
        self.assertEqual(added.headers["Location"], "/cart")

        cart_page = self.client.get("/cart")
        self.assertIn(b"White Sandwich Bread", cart_page.data)
        self.assertIn(b"Garlic Bread", cart_page.data)
        self.assertIn(b"5 item(s) in your cart", cart_page.data)

        self.assertEqual(self.register(email="cart-owner@example.com").status_code, 302)
        self.assertIn(b"5 item(s) in your cart", self.client.get("/cart").data)
        self.client.post("/logout")
        self.assertIn(b"5 item(s) in your cart", self.client.get("/cart").data)

        updated = self.client.post(
            "/cart/update",
            data={
                "action": "update",
                "business_slug": "fresh-bakery",
                "product": "White Sandwich Bread",
                "quantity": "4",
            },
        )
        self.assertEqual(updated.status_code, 302)
        self.assertIn(b"7 item(s) in your cart", self.client.get("/cart").data)

        removed = self.client.post(
            "/cart/update",
            data={
                "action": "remove",
                "business_slug": "fresh-bakery",
                "product": "Garlic Bread",
            },
        )
        self.assertEqual(removed.status_code, 302)
        cart_page = self.client.get("/cart")
        self.assertNotIn(b"Garlic Bread", cart_page.data)
        self.assertIn(b"4 item(s) in your cart", cart_page.data)

        cleared = self.client.post("/cart/update", data={"action": "clear"})
        self.assertEqual(cleared.status_code, 302)
        self.assertIn(b"Your cart is empty", self.client.get("/cart").data)

    def test_cart_rejects_products_not_in_the_business_catalog(self):
        response = self.client.post(
            "/business/fresh-bakery/cart",
            data={"products": ["Product that does not exist"]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Your cart is empty", self.client.get("/cart").data)

    def test_homepage_and_static_assets_load(self):
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertIn(b"All Businesses", home.data)
        self.assertIn(b"/business/fresh-bakery", home.data)

        script = self.client.get("/static/js/script.js")
        stylesheet = self.client.get("/static/css/style.css")
        self.assertEqual(script.status_code, 200)
        self.assertEqual(stylesheet.status_code, 200)
        script.close()
        stylesheet.close()


if __name__ == "__main__":
    unittest.main()

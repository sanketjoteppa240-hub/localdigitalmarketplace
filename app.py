from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import os
import re
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get(
    "LOCALMART_SECRET_KEY",
    "localmart-development-secret-key",
)

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

BUSINESSES = [
    {
        "slug": "fresh-bakery",
        "name": "Fresh Bakery",
        "category": "Food",
        "description": "Freshly baked bread, pastries, and treats made every day.",
        "image": "🥖",
        "image_class": "bakery-image",
        "latitude": 12.9055153,
        "longitude": 77.6277689,
        "map_bbox": "77.6230,12.9025,77.6325,12.9090",
        "map_label": "Near Lulu Bakery, Begur Road",
        "map_note": (
            "The map marks nearby Lulu Bakery, listed in OpenStreetMap. "
            "Fresh Bakery and its catalog are demo data; its exact shop address "
            "has not been verified."
        ),
        "products": [
            "White Sandwich Bread",
            "Whole Wheat / Multigrain Bread",
            "Sourdough Loaf",
            "Garlic Bread",
            "Burger Buns & Dinner Rolls (Pav)",
            "Butter Croissant",
            "Chocolate Croissant",
            "Veg / Paneer Puff Pastry",
            "Cream Roll",
            "Cinnamon Roll",
            "Black Forest Cake",
            "Chocolate Truffle Cake",
            "Red Velvet Pastry",
            "Pineapple Cream Cake",
            "Mawa / Tea Cake",
            "Chocolate Brownie",
            "Choco-Chip Muffin",
            "Red Velvet Cupcake",
            "Glazed Donut",
            "Chocolate Chip Cookies",
            "Butter / Shrewsbury Cookies",
            "Khari Biscuits",
            "Rusk / Milk Toast",
            "Veg Sandwich",
            "Savory Quiche",
        ],
    },
    {
        "slug": "fashion-store",
        "name": "Fashion Store",
        "category": "Fashion",
        "description": "Explore thoughtfully selected clothing and local styles.",
        "image": "👗",
        "image_class": "fashion-image",
        "latitude": 12.9034581,
        "longitude": 77.6230028,
        "map_bbox": "77.6195324,12.8963290,77.6311381,12.9105698",
        "map_label": "Bommanahalli (approximate demo location)",
        "map_note": (
            "No specific clothing shop was confirmed in the map data. "
            "This pin marks the approximate Bommanahalli area; Fashion Store "
            "and its catalog are demo data."
        ),
        "products": [
            "Crew-Neck Cotton T-Shirt",
            "Polo T-Shirt",
            "Oversized Graphic Tee",
            "Formal Button-Down Shirt",
            "Casual Linen Shirt",
            "Women’s Blouse / Top",
            "Crop Top",
            "Kurta / Kurti",
            "Slim-Fit Jeans",
            "Straight-Fit / Baggy Jeans",
            "Chino Trousers",
            "Formal Dress Pants",
            "Cargo Pants",
            "Joggers / Track Pants",
            "Denim / Cotton Shorts",
            "Midi / Maxi Skirt",
            "Palazzo Pants",
            "Leggings",
            "Casual Sundress",
            "Party / Cocktail Dress",
            "Co-ord Set",
            "Denim / Bomber Jacket",
            "Hoodie / Sweatshirt",
            "Scarf / Dupatta",
            "Leather Belt & Tote Bag",
        ],
    },
    {
        "slug": "green-grocery",
        "name": "Green Grocery",
        "category": "Groceries",
        "description": "Fresh vegetables, fruit, and everyday grocery essentials.",
        "image": "🥬",
        "image_class": "grocery-image",
        "latitude": 12.9085640,
        "longitude": 77.6239237,
        "map_bbox": "77.6196,12.9055,77.6282,12.9116",
        "map_label": "Near ALV Fresh Supermarket, Viratnagar Main Road",
        "map_note": (
            "The map marks nearby ALV Fresh Supermarket, listed in OpenStreetMap. "
            "Green Grocery and its catalog are demo data; its exact shop address "
            "has not been verified."
        ),
        "products": [
            "Potatoes",
            "Red Onions",
            "Tomatoes",
            "Carrots",
            "Cucumbers",
            "Bell Peppers (Capsicum)",
            "Spinach (Palak)",
            "Coriander & Mint Leaves",
            "Cauliflower & Cabbage",
            "Broccoli",
            "Eggplant (Brinjal)",
            "Okra (Ladyfinger / Bhindi)",
            "Garlic, Ginger & Green Chilies",
            "Bananas",
            "Apples",
            "Oranges",
            "Mangoes",
            "Watermelon & Papaya",
            "Grapes & Pomegranate",
            "Lemons",
            "Basmati / Regular Rice",
            "Whole Wheat Flour (Atta)",
            "Lentils (Toor, Moong & Chana Dal)",
            "Cooking Oil & Ghee",
            "Milk, Curd, Paneer & Eggs",
        ],
    },
]

CATEGORIES = [
    {"name": "All Businesses", "slug": "all", "icon": "✨"},
    {"name": "Groceries", "slug": "groceries", "icon": "🛒"},
    {"name": "Fashion", "slug": "fashion", "icon": "👕"},
    {"name": "Food", "slug": "food", "icon": "🍔"},
    {"name": "Electronics", "slug": "electronics", "icon": "💻"},
    {"name": "Home Services", "slug": "home-services", "icon": "🔧"},
    {"name": "Beauty", "slug": "beauty", "icon": "💇"},
]


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None

    if user_id is not None:
        connection = get_db_connection()
        try:
            g.user = connection.execute(
                "SELECT id, name, email, role, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        finally:
            connection.close()


@app.context_processor
def inject_current_user():
    cart = session.get("cart", {})
    cart_count = sum(
        quantity
        for products in cart.values()
        for quantity in products.values()
    )
    return {
        "current_user": getattr(g, "user", None),
        "cart_count": cart_count,
    }


def find_business(slug):
    return next((item for item in BUSINESSES if item["slug"] == slug), None)


def get_cart_items():
    cart = session.get("cart", {})
    items = []
    for slug, products in cart.items():
        business = find_business(slug)
        if business is None:
            continue
        for product, quantity in products.items():
            if product in business["products"]:
                items.append(
                    {
                        "business_slug": slug,
                        "business_name": business["name"],
                        "product": product,
                        "quantity": quantity,
                    }
                )
    return items


def clear_auth_session():
    cart = session.get("cart", {})
    session.clear()
    if cart:
        session["cart"] = cart


@app.route("/")
def home():
    return render_template(
        "index.html",
        businesses=BUSINESSES,
        categories=CATEGORIES,
    )


@app.route("/category/<category_slug>")
def category_detail(category_slug):
    category = next(
        (item for item in CATEGORIES if item["slug"] == category_slug),
        None,
    )
    if category is None:
        abort(404)

    businesses = [
        business
        for business in BUSINESSES
        if category_slug == "all"
        or business["category"].lower() == category_slug
    ]
    return render_template(
        "category.html",
        category=category,
        businesses=businesses,
    )


@app.route("/business/<slug>")
def business_detail(slug):
    business = find_business(slug)
    if business is None:
        abort(404)
    return render_template("business.html", business=business)


@app.route("/business/<slug>/cart", methods=["POST"])
def add_to_cart(slug):
    business = find_business(slug)
    if business is None:
        abort(404)

    selected_products = list(dict.fromkeys(request.form.getlist("products")))
    if not selected_products:
        flash("Select at least one product to add to your cart.", "error")
        return redirect(url_for("business_detail", slug=slug))

    if any(product not in business["products"] for product in selected_products):
        abort(400)

    cart = session.get("cart", {})
    additions = {}
    for product in selected_products:
        product_index = business["products"].index(product) + 1
        quantity_value = request.form.get(f"quantity_{product_index}", "1")
        try:
            quantity = int(quantity_value)
        except ValueError:
            flash("Enter a valid quantity for each selected product.", "error")
            return redirect(url_for("business_detail", slug=slug))

        current_quantity = cart.get(slug, {}).get(product, 0)
        if quantity < 1 or current_quantity + quantity > 99:
            flash("Each product's cart quantity must total between 1 and 99.", "error")
            return redirect(url_for("business_detail", slug=slug))
        additions[product] = current_quantity + quantity

    cart.setdefault(slug, {}).update(additions)
    session["cart"] = cart
    flash(f"Added {len(selected_products)} product(s) to your cart.", "success")
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    items = get_cart_items()
    return render_template(
        "cart.html",
        items=items,
        total_items=sum(item["quantity"] for item in items),
    )


@app.route("/cart/update", methods=["POST"])
def update_cart():
    action = request.form.get("action")
    cart_items = session.get("cart", {})

    if action == "clear":
        session["cart"] = {}
        flash("Your cart has been cleared.", "success")
        return redirect(url_for("cart"))

    slug = request.form.get("business_slug", "")
    product = request.form.get("product", "")
    business = find_business(slug)
    if business is None or product not in business["products"]:
        abort(400)

    products = cart_items.get(slug, {})
    if product not in products:
        abort(404)

    if action == "remove":
        products.pop(product)
        if not products:
            cart_items.pop(slug)
        flash("Product removed from your cart.", "success")
    elif action == "update":
        try:
            quantity = int(request.form.get("quantity", ""))
        except ValueError:
            flash("Enter a valid quantity.", "error")
            return redirect(url_for("cart"))
        if quantity < 1 or quantity > 99:
            flash("Quantity must be between 1 and 99.", "error")
            return redirect(url_for("cart"))
        products[product] = quantity
        flash("Cart quantity updated.", "success")
    else:
        abort(400)

    session["cart"] = cart_items
    return redirect(url_for("cart"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user is not None:
        return redirect(url_for("profile"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "customer")

        if not name or not email or not password or not confirm_password:
            flash("Please fill in all fields.", "error")
        elif len(name) > 80 or len(email) > 254:
            flash("Name or email is too long.", "error")
        elif re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is None:
            flash("Please enter a valid email address.", "error")
        elif role not in {"customer", "seller"}:
            flash("Please choose a valid account type.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            connection = get_db_connection()
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, email, generate_password_hash(password), role),
                )
                connection.commit()
                clear_auth_session()
                session["user_id"] = cursor.lastrowid
                flash("Your account has been created.", "success")
                return redirect(url_for("profile"))
            except sqlite3.IntegrityError:
                flash("This email is already registered.", "error")
            finally:
                connection.close()

    return render_template(
        "register.html",
        name=request.form.get("name", ""),
        email=request.form.get("email", ""),
        role=request.form.get("role", request.args.get("role", "customer")),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        connection = get_db_connection()
        try:
            user = connection.execute(
                "SELECT id, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        finally:
            connection.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Email or password is incorrect.", "error")
        else:
            clear_auth_session()
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))

    return render_template("login.html", email=request.form.get("email", ""))


@app.route("/profile")
def profile():
    if g.user is None:
        flash("Please log in to view your profile.", "error")
        return redirect(url_for("login"))
    return render_template("profile.html", user=g.user)


@app.route("/logout", methods=["POST"])
def logout():
    clear_auth_session()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

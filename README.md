# LocalMart

LocalMart is a Flask app for browsing local businesses and their demo product
catalogs, creating customer or seller accounts, and viewing an account profile.

## Run locally

From this directory, install the dependencies and start the development server:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The SQLite database is
created at `database.db` when the app starts. Registration signs the new user
in and opens their profile. Existing users can log in at `/login`.

Category pages show the businesses and products for that category. On a
business page, select products and quantities to add them to the session cart;
the cart supports quantity updates, removal, and clearing. Demo products do
not have prices or checkout.

Business pages embed OpenStreetMap and link to a full map. Map pins are
reference locations in Bommanahalli, not verified addresses for the demo
businesses. An internet connection is required to load the map.

Set `LOCALMART_SECRET_KEY` to a private random value when running outside local
development.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

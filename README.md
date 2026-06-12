# E-Commerce Web Application

A full-featured Python and Flask-based E-Commerce web application powered by MongoDB. It provides a complete shopping experience including user authentication, product browsing, shopping cart, checkout, order history, and an administrative dashboard.

## 🚀 Features

### User Experience
* **Authentication:** Secure user registration, login, logout, and password reset.
* **Profile Management:** Users can save and update their delivery address natively in their profile.
* **Dynamic Category Navigation:** A sleek, responsive horizontal category carousel with custom-mapped product emojis and icons.
* **Wishlist:** Users can save their favorite items to a personal wishlist.
* **Shopping Cart:** Add, remove, and adjust quantities of products before checkout.
* **Checkout System:** Secure checkout flow requiring a saved delivery address. Supports Cash on Delivery (COD) and Online Payment simulation.
* **Order Tracking:** Detailed order history and dynamic invoice generation.

### Admin Capabilities
* **Admin Dashboard:** Overview of total products, orders, and system metrics.
* **Product Management:** Add, edit, and delete products directly from the dashboard.
* **Bulk Upload:** Facility to bulk upload products via CSV/JSON.

## 🛠️ Technology Stack

* **Backend:** Python 3.10+, Flask, Flask-Login, Werkzeug
* **Database:** MongoDB Atlas (accessed via PyMongo)
* **Frontend:** HTML5, CSS3 (Vanilla), JavaScript, Jinja2 Templating
* **Icons:** Lucide Icons / Native Emojis

## 📦 Products Data API

The initial catalog of products is dynamically fetched and populated using the **[DummyJSON API](https://dummyjson.com/docs/products)**. 

By running the importer script (`import_mongo.py`), the application automatically pulls up to 200 real-world dummy products across various categories (electronics, smartphones, fashion, groceries, etc.) and seamlessly injects them directly into the MongoDB `products` and `categories` collections.

## ⚙️ Installation & Setup

### 1. Prerequisites
Ensure you have the following installed:
* Python 3.10 or higher
* MongoDB (Local instance or MongoDB Atlas account)

### 2. Setup Virtual Environment
Navigate to the project directory and create a virtual environment:
```bash
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory and add your secret keys and database URI:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secure_secret_key_here
MONGO_URI=mongodb+srv://<username>:<password>@cluster...
```

### 5. Seed the Database
To populate your store with products from the DummyJSON API, run the import script:
```bash
python import_mongo.py
```
*(Optional)* To create default Admin and Customer accounts, run the seed script:
```bash
python seed.py
```

### 6. Run the Application
Start the Flask development server:
```bash
python app.py
```
The application will be accessible at `http://127.0.0.1:5000/`.

## 📂 Project Structure

* `app.py` - Main application entry point and Flask app initialization.
* `routes/` - Contains Blueprint routing modules (`auth.py`, `shop.py`, `cart.py`, `order.py`, `admin.py`, etc.).
* `models/` - Contains database interaction logic and data modeling classes (`user.py`, `product.py`, `cart.py`, etc.).
* `templates/` - Jinja2 HTML templates divided by feature.
* `static/` - CSS styles (`style.css`), JavaScript, and static assets.
* `import_mongo.py` - Fetches product data from DummyJSON API.
* `seed.py` - Seeds default users (admin & customer).

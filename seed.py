import os
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
import certifi
from datetime import datetime, timezone
import random
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ecommerce')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_default_database()

# Clear existing data
print("Clearing database...")
db.users.delete_many({})
db.categories.delete_many({})
db.products.delete_many({})
db.carts.delete_many({})
db.cart_items.delete_many({})
db.wishlist.delete_many({})
db.orders.delete_many({})
db.order_items.delete_many({})
db.payments.delete_many({})

print("Creating categories...")
categories_data = [
    {'name': 'Electronics', 'description': 'Gadgets and devices', 'image': '💻'},
    {'name': 'Clothing', 'description': 'Fashion and apparel', 'image': '👕'},
    {'name': 'Home & Kitchen', 'description': 'For your house', 'image': '🏠'},
    {'name': 'Books', 'description': 'Read and learn', 'image': '📚'},
    {'name': 'Sports', 'description': 'Stay active', 'image': '⚽'},
    {'name': 'Beauty', 'description': 'Skincare and makeup', 'image': '💄'},
    {'name': 'Toys', 'description': 'For kids', 'image': '🧸'},
    {'name': 'Groceries', 'description': 'Daily needs', 'image': '🛒'},
]

category_ids = {}
for c in categories_data:
    result = db.categories.insert_one({
        'name': c['name'],
        'description': c['description'],
        'created_at': datetime.now(timezone.utc)
    })
    category_ids[c['name']] = result.inserted_id

print("Creating users...")
db.users.insert_one({
    'username': 'admin',
    'email': 'admin@shop.com',
    'password_hash': generate_password_hash('admin123'),
    'full_name': 'Admin User',
    'phone': '1234567890',
    'address': 'Admin Street',
    'role': 'admin',
    'created_at': datetime.now(timezone.utc)
})

db.users.insert_one({
    'username': 'customer',
    'email': 'john@example.com',
    'password_hash': generate_password_hash('customer123'),
    'full_name': 'John Doe',
    'phone': '9876543210',
    'address': '123 Main St',
    'role': 'customer',
    'created_at': datetime.now(timezone.utc)
})

print("Creating products...")
products_data = [
    ('Smartphone X', 'Latest smartphone', 69999, 79999, 'Electronics', True),
    ('Laptop Pro', 'Powerful laptop for professionals', 129999, 149999, 'Electronics', True),
    ('Wireless Earbuds', 'Noise cancelling', 14999, 19999, 'Electronics', False),
    ('Smartwatch Series 5', 'Fitness tracker', 24999, 29999, 'Electronics', True),
    ('Men\'s T-Shirt', 'Cotton casual t-shirt', 999, 1499, 'Clothing', False),
    ('Women\'s Jeans', 'Slim fit denim', 1999, 2999, 'Clothing', False),
    ('Winter Jacket', 'Warm and cozy', 4999, 6999, 'Clothing', True),
    ('Coffee Maker', 'Automatic espresso machine', 8999, 11999, 'Home & Kitchen', False),
    ('Non-Stick Cookware', 'Set of 5 pans', 3499, 4999, 'Home & Kitchen', False),
    ('Python Crash Course', 'Learn Python programming', 1499, 1999, 'Books', True),
    ('Clean Code', 'A Handbook of Agile Software Craftsmanship', 2499, 2999, 'Books', False),
    ('Yoga Mat', 'Anti-slip exercise mat', 899, 1299, 'Sports', False),
    ('Dumbbell Set', 'Adjustable weights 20kg', 4999, 6999, 'Sports', True),
    ('Face Wash', 'Organic face cleanser', 499, 699, 'Beauty', False),
    ('Moisturizer', 'Hydrating skin cream', 799, 999, 'Beauty', False),
    ('Lego City', 'Building blocks set', 3999, 4999, 'Toys', True),
    ('Action Figure', 'Superhero collectible', 1499, 1999, 'Toys', False),
    ('Organic Honey', 'Pure raw honey 500g', 399, 499, 'Groceries', False),
    ('Almonds', 'Premium quality 1kg', 1199, 1499, 'Groceries', False),
    ('Green Tea', '100 tea bags', 449, 599, 'Groceries', False),
    ('Gaming Mouse', 'RGB optical mouse', 2499, 3499, 'Electronics', False),
    ('Mechanical Keyboard', 'Blue switches', 5999, 7999, 'Electronics', True),
    ('Running Shoes', 'Lightweight sports shoes', 3499, 4999, 'Clothing', True),
    ('Sunglasses', 'UV protection', 1299, 1999, 'Clothing', False),
    ('Blender', 'High speed smoothie maker', 4499, 5999, 'Home & Kitchen', False),
    ('Fantasy Novel', 'Bestselling fiction', 599, 799, 'Books', False),
    ('Tennis Racket', 'Professional grade', 8999, 10999, 'Sports', False),
    ('Lipstick Set', 'Matte finish 3 shades', 1499, 1999, 'Beauty', False),
    ('Board Game', 'Family strategy game', 2499, 3499, 'Toys', True),
    ('Olive Oil', 'Extra virgin 1L', 999, 1299, 'Groceries', False),
]

for p in products_data:
    name, desc, price, comp_price, cat_name, featured = p
    db.products.insert_one({
        'name': name,
        'description': desc,
        'price': float(price),
        'compare_price': float(comp_price),
        'stock': random.randint(10, 100),
        'image_url': f"https://placehold.co/600x600/1A1A2E/6C5CE7?text={name[:15].replace(' ', '+')}",
        'category_id': category_ids[cat_name],
        'featured': featured,
        'rating': round(random.uniform(3.5, 5.0), 1),
        'created_at': datetime.now(timezone.utc)
    })

print("Database seeded successfully!")

import requests
from pymongo import MongoClient
from datetime import datetime, timezone

# MongoDB Atlas URI
MONGO_URI = "mongodb+srv://2022062514_db_user:password1234@cluster0.oolrijk.mongodb.net/ecommerce?appName=Cluster0"

# Database Name
DB_NAME = "ecommerce"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Fetch products from DummyJSON
url = "https://dummyjson.com/products?limit=200"

response = requests.get(url)

if response.status_code != 200:
    print("Failed to fetch products")
    exit()

products = response.json()["products"]

print(f"Found {len(products)} products")

# Create category cache
category_ids = {}

for product in products:

    category_name = product["category"]

    # Create category if not exists
    category = db.categories.find_one({"name": category_name})

    if not category:
        result = db.categories.insert_one({
            "name": category_name,
            "created_at": datetime.now(timezone.utc)
        })

        category_ids[category_name] = result.inserted_id
    else:
        category_ids[category_name] = category["_id"]

    # Skip duplicate products
    existing = db.products.find_one({
        "name": product["title"]
    })

    if existing:
        print(f"Skipped: {product['title']}")
        continue

    db.products.insert_one({
        "name": product["title"],
        "description": product["description"],
        "price": float(product["price"]),
        "compare_price": float(product["price"] * 1.15),
        "stock": product["stock"],
        "image_url": product["thumbnail"],
        "category_id": category_ids[category_name],
        "featured": product["rating"] >= 4.5,
        "rating": float(product["rating"]),
        "created_at": datetime.now(timezone.utc)
    })

    print(f"Inserted: {product['title']}")

print("Import completed successfully!")
print("Total Products:", db.products.count_documents({}))
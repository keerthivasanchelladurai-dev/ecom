from datetime import datetime, timezone
from bson import ObjectId


def create_product(db, name, description, price, category_id, stock=100,
                   compare_price=0, image_url='', featured=False, rating=4.0):
    """Insert a new product."""
    doc = {
        'name': name,
        'description': description,
        'price': float(price),
        'compare_price': float(compare_price),
        'stock': int(stock),
        'image_url': image_url,
        'category_id': ObjectId(category_id) if category_id else None,
        'featured': featured,
        'rating': float(rating),
        'created_at': datetime.now(timezone.utc),
    }
    result = db.products.insert_one(doc)
    doc['_id'] = result.inserted_id
    return doc


def get_products(db, query=None, category_id=None, sort='newest', page=1, per_page=12, featured_only=False):
    """Return paginated products with optional search/filter/sort."""
    filters = {}

    if query:
        filters['name'] = {'$regex': query, '$options': 'i'}

    if category_id:
        filters['category_id'] = ObjectId(category_id)

    if featured_only:
        filters['featured'] = True

    sort_map = {
        'newest': ('created_at', -1),
        'price_low': ('price', 1),
        'price_high': ('price', -1),
        'rating': ('rating', -1),
        'name': ('name', 1),
    }
    sort_field, sort_dir = sort_map.get(sort, ('created_at', -1))

    total = db.products.count_documents(filters)
    skip = (page - 1) * per_page
    products = list(
        db.products.find(filters)
        .sort(sort_field, sort_dir)
        .skip(skip)
        .limit(per_page)
    )

    return products, total


def get_product_by_id(db, product_id):
    """Return a single product."""
    return db.products.find_one({'_id': ObjectId(product_id)})


def get_related_products(db, product, limit=4):
    """Return related products in the same category."""
    return list(
        db.products.find({
            'category_id': product.get('category_id'),
            '_id': {'$ne': product['_id']}
        }).limit(limit)
    )


def update_product(db, product_id, data):
    """Update a product."""
    if 'price' in data:
        data['price'] = float(data['price'])
    if 'compare_price' in data:
        data['compare_price'] = float(data['compare_price'])
    if 'stock' in data:
        data['stock'] = int(data['stock'])
    if 'rating' in data:
        data['rating'] = float(data['rating'])
    if 'category_id' in data and data['category_id']:
        data['category_id'] = ObjectId(data['category_id'])
    db.products.update_one({'_id': ObjectId(product_id)}, {'$set': data})


def delete_product(db, product_id):
    """Delete a product."""
    db.products.delete_one({'_id': ObjectId(product_id)})

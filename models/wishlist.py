from bson import ObjectId
from datetime import datetime, timezone


def toggle_wishlist(db, user_id, product_id):
    """Add or remove a product from the wishlist. Returns True if added."""
    existing = db.wishlist.find_one({
        'user_id': ObjectId(user_id),
        'product_id': ObjectId(product_id),
    })
    if existing:
        db.wishlist.delete_one({'_id': existing['_id']})
        return False
    else:
        db.wishlist.insert_one({
            'user_id': ObjectId(user_id),
            'product_id': ObjectId(product_id),
            'added_at': datetime.now(timezone.utc),
        })
        return True


def get_wishlist_items(db, user_id):
    """Return wishlist items with product details."""
    items = list(db.wishlist.find({'user_id': ObjectId(user_id)}).sort('added_at', -1))
    enriched = []
    for item in items:
        product = db.products.find_one({'_id': item['product_id']})
        if product:
            item['product'] = product
            enriched.append(item)
        else:
            db.wishlist.delete_one({'_id': item['_id']})
    return enriched


def is_in_wishlist(db, user_id, product_id):
    """Check if a product is in the user's wishlist."""
    return db.wishlist.find_one({
        'user_id': ObjectId(user_id),
        'product_id': ObjectId(product_id),
    }) is not None


def get_wishlist_product_ids(db, user_id):
    """Return a set of product_id strings that are in the user's wishlist."""
    items = db.wishlist.find({'user_id': ObjectId(user_id)}, {'product_id': 1})
    return {str(item['product_id']) for item in items}

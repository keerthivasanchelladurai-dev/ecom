from bson import ObjectId
from datetime import datetime, timezone


def get_or_create_cart(db, user_id):
    """Get existing cart or create a new one for the user."""
    cart = db.carts.find_one({'user_id': ObjectId(user_id)})
    if not cart:
        cart = {
            'user_id': ObjectId(user_id),
            'created_at': datetime.now(timezone.utc),
        }
        result = db.carts.insert_one(cart)
        cart['_id'] = result.inserted_id
    return cart


def add_to_cart(db, user_id, product_id, quantity=1):
    """Add a product to the user's cart, or increment quantity."""
    cart = get_or_create_cart(db, user_id)
    existing = db.cart_items.find_one({
        'cart_id': cart['_id'],
        'product_id': ObjectId(product_id),
    })
    if existing:
        db.cart_items.update_one(
            {'_id': existing['_id']},
            {'$inc': {'quantity': quantity}}
        )
    else:
        db.cart_items.insert_one({
            'cart_id': cart['_id'],
            'product_id': ObjectId(product_id),
            'quantity': quantity,
        })


def update_cart_item(db, item_id, quantity):
    """Update the quantity of a cart item."""
    if quantity <= 0:
        db.cart_items.delete_one({'_id': ObjectId(item_id)})
    else:
        db.cart_items.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': {'quantity': quantity}}
        )


def remove_cart_item(db, item_id):
    """Remove an item from the cart."""
    db.cart_items.delete_one({'_id': ObjectId(item_id)})


def get_cart_items(db, user_id):
    """Return all cart items with product details for a user."""
    cart = db.carts.find_one({'user_id': ObjectId(user_id)})
    if not cart:
        return [], 0

    items = list(db.cart_items.find({'cart_id': cart['_id']}))
    enriched = []
    total = 0
    for item in items:
        product = db.products.find_one({'_id': item['product_id']})
        if product:
            item['product'] = product
            item['subtotal'] = product['price'] * item['quantity']
            total += item['subtotal']
            enriched.append(item)
        else:
            # Product was deleted — clean up
            db.cart_items.delete_one({'_id': item['_id']})

    return enriched, total


def clear_cart(db, user_id):
    """Remove all items from a user's cart."""
    cart = db.carts.find_one({'user_id': ObjectId(user_id)})
    if cart:
        db.cart_items.delete_many({'cart_id': cart['_id']})

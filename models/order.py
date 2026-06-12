from bson import ObjectId
from datetime import datetime, timezone
import random
import string


def _generate_order_number():
    """Generate a human-readable order number like ORD-AB12CD."""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=6))
    return f"ORD-{code}"


def create_order(db, user_id, items, total, shipping_address, payment_method='cod'):
    """Create a new order with its items."""
    order = {
        'order_number': _generate_order_number(),
        'user_id': ObjectId(user_id),
        'total': float(total),
        'status': 'pending',
        'shipping_address': shipping_address,
        'payment_method': payment_method,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }
    result = db.orders.insert_one(order)
    order['_id'] = result.inserted_id

    # Insert order items
    order_items = []
    for item in items:
        oi = {
            'order_id': order['_id'],
            'product_id': item['product']['_id'],
            'product_name': item['product']['name'],
            'product_image': item['product'].get('image_url', ''),
            'quantity': item['quantity'],
            'price': item['product']['price'],
        }
        db.order_items.insert_one(oi)
        order_items.append(oi)

        # Decrease product stock
        db.products.update_one(
            {'_id': item['product']['_id']},
            {'$inc': {'stock': -item['quantity']}}
        )

    return order


def get_user_orders(db, user_id):
    """Return all orders for a user, newest first."""
    return list(
        db.orders.find({'user_id': ObjectId(user_id)}).sort('created_at', -1)
    )


def get_order_by_id(db, order_id):
    """Return a single order."""
    return db.orders.find_one({'_id': ObjectId(order_id)})


def get_order_items(db, order_id):
    """Return all items for an order."""
    return list(db.order_items.find({'order_id': ObjectId(order_id)}))


def update_order_status(db, order_id, status):
    """Update the status of an order."""
    db.orders.update_one(
        {'_id': ObjectId(order_id)},
        {'$set': {'status': status, 'updated_at': datetime.now(timezone.utc)}}
    )


def get_all_orders(db, status=None, page=1, per_page=20):
    """Return all orders (admin), optionally filtered by status."""
    filters = {}
    if status:
        filters['status'] = status
    total = db.orders.count_documents(filters)
    orders = list(
        db.orders.find(filters)
        .sort('created_at', -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    # Attach user info
    for order in orders:
        user = db.users.find_one({'_id': order['user_id']})
        order['user'] = user
    return orders, total

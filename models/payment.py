from bson import ObjectId
from datetime import datetime, timezone
import random
import string


def _generate_transaction_id():
    """Generate a mock transaction ID."""
    chars = string.ascii_uppercase + string.digits
    return 'TXN-' + ''.join(random.choices(chars, k=10))


def create_payment(db, order_id, amount, method='cod'):
    """Create a payment record."""
    payment = {
        'order_id': ObjectId(order_id),
        'amount': float(amount),
        'method': method,
        'status': 'completed' if method == 'cod' else 'pending',
        'transaction_id': _generate_transaction_id(),
        'created_at': datetime.now(timezone.utc),
    }
    result = db.payments.insert_one(payment)
    payment['_id'] = result.inserted_id
    return payment


def complete_payment(db, payment_id):
    """Mark a payment as completed."""
    db.payments.update_one(
        {'_id': ObjectId(payment_id)},
        {'$set': {'status': 'completed'}}
    )


def get_payment_by_order(db, order_id):
    """Get payment for an order."""
    return db.payments.find_one({'order_id': ObjectId(order_id)})

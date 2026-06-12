from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.order import get_order_by_id, update_order_status
from models.payment import get_payment_by_order, complete_payment
from database import get_db

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/payment/<order_id>', methods=['GET', 'POST'])
@login_required
def process_payment(order_id):
    db = get_db()
    order = get_order_by_id(db, order_id)

    if not order or str(order['user_id']) != current_user.id:
        flash('Order not found.', 'danger')
        return redirect(url_for('order.order_history'))

    payment = get_payment_by_order(db, order_id)

    if request.method == 'POST':
        # Mock payment — always succeeds
        if payment:
            complete_payment(db, str(payment['_id']))
        update_order_status(db, order_id, 'confirmed')
        flash('Payment successful! Your order has been confirmed.', 'success')
        return redirect(url_for('order.order_confirmation', order_id=order_id))

    return render_template('payment/payment.html', order=order, payment=payment)

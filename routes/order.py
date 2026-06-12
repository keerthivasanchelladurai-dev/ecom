from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.cart import get_cart_items, clear_cart
from models.order import create_order, get_user_orders, get_order_by_id, get_order_items
from models.payment import create_payment, get_payment_by_order
from app import get_db
from bson import ObjectId
from datetime import datetime, timezone

order_bp = Blueprint('order', __name__)


@order_bp.route('/checkout')
@login_required
def checkout():
    if not getattr(current_user, 'address', None):
        flash('Please save your delivery address in your profile before checking out.', 'warning')
        return redirect(url_for('auth.profile'))

    db = get_db()
    items, total = get_cart_items(db, current_user.id)
    if not items:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('shop.products'))
    return render_template('order/checkout.html', items=items, total=total)


@order_bp.route('/place-order', methods=['POST'])
@login_required
def place_order():
    db = get_db()
    items, total = get_cart_items(db, current_user.id)

    if not items:
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('shop.products'))

    # Gather shipping address
    address = {
        'full_name': request.form.get('full_name', '').strip(),
        'phone': request.form.get('phone', '').strip(),
        'address_line': request.form.get('address_line', '').strip(),
        'city': request.form.get('city', '').strip(),
        'state': request.form.get('state', '').strip(),
        'pincode': request.form.get('pincode', '').strip(),
    }
    payment_method = request.form.get('payment_method', 'cod')

    if not all([address['full_name'], address['phone'], address['address_line'],
                address['city'], address['state'], address['pincode']]):
        flash('Please fill in all shipping details.', 'danger')
        return redirect(url_for('order.checkout'))

    # Create the order
    order = create_order(db, current_user.id, items, total, address, payment_method)

    # Create payment
    payment = create_payment(db, str(order['_id']), total, payment_method)

    # Clear cart
    clear_cart(db, current_user.id)

    if payment_method == 'online':
        return redirect(url_for('payment.process_payment', order_id=str(order['_id'])))

    # COD — confirm immediately
    from models.order import update_order_status
    update_order_status(db, str(order['_id']), 'confirmed')
    flash('Order placed successfully!', 'success')
    return redirect(url_for('order.order_confirmation', order_id=str(order['_id'])))


@order_bp.route('/order/confirmation/<order_id>')
@login_required
def order_confirmation(order_id):
    db = get_db()
    order = get_order_by_id(db, order_id)
    if not order or str(order['user_id']) != current_user.id:
        flash('Order not found.', 'danger')
        return redirect(url_for('order.order_history'))
    items = get_order_items(db, order_id)
    payment = get_payment_by_order(db, order_id)
    return render_template('order/order_confirmation.html', order=order, items=items, payment=payment)


@order_bp.route('/orders')
@login_required
def order_history():
    db = get_db()
    orders = get_user_orders(db, current_user.id)
    for order in orders:
        order['item_count'] = db.order_items.count_documents({'order_id': order['_id']})
    return render_template('order/order_history.html', orders=orders)


@order_bp.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    db = get_db()
    order = get_order_by_id(db, order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('order.order_history'))

    # Allow admin or the order owner to view
    if str(order['user_id']) != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('order.order_history'))

    items = get_order_items(db, order_id)
    payment = get_payment_by_order(db, order_id)
    return render_template('order/order_detail.html', order=order, items=items, payment=payment)


@order_bp.route('/order/<order_id>/invoice')
@login_required
def invoice(order_id):
    db = get_db()
    order = get_order_by_id(db, order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('order.order_history'))

    if str(order['user_id']) != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('order.order_history'))

    items = get_order_items(db, order_id)
    payment = get_payment_by_order(db, order_id)
    return render_template('order/invoice.html', order=order, items=items, payment=payment)

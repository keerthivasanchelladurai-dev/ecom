from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models.cart import add_to_cart, update_cart_item, remove_cart_item, get_cart_items
from database import get_db

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/cart')
@login_required
def view_cart():
    db = get_db()
    items, total = get_cart_items(db, current_user.id)
    return render_template('cart/cart.html', items=items, total=total)


@cart_bp.route('/cart/add/<product_id>', methods=['POST'])
@login_required
def add_item(product_id):
    db = get_db()
    quantity = request.form.get('quantity', 1, type=int)
    add_to_cart(db, current_user.id, product_id, quantity)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items, total = get_cart_items(db, current_user.id)
        count = sum(i['quantity'] for i in items)
        return jsonify({'success': True, 'cart_count': count, 'message': 'Added to cart!'})

    flash('Product added to cart!', 'success')
    return redirect(request.referrer or url_for('shop.home'))


@cart_bp.route('/cart/update/<item_id>', methods=['POST'])
@login_required
def update_item(item_id):
    db = get_db()
    quantity = request.form.get('quantity', 1, type=int)
    update_cart_item(db, item_id, quantity)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items, total = get_cart_items(db, current_user.id)
        count = sum(i['quantity'] for i in items)
        return jsonify({'success': True, 'cart_count': count, 'total': total})

    flash('Cart updated.', 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/remove/<item_id>', methods=['POST'])
@login_required
def remove_item(item_id):
    db = get_db()
    remove_cart_item(db, item_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items, total = get_cart_items(db, current_user.id)
        count = sum(i['quantity'] for i in items)
        return jsonify({'success': True, 'cart_count': count, 'total': total})

    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart.view_cart'))

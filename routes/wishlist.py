from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.wishlist import toggle_wishlist, get_wishlist_items
from database import get_db

wishlist_bp = Blueprint('wishlist', __name__)


@wishlist_bp.route('/wishlist')
@login_required
def view_wishlist():
    db = get_db()
    items = get_wishlist_items(db, current_user.id)
    return render_template('wishlist/wishlist.html', items=items)


@wishlist_bp.route('/wishlist/toggle/<product_id>', methods=['POST'])
@login_required
def toggle(product_id):
    db = get_db()
    added = toggle_wishlist(db, current_user.id, product_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'added': added,
            'message': 'Added to wishlist!' if added else 'Removed from wishlist.'
        })

    flash('Added to wishlist!' if added else 'Removed from wishlist.', 'success' if added else 'info')
    return redirect(request.referrer or url_for('shop.home'))

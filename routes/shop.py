from flask import Blueprint, render_template, request
from flask_login import current_user
from models.product import get_products, get_product_by_id, get_related_products
from models.category import get_all_categories, get_category_by_id
from models.wishlist import get_wishlist_product_ids
from app import get_db
import math

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/')
def home():
    db = get_db()
    featured, _ = get_products(db, featured_only=True, per_page=8)
    categories = get_all_categories(db)
    latest, _ = get_products(db, sort='newest', per_page=8)

    wishlist_ids = set()
    if current_user.is_authenticated:
        wishlist_ids = get_wishlist_product_ids(db, current_user.id)

    return render_template('shop/home.html',
                           featured=featured,
                           categories=categories,
                           latest=latest,
                           wishlist_ids=wishlist_ids)


@shop_bp.route('/products')
def products():
    db = get_db()
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 12

    products_list, total = get_products(
        db, query=query, category_id=category_id or None,
        sort=sort, page=page, per_page=per_page
    )
    categories = get_all_categories(db)
    total_pages = math.ceil(total / per_page) if total else 1

    # Current category name
    current_category = None
    if category_id:
        current_category = get_category_by_id(db, category_id)

    wishlist_ids = set()
    if current_user.is_authenticated:
        wishlist_ids = get_wishlist_product_ids(db, current_user.id)

    return render_template('shop/products.html',
                           products=products_list,
                           categories=categories,
                           current_category=current_category,
                           query=query,
                           sort=sort,
                           page=page,
                           total_pages=total_pages,
                           total=total,
                           wishlist_ids=wishlist_ids)


@shop_bp.route('/product/<product_id>')
def product_detail(product_id):
    db = get_db()
    product = get_product_by_id(db, product_id)
    if not product:
        return render_template('errors/404.html'), 404

    related = get_related_products(db, product)
    category = None
    if product.get('category_id'):
        category = get_category_by_id(db, str(product['category_id']))

    in_wishlist = False
    if current_user.is_authenticated:
        from models.wishlist import is_in_wishlist
        in_wishlist = is_in_wishlist(db, current_user.id, product_id)

    return render_template('shop/product_detail.html',
                           product=product,
                           related=related,
                           category=category,
                           in_wishlist=in_wishlist)

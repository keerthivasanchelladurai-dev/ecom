from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models.product import get_products, get_product_by_id, create_product, update_product, delete_product
from models.category import get_all_categories, get_category_by_id, create_category, update_category, delete_category
from models.order import get_all_orders, get_order_by_id, get_order_items, update_order_status
from models.payment import get_payment_by_order
from database import get_db
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import csv
import io

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to restrict access to admin users."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('shop.home'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ──────────────────────────────────────────────────
@admin_bp.route('/')
@admin_required
def dashboard():
    db = get_db()

    # KPI metrics
    total_products = db.products.count_documents({})
    total_customers = db.users.count_documents({'role': 'customer'})
    total_orders = db.orders.count_documents({})

    # Revenue
    pipeline = [{'$group': {'_id': None, 'total': {'$sum': '$total'}}}]
    rev = list(db.orders.aggregate(pipeline))
    total_revenue = rev[0]['total'] if rev else 0

    # Recent orders
    recent_orders = list(db.orders.find().sort('created_at', -1).limit(5))
    for order in recent_orders:
        user = db.users.find_one({'_id': order['user_id']})
        order['user'] = user

    # Orders by status
    status_pipeline = [{'$group': {'_id': '$status', 'count': {'$sum': 1}}}]
    status_data = {item['_id']: item['count'] for item in db.orders.aggregate(status_pipeline)}

    # Monthly revenue (last 6 months)
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    monthly_pipeline = [
        {'$match': {'created_at': {'$gte': six_months_ago}}},
        {'$group': {
            '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$created_at'}},
            'revenue': {'$sum': '$total'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    monthly_data = list(db.orders.aggregate(monthly_pipeline))

    # Top selling products
    top_pipeline = [
        {'$group': {'_id': '$product_id', 'total_sold': {'$sum': '$quantity'}, 'revenue': {'$sum': {'$multiply': ['$price', '$quantity']}}}},
        {'$sort': {'total_sold': -1}},
        {'$limit': 5}
    ]
    top_products_raw = list(db.order_items.aggregate(top_pipeline))
    top_products = []
    for tp in top_products_raw:
        product = db.products.find_one({'_id': tp['_id']})
        if product:
            tp['product'] = product
            top_products.append(tp)

    # Category distribution
    cat_pipeline = [
        {'$group': {'_id': '$category_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]
    cat_data_raw = list(db.products.aggregate(cat_pipeline))
    cat_data = []
    for cd in cat_data_raw:
        cat = db.categories.find_one({'_id': cd['_id']}) if cd['_id'] else None
        cat_data.append({
            'name': cat['name'] if cat else 'Uncategorized',
            'count': cd['count']
        })

    return render_template('admin/dashboard.html',
                           total_products=total_products,
                           total_customers=total_customers,
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           recent_orders=recent_orders,
                           status_data=status_data,
                           monthly_data=monthly_data,
                           top_products=top_products,
                           cat_data=cat_data)


# ── Products Management ───────────────────────────────────────
@admin_bp.route('/products')
@admin_required
def products():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    query = request.args.get('q', '').strip()
    products_list, total = get_products(db, query=query or None, page=page, per_page=20)
    categories = get_all_categories(db)

    # Attach category names
    cat_map = {str(c['_id']): c['name'] for c in categories}
    for p in products_list:
        p['category_name'] = cat_map.get(str(p.get('category_id', '')), 'N/A')

    import math
    total_pages = math.ceil(total / 20) if total else 1
    return render_template('admin/products.html',
                           products=products_list, total=total,
                           page=page, total_pages=total_pages, query=query)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    db = get_db()
    categories = get_all_categories(db)

    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'price': request.form.get('price', 0),
            'compare_price': request.form.get('compare_price', 0),
            'stock': request.form.get('stock', 0),
            'image_url': request.form.get('image_url', '').strip(),
            'featured': request.form.get('featured') == 'on',
            'rating': request.form.get('rating', 4.0),
        }
        category_id = request.form.get('category_id', '')

        if not data['name'] or not data['price']:
            flash('Name and price are required.', 'danger')
            return render_template('admin/product_form.html', categories=categories, product=None)

        create_product(db, category_id=category_id, **data)
        flash('Product created successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', categories=categories, product=None)


@admin_bp.route('/products/bulk-upload', methods=['GET', 'POST'])
@admin_required
def bulk_upload_products():
    db = get_db()
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
            
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file.', 'danger')
            return redirect(request.url)
            
        try:
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            
            success_count = 0
            for row in csv_input:
                name = row.get('Name', '').strip()
                if not name:
                    continue
                    
                price = row.get('Price', 0)
                try:
                    price = float(price)
                except ValueError:
                    price = 0.0
                    
                compare_price = row.get('Compare Price', 0)
                try:
                    compare_price = float(compare_price)
                except ValueError:
                    compare_price = 0.0
                    
                stock = row.get('Stock', 0)
                try:
                    stock = int(stock)
                except ValueError:
                    stock = 0
                    
                featured = str(row.get('Featured', '')).lower() in ['true', 'yes', '1', 'y']
                
                cat_name = row.get('Category Name', '').strip()
                category_id = None
                if cat_name:
                    # Find or create category
                    cat = db.categories.find_one({'name': {'$regex': f'^{cat_name}$', '$options': 'i'}})
                    if cat:
                        category_id = str(cat['_id'])
                    else:
                        from models.category import create_category
                        new_cat = create_category(db, cat_name)
                        category_id = str(new_cat['_id'])
                        
                create_product(
                    db,
                    category_id=category_id,
                    name=name,
                    description=row.get('Description', '').strip(),
                    price=price,
                    compare_price=compare_price,
                    stock=stock,
                    image_url=row.get('Image URL', '').strip(),
                    featured=featured,
                    rating=4.0
                )
                success_count += 1
                
            flash(f'Successfully imported {success_count} products!', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(request.url)
            
    return render_template('admin/bulk_upload.html')


@admin_bp.route('/products/<product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    product = get_product_by_id(db, product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.products'))

    categories = get_all_categories(db)

    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'price': request.form.get('price', 0),
            'compare_price': request.form.get('compare_price', 0),
            'stock': request.form.get('stock', 0),
            'image_url': request.form.get('image_url', '').strip(),
            'category_id': request.form.get('category_id', ''),
            'featured': request.form.get('featured') == 'on',
            'rating': request.form.get('rating', 4.0),
        }

        update_product(db, product_id, data)
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', categories=categories, product=product)


@admin_bp.route('/products/<product_id>/delete', methods=['POST'])
@admin_required
def delete_product_route(product_id):
    db = get_db()
    delete_product(db, product_id)
    flash('Product deleted.', 'info')
    return redirect(url_for('admin.products'))


# ── Categories Management ─────────────────────────────────────
@admin_bp.route('/categories')
@admin_required
def categories():
    db = get_db()
    cats = get_all_categories(db)
    # Count products per category
    for cat in cats:
        cat['product_count'] = db.products.count_documents({'category_id': cat['_id']})
    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    if request.method == 'POST':
        db = get_db()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        if not name:
            flash('Category name is required.', 'danger')
            return render_template('admin/category_form.html', category=None)
        create_category(db, name, description, image_url)
        flash('Category created!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=None)


@admin_bp.route('/categories/<category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    db = get_db()
    cat = get_category_by_id(db, category_id)
    if not cat:
        flash('Category not found.', 'danger')
        return redirect(url_for('admin.categories'))

    if request.method == 'POST':
        data = {
            'name': request.form.get('name', '').strip(),
            'description': request.form.get('description', '').strip(),
            'image_url': request.form.get('image_url', '').strip(),
        }
        update_category(db, category_id, data)
        flash('Category updated!', 'success')
        return redirect(url_for('admin.categories'))

    return render_template('admin/category_form.html', category=cat)


@admin_bp.route('/categories/<category_id>/delete', methods=['POST'])
@admin_required
def delete_category_route(category_id):
    db = get_db()
    delete_category(db, category_id)
    flash('Category deleted.', 'info')
    return redirect(url_for('admin.categories'))


# ── Customers ─────────────────────────────────────────────────
@admin_bp.route('/customers')
@admin_required
def customers():
    db = get_db()
    customer_list = list(db.users.find({'role': 'customer'}).sort('created_at', -1))
    for c in customer_list:
        c['order_count'] = db.orders.count_documents({'user_id': c['_id']})
    return render_template('admin/customers.html', customers=customer_list)


# ── Orders Management ─────────────────────────────────────────
@admin_bp.route('/orders')
@admin_required
def orders():
    db = get_db()
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    orders_list, total = get_all_orders(db, status=status_filter or None, page=page)
    import math
    total_pages = math.ceil(total / 20) if total else 1
    return render_template('admin/orders.html',
                           orders=orders_list, total=total,
                           page=page, total_pages=total_pages,
                           status_filter=status_filter)


@admin_bp.route('/orders/<order_id>')
@admin_required
def order_detail(order_id):
    db = get_db()
    order = get_order_by_id(db, order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('admin.orders'))
    items = get_order_items(db, order_id)
    payment = get_payment_by_order(db, order_id)
    user = db.users.find_one({'_id': order['user_id']})
    order['user'] = user
    return render_template('admin/order_detail.html', order=order, items=items, payment=payment)


@admin_bp.route('/orders/<order_id>/update-status', methods=['POST'])
@admin_required
def update_status(order_id):
    db = get_db()
    new_status = request.form.get('status', '')
    if new_status in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']:
        update_order_status(db, order_id, new_status)
        flash(f'Order status updated to {new_status}.', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))


# ── Analytics API ──────────────────────────────────────────────
@admin_bp.route('/api/analytics')
@admin_required
def analytics_api():
    db = get_db()

    # Daily orders (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    daily_pipeline = [
        {'$match': {'created_at': {'$gte': thirty_days_ago}}},
        {'$group': {
            '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}},
            'revenue': {'$sum': '$total'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    daily_data = list(db.orders.aggregate(daily_pipeline))

    return jsonify({
        'daily': daily_data,
    })

from flask import Flask, render_template
from flask_login import LoginManager
from pymongo import MongoClient
from config import Config
import certifi

# ── Global Extensions ──────────────────────────────────────────
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

mongo_client = None
db = None


def get_db():
    """Return the MongoDB database instance."""
    from flask import current_app
    return current_app.mongo_db


def create_app():
    """Application factory."""
    global mongo_client, db

    app = Flask(__name__)
    app.config.from_object(Config)

    # ── MongoDB Atlas Connection ───────────────────────────────
    mongo_client = MongoClient(app.config['MONGO_URI'], tlsCAFile=certifi.where())
    db = mongo_client["ecommerce"]
    app.mongo_client = mongo_client
    app.mongo_db = db

    # ── Flask-Login ────────────────────────────────────────────
    login_manager.init_app(app)

    from models.user import load_user_by_id
    login_manager.user_loader(load_user_by_id)

    # ── Register Blueprints ────────────────────────────────────
    from routes.auth import auth_bp
    from routes.shop import shop_bp
    from routes.cart import cart_bp
    from routes.wishlist import wishlist_bp
    from routes.order import order_bp
    from routes.payment import payment_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)

    # ── Context Processors ───────────────────────────────────────
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        count = 0
        if current_user.is_authenticated:
            from bson import ObjectId
            cart = db.carts.find_one({'user_id': ObjectId(current_user.id)})
            if cart:
                items = list(db.cart_items.find({'cart_id': cart['_id']}))
                count = sum(i.get('quantity', 0) for i in items)
                
        # Fetch all categories globally
        from models.category import get_all_categories
        all_categories = get_all_categories(db)
        
        return dict(cart_count=count, all_categories=all_categories)

    # ── Error Handlers ─────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # ── Create Indexes ─────────────────────────────────────────
    with app.app_context():
        _ensure_indexes(db)

    return app


def _ensure_indexes(database):
    """Create MongoDB indexes for performance."""
    database.users.create_index('email', unique=True)
    database.products.create_index('name')
    database.products.create_index('category_id')
    database.cart_items.create_index('cart_id')
    database.order_items.create_index('order_id')
    database.wishlist.create_index([('user_id', 1), ('product_id', 1)], unique=True)


# ── Global App Instance for Gunicorn ───────────────────────────
app = create_app()

# ── Run ────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models.user import User, create_user, find_user_by_email
from database import get_db
from bson import ObjectId

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('shop.home'))

    if request.method == 'POST':
        db = get_db()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()

        # Validation
        errors = []
        if not username or not email or not password:
            errors.append('All required fields must be filled.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if db.users.find_one({'email': email.lower()}):
            errors.append('Email already registered.')
        if db.users.find_one({'username': username}):
            errors.append('Username already taken.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register.html')

        user = create_user(db, username, email, password, full_name, phone)
        login_user(user)
        flash('Account created successfully! Welcome aboard.', 'success')
        return redirect(url_for('shop.home'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('shop.home'))

    if request.method == 'POST':
        db = get_db()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = find_user_by_email(db, email)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Welcome back!', 'success')
            next_page = request.args.get('next')
            if user.is_admin:
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('shop.home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('shop.home'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    if request.method == 'POST':
        address = request.form.get('address', '').strip()
        if address:
            db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'address': address}})
            current_user._doc['address'] = address
            flash('Address updated successfully.', 'success')
        else:
            flash('Address cannot be empty.', 'danger')
        return redirect(url_for('auth.profile'))

    total_orders = db.orders.count_documents({'user_id': ObjectId(current_user.id)})
    return render_template('auth/profile.html', total_orders=total_orders)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        db = get_db()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')

        if not email or not new_password:
            flash('All fields are required.', 'danger')
            return render_template('auth/reset_password.html')

        if new_password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html')

        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/reset_password.html')

        user_doc = db.users.find_one({'email': email.lower()})
        if not user_doc:
            flash('No account found with that email.', 'danger')
            return render_template('auth/reset_password.html')

        db.users.update_one(
            {'_id': user_doc['_id']},
            {'$set': {'password_hash': generate_password_hash(new_password)}}
        )
        flash('Password reset successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')

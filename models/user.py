from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime, timezone


class User(UserMixin):
    """Wrapper around a MongoDB user document to work with Flask-Login."""

    def __init__(self, user_doc):
        self._doc = user_doc

    @property
    def id(self):
        return str(self._doc['_id'])

    @property
    def email(self):
        return self._doc.get('email', '')

    @property
    def username(self):
        return self._doc.get('username', '')

    @property
    def full_name(self):
        return self._doc.get('full_name', '')

    @property
    def phone(self):
        return self._doc.get('phone', '')

    @property
    def address(self):
        return self._doc.get('address', '')

    @property
    def role(self):
        return self._doc.get('role', 'customer')

    @property
    def created_at(self):
        return self._doc.get('created_at', datetime.now(timezone.utc))

    @property
    def is_admin(self):
        return self.role == 'admin'

    def check_password(self, password):
        return check_password_hash(self._doc.get('password_hash', ''), password)

    def to_dict(self):
        return self._doc


def load_user_by_id(user_id):
    """Flask-Login user loader callback."""
    from app import get_db
    db = get_db()
    try:
        user_doc = db.users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return None
    if user_doc:
        return User(user_doc)
    return None


def create_user(db, username, email, password, full_name='', phone='', address='', role='customer'):
    """Insert a new user into MongoDB and return the User wrapper."""
    user_doc = {
        'username': username,
        'email': email.lower().strip(),
        'password_hash': generate_password_hash(password),
        'full_name': full_name,
        'phone': phone,
        'address': address,
        'role': role,
        'created_at': datetime.now(timezone.utc),
    }
    result = db.users.insert_one(user_doc)
    user_doc['_id'] = result.inserted_id
    return User(user_doc)


def find_user_by_email(db, email):
    """Find a user by email address."""
    doc = db.users.find_one({'email': email.lower().strip()})
    return User(doc) if doc else None

from datetime import datetime, timezone


def create_category(db, name, description='', image_url=''):
    """Insert a new category."""
    doc = {
        'name': name,
        'description': description,
        'image_url': image_url,
        'created_at': datetime.now(timezone.utc),
    }
    result = db.categories.insert_one(doc)
    doc['_id'] = result.inserted_id
    return doc


def get_all_categories(db):
    """Return all categories."""
    return list(db.categories.find().sort('name', 1))


def get_category_by_id(db, category_id):
    """Return a single category by its ObjectId."""
    from bson import ObjectId
    return db.categories.find_one({'_id': ObjectId(category_id)})


def update_category(db, category_id, data):
    """Update a category."""
    from bson import ObjectId
    db.categories.update_one({'_id': ObjectId(category_id)}, {'$set': data})


def delete_category(db, category_id):
    """Delete a category."""
    from bson import ObjectId
    db.categories.delete_one({'_id': ObjectId(category_id)})

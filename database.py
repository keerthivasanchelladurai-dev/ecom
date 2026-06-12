from flask import current_app

def get_db():
    """Return the MongoDB database instance."""
    return current_app.mongo_db

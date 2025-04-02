from flask import Blueprint, jsonify
from .models import TestDoc
from mongoengine.connection import get_db

test_db_bp = Blueprint('testdb_connection', __name__)


@test_db_bp.route('/test_db', methods=['GET'])
def test_db_connection():
    try:
        # Get the database and list collections
        db = get_db()
        collections = db.list_collection_names()

        # Insert a test document
        test_doc = TestDoc(name="Test Document2", value=2)
        test_doc.save()

        # Return a JSON response with details
        return jsonify({
            "message": "Database connection successful.",
            "collections": collections,
            "inserted_document": test_doc.to_json()
        })
    except Exception as e:
        return jsonify({
            "error": "Error connecting to the database",
            "details": str(e)
        }), 500
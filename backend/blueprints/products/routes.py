from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from mongoengine.errors import ValidationError as MongoValidationError
from marshmallow import ValidationError
from .models import Product
from backend.schemas.product_schema import ProductSchema
from backend.app import limiter

products_bp = Blueprint('products', __name__)
product_schema = ProductSchema()

# FETCHING ALL PRODUCTS with Pagination  #
#----------------------------------------#
@products_bp.get('/all_products')
@limiter.limit("5 per minute")
def get_all_products():
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=5, type=int)

    # Calculate skip count for pagination
    skip = (page - 1) * per_page

    products = Product.objects.skip(skip).limit(per_page)
    products_list = [p.to_json() for p in products]

    total = Product.objects.count()
    total_pages = (total + per_page - 1)//per_page

    return jsonify({
        "page":page,
        "per_page":per_page,
        "total":total,
        "total_pages":total_pages,
        "products":products_list
    }), 200


# CREATE PRODUCT with JWT Auth & RBAC  #
#---------------------------------------#
@products_bp.post('/create_product')
@limiter.limit("3 per minute")
@jwt_required()
def create_product():
    claims = get_jwt()

    if claims['role'] != 'admin':
        return jsonify({"message": "Only admins can create products"}), 403
    
    json_data = request.get_json()
    try:
        # validate and deserialize input using the schema
        data = product_schema.load(json_data)
    except ValidationError as err:
        return jsonify({
            "message": "Invalid input", 
            "errors": err.messages
            }), 400
    
    try:
        # create a new product document
        product = Product(**data).save()
        return jsonify({
            "message": "Product created successfully"
            }), 201
    except MongoValidationError as e:
        return jsonify({
            "message": "Database validation error",
            "errors": str(e)
        }), 400
    

# READ PRODUCT #
#--------------#
@products_bp.get('/<product_id>')
@limiter.limit("10 per minute")
def read_product(product_id):
    try:
        product = Product.objects.get(id=product_id)
        return jsonify(product.to_json()), 200
    except Product.DoesNotExist:
        return jsonify({"message": "Product not found"}), 404


# UPDATE PRODUCT with JWT Auth & RBAC  #
#---------------------------------------#
@products_bp.put('/update_product/<product_id>')
@limiter.limit("3 per minute") 
@jwt_required()
def update_product(product_id):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"message": "Only admins can update products"}), 403

    json_data = request.get_json()
    try:
        # Allow partial updates by setting partial=True
        data = product_schema.load(json_data, partial=True)
    except ValidationError as err:
        return jsonify({
            "message": "Invalid input",
            "errors": err.messages
        }), 400

    try:
        product = Product.objects.get(id=product_id)
        product.update(**data)
        product.reload()  # Refresh product data after update
        return jsonify({
            "message": "Product updated successfully",
            "product": product.to_json()
        }), 200
    except Product.DoesNotExist:
        return jsonify({"message": "Product not found"}), 404
    except MongoValidationError as e:
        return jsonify({
            "message": "Database validation error",
            "errors": str(e)
        }), 400


# DELETE PRODUCT #
#----------------#
@products_bp.delete('/delete_product/<product_id>')
@limiter.limit("2 per minute")
@jwt_required()
def delete_product(product_id):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"message": "Only admins can delete products"}), 403

    try:
        product = Product.objects.get(id=product_id)
        product.delete()
        return jsonify({"message": "Product deleted successfully"}), 200
    except Product.DoesNotExist:
        return jsonify({"message": "Product not found"}), 404

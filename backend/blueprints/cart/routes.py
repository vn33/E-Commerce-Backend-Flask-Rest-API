from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from .models import Cart, CartItem
from backend.blueprints.products.models import Product
from decimal import Decimal
from backend.app import limiter

cart_bp = Blueprint('cart', __name__)

# Getting the cart for a specifix user
@cart_bp.get('/details')
@limiter.limit("5 per minute")
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart = Cart.objects(user_id=user_id).first()
    if not cart or not cart.items:
        return jsonify({"message": "Cart is empty"}), 200
    return jsonify(cart.to_json()), 200

@cart_bp.post('/add_item')
@limiter.limit("5 per minute")
@jwt_required()
def add_to_cart():
    data = request.get_json()
    user_id = get_jwt_identity()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    price = data.get('price') # optional: price may be provided in payload

    if not product_id:
        return jsonify({
            "message": "Product ID is required"
        }), 400
    
    # If price is not provided, attempt to fetch it from the Product model
    if price is None:
        try:
            product = Product.objects.get(id=product_id)
            price = product.variants[0].price if product.variants else None
            if price is None:
                return jsonify({"message": "Product has no price"}), 400
        except Exception as e:
            return jsonify({
                "message": "Failed to fetch product price",
                "details": str(e)
                }), 400
    else:
        try:
            price = Decimal(str(price))
        except Exception as e:
            return jsonify({"message": "Invalid price format", "details": str(e)}), 400
        
    cart = Cart.objects(user_id=user_id).first()
    if not cart:
        # creating a new cart if one does not exist for the user
        cart = Cart(user_id=user_id, items=[])

    # check if the product already exists for the user
    for item in cart.items:
        if item.product_id == product_id:
            item.quantity += quantity
            break
    else:
        # if product is not in the cart, add it as a new item
        cart.items.append(CartItem(product_id=product_id, quantity=quantity, price=price))
    
    cart.save()
    return jsonify({
        "message": "Item added to cart",
        "cart": cart.to_json()
    }), 200


@cart_bp.post('/update_item_quantity')
@limiter.limit("5 per minute")
@jwt_required()
def update_item_quantity():
    data = request.get_json()
    user_id = get_jwt_identity()
    product_id = data.get('product_id')
    new_quantity = data.get('quantity')

    if not product_id or new_quantity is None:
        return jsonify({"message": "Product ID and new quantity are required"}), 400

    cart = Cart.objects(user_id=user_id).first()
    if not cart:
        return jsonify({"message": "Cart is empty"}), 200

    # Finding the cart item and update the quantity
    item_found = False
    for item in cart.items:
        if item.product_id == product_id:
            item_found = True
            if new_quantity > 0:
                item.quantity = new_quantity
            else:
                cart.items.remove(item)
            break

    if not item_found:
        return jsonify({"message": "Product not found in cart"}), 404

    cart.save()
    return jsonify({
        "message": "Cart updated successfully",
        "cart": cart.to_json()
    }), 200


# Remove an item from the cart
@cart_bp.post('/remove_item')
@limiter.limit("5 per minute")
@jwt_required()
def remove_from_cart():
    data = request.get_json()
    user_id = get_jwt_identity()
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({
            "message": "Product ID is required"
        }), 400
    
    cart =  Cart.objects(user_id=user_id).first()
    if not cart:
        return jsonify({
            "message": "Cart is empty"
        }), 200
    
    original_length = len(cart.items)
    cart.items = [item for item in cart.items if item.product_id != product_id]
    
    if len(cart.items) == original_length:
        return jsonify({
            "message": "Product not found in cart"
        }), 404
    
    cart.save()
    return jsonify({
        "message": "Item removed from cart",
        "cart": cart.to_json()
    }), 200
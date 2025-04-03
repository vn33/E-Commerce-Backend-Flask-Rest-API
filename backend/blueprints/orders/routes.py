from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from mongoengine.errors import ValidationError as MongoValidationError
from backend.app import limiter
from decimal import Decimal
from datetime import datetime
import pytz
from .models import Order, OrderItem
from backend.blueprints.coupons.models import Coupon
from backend.blueprints.cart.models import Cart
from backend.tasks.notifications import send_order_notification

orders_bp = Blueprint('orders', __name__)

# Create an Order (Place an Order from provided cart data)
@orders_bp.post('/create')
@limiter.limit("5 per minute")
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get('role')

    data = request.get_json() # payload will be empty but we still accept coupon
    coupon_code = data.get("coupon_code")

    # fetch cart items from the Cart
    cart = Cart.objects(user_id=user_id).first()
    if not cart or not cart.items:
        return jsonify({"message": "Cart is empty"}), 400

    order_items = []
    total_amount = Decimal("0.00")

    for item in cart.items:
        quantity = item.quantity
        price = item.price
        total_amount += price * quantity
        order_items.append(OrderItem(
            product_id=item.product_id,
            quantity=quantity,
            price=price
        ))
    
    discount_applied = Decimal("0.00")
    if coupon_code:
        coupon = Coupon.objects(code=coupon_code).first()
        # print(f"coupon.expiry: {coupon.expiry}, tzinfo: {coupon.expiry.tzinfo}, type: {type(coupon.expiry)}")
        # print(f"now: {datetime.now(pytz.utc)}, tzinfo: {datetime.now(pytz.utc).tzinfo}, type: {type(datetime.now(pytz.utc))}")
        if not coupon:
            return jsonify({"message": "Invalid coupon code"}), 400
        
        # Convert coupon expiry to UTC explicitly
        coupon_expiry_utc = coupon.expiry.replace(tzinfo=pytz.utc) if coupon.expiry.tzinfo is None else coupon.expiry
        
        # Check coupon eligibility based on user's role
        if coupon.eligible_roles and user_role not in coupon.eligible_roles:
            return jsonify({"message": "You are not eligible to use this coupon"}), 400
        
        if coupon_expiry_utc < datetime.now(pytz.utc):
            return jsonify({"message": "Coupon expired"}), 400
  
        discount_applied = (total_amount * Decimal(coupon.discount_percent)) / Decimal(100)

    final_amount = total_amount - discount_applied

    try:
        order = Order(
            user_id=user_id,
            items=order_items,
            total_amount=total_amount,
            discount_applied=discount_applied,
            final_amount=final_amount,
            status="Pending"
        )
        order.save()

        # Clearing the Cart after order creation
        cart.items = []
        cart.save()

        # Queue the background task for order notification
        send_order_notification.delay(str(order.pk))

        return jsonify({
            "message": "Order placed successfully",
            "order": order.to_json()
        }), 201
    except MongoValidationError as e:
        return jsonify({
            "message": "Order validation error",
            "details": str(e)
        }), 400

# Track Order Status
@orders_bp.get('/<order_id>')
@limiter.limit("5 per minute")
@jwt_required()
def track_order(order_id):
    try:
        order = Order.objects.get(id=order_id)
        return jsonify({
            "order": order.to_json()
        }), 200
    except Order.DoesNotExist:
        return jsonify({"message": "Order not found"}), 404


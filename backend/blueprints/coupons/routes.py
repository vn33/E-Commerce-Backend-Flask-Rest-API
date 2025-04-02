from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from mongoengine.errors import ValidationError as MongoValidationError
from mongoengine.errors import NotUniqueError as MongoUniqueError
from backend.app import limiter
from datetime import datetime
import pytz
from .models import Coupon

coupons_bp = Blueprint('coupons', __name__)

# FETCH ALL Coupons( Admins only)
@coupons_bp.get('/all')
@limiter.limit("5 per minute")
@jwt_required()
def get_all_coupons():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"message": "Only admins can access all coupons"}), 403

    coupons = Coupon.objects()  # Retrieve all coupons
    coupons_list = [coupon.to_json() for coupon in coupons]
    
    return jsonify({
        "message": "Coupons retrieved successfully",
        "coupons": coupons_list
    }), 200

# CREATE COUPON (Admin only)
@coupons_bp.post('/create')
@limiter.limit("5 per minute")
@jwt_required()
def create_coupon():
    claims = get_jwt()

    if claims.get('role') != 'admin':
        return jsonify({"message": "Only admins can create coupons"}), 403

    data = request.get_json()
    try:
        # Validate required fields
        code = data['code']
        discount_percent = int(data['discount_percent'])
        # Expecting expiry in ISO 8601 format, e.g., "2025-12-31T23:59:59"
        expiry = datetime.fromisoformat(data['expiry']).replace(tzinfo=pytz.utc)

        # Optionally, check eligible_roles if provided; default to ['customer']
        eligible_roles = data.get('eligible_roles', ["customer"])
    except (KeyError, ValueError) as e:
        return jsonify({
            "message": "Invalid input",
            "details": str(e)
        }), 400

    try:
        coupon = Coupon(
            code=code,
            discount_percent=discount_percent,
            expiry=expiry,
            eligible_roles=eligible_roles
        )
        coupon.save()
    except (MongoValidationError, MongoUniqueError) as e:
        return jsonify({
            "message": "Coupon creation failed",
            "details": str(e)
        }), 400

    return jsonify({
        "message": "Coupon created successfully",
        "coupon": coupon.to_json()
    }), 201

# UPDATE COUPON (Admin only)
@coupons_bp.put('/update/<coupon_code>')
@limiter.limit("5 per minute")
@jwt_required()
def update_coupon(coupon_code):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"message": "Only admins can update coupons"}), 403

    data = request.get_json()

    coupon = Coupon.objects(code=coupon_code).first()
    if not coupon:
        return jsonify({"message": "Coupon not found"}), 404

    try:
        # Allow updating discount_percent, expiry, and eligible_roles
        if 'discount_percent' in data:
            coupon.discount_percent = int(data['discount_percent'])
        if 'expiry' in data:
            coupon.expiry = datetime.fromisoformat(data['expiry']).replace(tzinfo=pytz.utc)
        if 'eligible_roles' in data:
            coupon.eligible_roles = data['eligible_roles']
        coupon.save()
    except (ValueError, MongoValidationError) as e:
        return jsonify({
            "message": "Coupon update failed",
            "details": str(e)
        }), 400

    return jsonify({
        "message": "Coupon updated successfully",
        "coupon": coupon.to_json()
    }), 200

# DELETE COUPON (Admin only)
@coupons_bp.delete('/delete/<coupon_code>')
@limiter.limit("3 per minute")
@jwt_required()
def delete_coupon(coupon_code):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"message": "Only admins can delete coupons"}), 403

    coupon = Coupon.objects(code=coupon_code).first()
    if not coupon:
        return jsonify({"message": "Coupon not found"}), 404

    try:
        coupon.delete()
    except MongoValidationError as e:
        return jsonify({
            "message": "Coupon deletion failed",
            "details": str(e)
        }), 400

    return jsonify({
        "message": "Coupon deleted successfully"
    }), 200

# User Specific Coupons
@coupons_bp.get('/my_coupons')
@limiter.limit("5 per minute")
@jwt_required()
def get_user_coupons():
    claims = get_jwt()
    user_role = claims.get('role')
    
    # Retrieving coupons that include the user's role in their eligible_roles
    # and that haven't expired
    coupons = Coupon.objects(
        eligible_roles__in=[user_role],
        expiry__gte=datetime.now(pytz.utc)
    )
    coupons_list = [coupon.to_json() for coupon in coupons]
    
    return jsonify({
        "message": "Coupons retrieved successfully",
        "coupons": coupons_list
    }), 200
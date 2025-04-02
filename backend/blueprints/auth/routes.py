from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from mongoengine.errors import ValidationError as MongoValidationError
from marshmallow.exceptions import ValidationError 
from .models import User, RevokedToken
from backend.schemas.register_schema import UserRegisterSchema
from backend.schemas.login_schema import UserLoginSchema
from backend.app import limiter

auth_bp = Blueprint('auth', __name__)
user_register_schema = UserRegisterSchema()
user_login_schema = UserLoginSchema()

@auth_bp.post('/register')
@limiter.limit("5 per minute")
def register_user():
    json_data = request.get_json()
    try:
        data = user_register_schema.load(json_data)
    except ValidationError as err:
        return jsonify({
            "message": "Invalid input", 
            "errors": err.messages
        }), 400
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    
    if User.objects(email=email).first():
        return jsonify({
            "message": "Email already exists"
        }), 400
    
    try:
        user = User(email=email, role=role)
        user.set_password(password=password)
        user.save()
        return jsonify({
            "message": "User registered successfully",
            "user": user.to_json()
        }), 201
    
    except MongoValidationError as e:
        return jsonify({
            "message": "Database validation error",
            "errors": str(e)
        }), 400
    
@auth_bp.post('/login')
@limiter.limit("5 per minute")
def login():
    json_data = request.get_json()
    try:
        data = user_login_schema.load(json_data)
    except ValidationError as err:
        return jsonify({
            "message": "Invalid input", 
            "errors": err.messages
        }), 400
    email = data.get('email')
    password = data.get('password')

    user = User.objects(email=email).first()
    if not user or not user.check_password(password=password):
        return jsonify({
            "message": "Invalid email or password"
        }), 401
    
    access_token = create_access_token(identity=str(user.pk))
    refresh_token = create_refresh_token(identity=str(user.pk))

    return jsonify({
        "message": "Logged in successfully",
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, 
        "user": user.to_json()
    }), 200

@auth_bp.get('/protected')
@limiter.limit("10 per minute")
@jwt_required()
def protected():
    # Retrieving all claims from the JWT
    claims = get_jwt()
    role = claims.get("role")
    email = claims.get("email")
    
    return jsonify({
        "message": "Protected route accessed",
        "role": role,
        "email": email
    }), 200

# Regain access token from refresh token
@auth_bp.get('/refresh_access_token')
@limiter.limit("5 per minute")
@jwt_required(refresh=True)
def refresh_access_token():
    jwt_data = get_jwt()
    jti = jwt_data['jti']
    
    refresh_tokeb_b = RevokedToken(jti=jti)
    refresh_tokeb_b.save()
    
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    new_refresh_token = create_refresh_token(identity=identity)

    return jsonify({
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }), 200

@auth_bp.get('/logout')
@limiter.limit("5 per minute")
@jwt_required(verify_type=False)
def logout():
    jwt = get_jwt()

    jti = jwt['jti']
    token_type = jwt['type']

    token_b = RevokedToken(jti=jti)
    token_b.save()
    return jsonify({"message": f"{token_type} token revoked and Logout successfully"}), 200
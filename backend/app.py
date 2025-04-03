from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from mongoengine import connect
from flask_jwt_extended import JWTManager
from config import DevelopmentConfig
from backend.blueprints.auth.models import User, RevokedToken
from datetime import timedelta
from flask_caching import Cache
from .celery_utils import celery_init_app

jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,  # Determines unique user (IP-based)
    default_limits=["10 per minute"],  # Default global limit
    storage_uri="memory://"  #mongodb://localhost:27017/rate_limits
)

cache = Cache()
celery_app = None

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30) # expires in 30 
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost:6379/0",
            result_backend="redis://localhost:6379/0",
        ),
    )
    
    limiter.init_app(app)
    cache.init_app(app)

    # Initialize MongoEngine
    connect(host=app.config['MONGO_URI'])
    jwt.init_app(app)

    celery_app = celery_init_app(app)
    celery_app.set_default()


    from backend.blueprints.testdb_connection.routes import test_db_bp
    from backend.blueprints.auth.routes import auth_bp
    from backend.blueprints.products.routes import products_bp
    from backend.blueprints.cart.routes import cart_bp
    from backend.blueprints.orders.routes import orders_bp
    from backend.blueprints.coupons.routes import coupons_bp
    
    app.register_blueprint(test_db_bp, url_prefix='/testdb_connection')
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(coupons_bp, url_prefix="/coupons")
    
    # Handle Rate Limit Errors
    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(e):
        return jsonify({
            "message": "Rate limit exceeded. Please try again later.",
            "error": "Too Many Requests"
        }), 429

    # load user
    @jwt.user_lookup_loader
    def user_lookup_callback(jwt_headers, jwt_data):
        identity = jwt_data["sub"]
        return User.objects(id=identity).first()
    
    # additional claims
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        # Lookup the user object based on the identity (user id)
        user = User.objects(id=identity).first()
        if user:
            return {
                "role": user.role,
                "email": user.email
            }
        return {}
    
    # jwt error handlers
    @jwt.expired_token_loader
    def exprired_token_callback(jwt_header, jwt_data):
        return jsonify({"message": "The token has expired","error":"token_expired"}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "The token is invalid","error":"invalid_token"}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"message": "The token is missing","error":"authorization_header"}), 401
    
    # revoking access token
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        token = RevokedToken.objects(jti=jti).first()
        return token is not None
    
    return app
   
from mongoengine import Document, StringField, DateTimeField
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

class User(Document):
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    role = StringField(required=True, choices=('customer', 'admin','prime_customer'), default='customer')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def to_json(self):
        return {
            "id": str(self.pk),
            "email": self.email,
            "role": self.role
        }

class RevokedToken(Document):
    jti = StringField(required=True, unique=True)
    revoked_at = DateTimeField(required=True, default=lambda: datetime.now(pytz.timezone("Asia/Kolkata")))
    
    def __repr__(self):
        return f"<Token {self.jti}>"
    
    def save_token(self):
        self.save()

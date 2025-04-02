from mongoengine import (
    Document, EmbeddedDocument, EmbeddedDocumentField,
    EmbeddedDocumentListField, StringField, IntField,
    DecimalField, DateTimeField, ListField
)
from datetime import datetime
import pytz

class Coupon(Document):
    code = StringField(required=True, unique=True)
    discount_percent = IntField(required=True)
    expiry = DateTimeField(required=True)
    # Optional: list of roles eligible for this coupon (default to customers)
    eligible_roles = ListField(StringField(), default=["customer"])

    def to_json(self):
        return {
            "id": str(self.pk),
            "code": self.code,
            "discount_percent": self.discount_percent,
            "expiry": self.expiry.isoformat(),
            "eligible_roles": self.eligible_roles
        }
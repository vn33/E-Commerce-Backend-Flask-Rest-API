from mongoengine import (
    Document, EmbeddedDocument,
    EmbeddedDocumentListField, StringField, IntField,
    DecimalField, DateTimeField
)

from datetime import datetime
import pytz

class OrderItem(EmbeddedDocument):
    product_id = StringField(required=True)
    quantity = IntField(required=True, default=1)
    price = DecimalField(required=True, precision=2)
    
    def to_json(self):
        return {
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': float(self.price)
        }

class Order(Document):
    user_id = StringField(required=True)
    items = EmbeddedDocumentListField(OrderItem)
    total_amount = DecimalField(required=True, precision=2)
    discount_applied = DecimalField(required=True, default=0, precision=2)
    final_amount = DecimalField(required=True, precision=2)
    status = StringField(required=True, choices=["Pending","Shipped","Delivered"], default="Pending")
    created_at = DateTimeField(default=datetime.now(pytz.utc))

    def to_json(self):
        return {
            "id": str(self.pk),
            "user_id": self.user_id,
            "items": [item.to_json() for item in self.items],
            "total_amount": float(self.total_amount),
            "discount_applied": float(self.discount_applied),
            "final_amount": float(self.final_amount),
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }        
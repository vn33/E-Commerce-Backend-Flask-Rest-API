from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentListField, StringField, IntField, DecimalField

class CartItem(EmbeddedDocument):
    product_id = StringField(required=True)
    quantity = IntField(required=True, default=1)
    price = DecimalField(required=True, precision=2)

class Cart(Document):
    user_id = StringField(required=True, unique=True)
    items = EmbeddedDocumentListField(CartItem)

    def to_json(self):
        return {
            "user_id": self.user_id,
            "items": [{"product_id": item.product_id, "quantity": item.quantity, "price": item.price} for item in self.items]
        }

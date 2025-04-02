from mongoengine import Document, StringField, IntField, ListField,DecimalField, EmbeddedDocument, EmbeddedDocumentListField

class ProductVariant(EmbeddedDocument):
    sku = StringField(required=True)
    stock = IntField(min_value=0, default=0)
    price = DecimalField(precision=2, min_value=0)

    def to_json(self):
        return {
            "sku": self.sku,
            "stock": self.stock,
            "price": float(self.price)
        }

class Product(Document):
    name = StringField(required=True)
    description = StringField()
    category = StringField(required=True)
    variants = EmbeddedDocumentListField(ProductVariant)
    images = ListField(StringField())
    
    meta = {'collection': 'products', 'indexes': ['name', 'category']}
    def to_json(self):
        return {
            "id": str(self.pk),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "variants": [v.to_json() for v in self.variants],
            "images": self.images
        }



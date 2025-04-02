from marshmallow import Schema, fields, validate


class ProductVariantSchema(Schema):
    sku = fields.Str(required=True)
    stock = fields.Int(missing=0, validate=validate.Range(min=0))
    price = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0))

class ProductSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(missing="")
    category = fields.Str(required=True)
    images = fields.List(fields.Str(), missing=[])
    variants = fields.List(fields.Nested(ProductVariantSchema), missing=[])

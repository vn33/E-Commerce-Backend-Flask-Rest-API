from marshmallow import Schema, fields, validate


class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
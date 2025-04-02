from mongoengine import Document, StringField, IntField

class TestDoc(Document):
    name = StringField(required=True)
    value = IntField()
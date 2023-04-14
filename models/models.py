from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import enum

db = SQLAlchemy()

class EnumADiccionario(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return {"llave": value.name, "valor": value.value}

class Status(enum.Enum):
    UPLOADED = 1
    PROCESSED = 2

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fileName = db.Column(db.String(50))
    newFormat = db.Column(db.String(50))
    timeStamp = db.Column(db.DateTime)
    status = db.Column(db.Enum(Status))
    user = db.Column(db.Integer, db.ForeignKey('user.id'))

class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        include_relationships = True
        load_instance = True

    fileName = fields.String()
    newFormat = fields.String()
    timeStamp = fields.DateTime()
    status = EnumADiccionario(attribute=("status"))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(50))
    password = db.Column(db.String(50))
    tasks = db.relationship('Task', cascade='all, delete, delete-orphan')
  
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True
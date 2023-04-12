from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields, Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app import db


class Task(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    file_name = db.Column(db.String(128))
    new_format = db.Column(db.String(128))
    time_stamp = db.Column(db.DateTime, default= db.func.current_timestamp())
    status = db.Column(db.String(128), default="uploaded")

class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        load_instance = True
    id = fields.String()
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields, Schema
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    file_name = db.Column(db.String(128))
    new_format = db.Column(db.String(128))
    time_stamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(128), default="uploaded")

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    nombre_archivo = db.Column(db.String(128))
    ruta = db.Column(db.String(128))
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50))
    password1 = db.Column(db.String(50))
    password2 = db.Column(db.String(50))
    email = db.Column(db.String(128))
    tasks = db.relationship('Task', cascade='all, delete, delete-orphan')
    files = db.relationship('File', cascade='all, delete, delete-orphan')



class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        include_relationships = True
        load_instance = True

    id = fields.String()
    file_name = fields.String()
    new_format = fields.String()
    time_stamp = fields.DateTime(dump_only=True)
    status = fields.String()

class FileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = File
        include_relationships = True
        load_instance = True

    id = fields.String()
    nombre_archivo = fields.String()
    ruta = fields.String()


class UsuarioSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Usuario
        include_relationships = True
        load_instance = True
    id = fields.String()
    username = fields.String()
    password1 = fields.String(load_only=True)
    password2 = fields.String(load_only=True)
    email = fields.String()
    tasks = fields.Nested(TaskSchema, many=True)
    files = fields.Nested(FileSchema, many=True)






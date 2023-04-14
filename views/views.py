from cmath import log
from fileinput import filename
from operator import truediv
from flask import request, send_from_directory, abort
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_restful import Resource
from werkzeug.utils import secure_filename
import re
import os
from datetime import datetime
from models import db, User, UserSchema, Task
from tasks import tasks
from models.models import Status, TaskSchema
from pydub import AudioSegment
from celery import Celery

user_schema = UserSchema()
task_schema = TaskSchema()

celery_app = Celery(__name__, broker='redis://localhost:6379/0')

ALLOWED_EXTENSIONS_AUDIO = set(['mp3', 'acc', 'ogg', 'wav', 'wma'])

class ViewSignUp(Resource):

    def post(self):

        if not request.json["password1"] == request.json["password2"]:
            return "Las contraseñas no coinciden.", 412    

        if not ViewSignUp.password_check(request.json["password1"]):
            return "La contraseña no es lo suficientemente fuerte.", 412   

        email = User.query.filter(User.email == request.json["email"]).first()
        if not email is None:
            return "Ya existe un usuario registrado con el correo electrónico.", 412 
        
        username = User.query.filter(User.username == request.json["username"]).first()
        if not username is None:
            return "Ya existe un usuario registrado con el nombre de usuario.", 412

        else:
            new_user = User(username=request.json["username"], email=request.json["email"], password=request.json["password1"])
            db.session.add(new_user)
            db.session.commit()
            token_de_acceso = create_access_token(identity=new_user.id)
            return {"mensaje": "Usuario creado exitosamente", "token": token_de_acceso, "id": new_user.id}
    
    def password_check(password):
        """
        Una contraseña se considera fuerte si tiene:
            8 caracteres de longitud o más
            1 dígito o más
            1 símbolo o más
            1 letra mayúscula o más
            1 letra minúscula o más
        """
        length_error = len(password) < 8

        digit_error = re.search(r"\d", password) is None

        uppercase_error = re.search(r"[A-Z]", password) is None

        lowercase_error = re.search(r"[a-z]", password) is None

        symbol_error = re.search(r"[ !#$%&'()*+,-./[\\\]^_`{|}~"+r'"]', password) is None

        password_ok = not ( length_error or digit_error or uppercase_error or lowercase_error or symbol_error )

        return password_ok

class ViewLogIn(Resource):

    def post(self):
        user = User.query.filter(User.username == request.json["username"],
                                       User.password == request.json["password"]).first()
        db.session.commit()
        if user is None:
            return "El nombre de usuario o contraseña es incorrecto.", 404
        else:
            token_de_acceso = create_access_token(identity=user.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": token_de_acceso}    

class ViewTask(Resource):
    
    @jwt_required()
    def get(self, id_task=None):
        if id_task is not None:
            task = Task.query.filter(Task.id == id_task).first()
            db.session.commit()
            if task is None:
                return "La tarea no existe.", 404
            else:
                task = task_schema.dump(task)
                return {"mensaje": "Tarea obtenida exitosamente", "tarea": task}
        else:        
            user = get_jwt_identity()
            tasks = Task.query.filter(Task.user == user).all()

            db.session.commit()
            args = request.args
            order = args.get('order')
            maxTasks = args.get('max')
            if order == "0":
                tasks = Task.query.filter(Task.user == user).order_by(Task.id.asc()).limit(maxTasks)
            elif order == "1":
                tasks = Task.query.filter(Task.user == user).order_by(Task.id.desc()).limit(maxTasks)
            else:
                return "El orden debe ser 'asc' o 'desc'.", 412
            tasks = task_schema.dump(tasks, many=True)
            return {"mensaje": "Tareas obtenidas exitosamente", "tareas": tasks}

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        user =  User.query.get_or_404(user_id)
        print(user.username)
        if user:
            file = request.files['fileName']
            filename = secure_filename(file.filename)
            newFormat = request.values["newFormat"]
            
            if allowed_file(filename) and allowed_file(newFormat):
                file.save(os.path.join('./data/uploaded',filename))
                new_task = Task(fileName = filename, newFormat = newFormat, timeStamp = datetime.now(), status = "UPLOADED")
                user.tasks.append(new_task)
                db.session.add(new_task)
                db.session.commit()
                tasks.process_file.delay(filename, newFormat, new_task.id, user.id)
                return {"mensaje": "Tarea creada exitosamente.", "id": new_task.id}

            else:
                return "El archivo no cumple con los formatos permitidos.", 412 

    @jwt_required()
    def delete(self, id_task):
        task = Task.query.get_or_404(id_task)
        db.session.commit()
        if task is None:
            return "La tarea no existe.", 404
        else:
            if task.status != Status.PROCESSED:
                return "La tarea no ha sido procesada.", 412
            fileName = task.fileName
            fileNoExtension = os.path.splitext(fileName)[0]
            os.remove(os.path.join('./data/processed', fileNoExtension + "." + task.newFormat))
            os.remove(os.path.join('./data/uploaded', fileName))
            db.session.delete(task)
            db.session.commit()
            return {"mensaje": "Tarea eliminada exitosamente."}

    @jwt_required()
    def put(self, id_task):
        # Modify task format
        task = Task.query.get_or_404(id_task)
        db.session.commit()
        if task is None:
            return "La tarea no existe.", 404
        else:
            if not allowed_file(request.json["newFormat"]):
                return "El formato no es válido.", 412
            print(task.status)
            if task.status == Status.PROCESSED:
                # Delete old file
                fileNoExtension = os.path.splitext(task.fileName)[0]
                os.remove(os.path.join('./data/processed', fileNoExtension + "." + task.newFormat))
                task.status = Status.UPLOADED
            tasks.process_file.delay(task.fileName, task.newFormat, task.id, task.user)
            task.newFormat = request.json["newFormat"]
            db.session.commit()
            return {"mensaje": "Tarea modificada exitosamente", "tarea": task_schema.dump(task)}

class ViewFile(Resource):
    def get(self, filename):
        try:
            task = Task.query.filter(Task.fileName.startswith(filename)).first()
            db.session.commit()
            if task is None:
                return "El archivo no existe.", 404
            else:
                args = request.args
                tipo = args.get('tipo')
                if tipo == "original":
                    return send_from_directory('./data/uploaded', filename = task.fileName, as_attachment = True)
                if tipo == "procesado":
                    return send_from_directory('./data/processed', filename = filename + "." + task.newFormat, as_attachment = True)
                else:
                    return "El tipo debe ser 'original' o 'procesado'.", 412
        except FileNotFoundError:
            abort(404)    
        
def allowed_file(file):
        file = file.split('.')
        print(file)
        # File extension allowed
        print(file[-1])
        if file[-1] in ALLOWED_EXTENSIONS_AUDIO:
            return True
        return False

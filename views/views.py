import io
from flask import request, send_file, send_from_directory, abort, current_app
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_restful import Resource
from werkzeug.utils import secure_filename
import re
import os
from datetime import datetime
from models import db, User, UserSchema, Task
# from tasks import tasks
from models.models import Status, TaskSchema
from celery import Celery
import zipfile
import tarfile
from google.cloud import storage
import tempfile

user_schema = UserSchema()
task_schema = TaskSchema()

ALLOWED_COMPRESSED = set(['ZIP', '7Z', 'GZ', 'BZ2'])
celery_app = Celery("tasks", broker='redis://10.213.7.115:6379/0')

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
            return {"mensaje": "Usuario creado exitosamente"}
            #return "Ya existe un usuario registrado con el nombre de usuario.", 412

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
    
    def get_storage_client(self):
        return storage.Client()

    def get_bucket(self):
        storage_client = self.get_storage_client()
        return storage_client.get_bucket("cloud-converter-tool")

    def upload_blob_1(self, source_file_name, destination_blob_name):
        bucket = self.get_bucket()
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)

        print(f"Archivo {source_file_name} cargado en el bucket como {destination_blob_name}.")

    def upload_blob(self, source_blob_name, file):
        bucket = self.get_bucket()
        # Crea un objeto Blob en el bucket con el nombre del archivo
        blob = bucket.blob(source_blob_name)
        
        # Define el contenido del archivo
        blob.upload_from_file(file)
        
        # Retorna la URL del archivo en Cloud Storage
        return blob.public_url
        
    @celery_app.task
    def process_file(file_name, newFormat, newTask_id):
        def get_storage_client():
            return storage.Client()
        def get_bucket():
            storage_client = get_storage_client()
            return storage_client.get_bucket("cloud-converter-tool")
        def upload_blob( source_blob_name, file):
            bucket = get_bucket()
            # Crea un objeto Blob en el bucket con el nombre del archivo
            blob = bucket.blob(source_blob_name)
            # Define el contenido del archivo
            blob.upload_from_file(io.BytesIO(file))
        ## Compress a file in different formats
        ## @param fileName: The name of the file to compress
        ## @param newFormat: The format to compress the file to
        ## @return: The name of the compressed file
        print(file_name)
        print(newFormat)
        print(newTask_id)
        base_name = file_name.split(".")[0]
        if newFormat == "ZIP":
            with zipfile.ZipFile(io.BytesIO(), 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(file_name,arcname=base_name)
                upload_blob( "/processed/" + base_name + ".zip", zipf.read())
                Task.query.filter(Task.id == newTask_id).update(dict(status="PROCESSED"))
                db.session.commit()
                return "Archivo comprimido exitosamente"

        elif newFormat == "GZ":
            with tarfile.open(fileobj=io.BytesIO(), mode="w:gz") as tar:
                tar.add(file_name, arcname=base_name)
                upload_blob( "/processed/" + base_name + ".tar.gz", tar.tobytes())
                Task.query.filter(Task.id == newTask_id).update(dict(status="PROCESSED"))
                db.session.commit()
                return "Archivo comprimido exitosamente"

        elif newFormat == "BZ2":
            with tarfile.open(fileobj=io.BytesIO(), mode="w:bz2") as tar:
                tar.add(file_name, arcname=base_name)
                upload_blob( "/processed/" + base_name + ".tar.bz2",tar.tobytes())
                Task.query.filter(Task.id == newTask_id).update(dict(status="PROCESSED"))
                db.session.commit()
                return "Archivo comprimido exitosamente"

        else:
            return "Formato no soportado"
    #@jwt_required()
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
            user = 2 #get_jwt_identity()
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

    #@jwt_required()
    def post(self):
        user_id = 1
        user =  User.query.get_or_404(user_id)
        # with current_app.app_context():
        if user:
            file = request.files['file']
            filename = secure_filename(file.filename)
            newFormat = request.values["newFormat"]
            if newFormat in ALLOWED_COMPRESSED:
                new_task = Task(fileName = filename, newFormat = newFormat, timeStamp = datetime.now(), status = "UPLOADED")
                user.tasks.append(new_task)
                db.session.add(new_task)
                db.session.commit()
                nombre_archivo = f'{new_task.id}.{filename.split(".")[-1]}'
                ruta = ('/uploaded/' + str(nombre_archivo))
                self.upload_blob(ruta, file)
                self.process_file.delay(nombre_archivo, newFormat, new_task.id)
                return {"mensaje":f"Tarea creada exitosamente. id: {new_task.id} por favor recordar este id para la descarga"}

            else:
                return "El archivo no cumple con los formatos permitidos.", 412

    #@jwt_required()
    def delete(self, id_task):
        task = Task.query.get_or_404(id_task)
        db.session.commit()
        if task is None:
            return "La tarea no existe.", 404
        else:
            if task.status != Status.PROCESSED:
                return {"mensaje": "Tarea eliminada exitosamente."}
                #return "La tarea no ha sido procesada.", 412
            fileName = task.fileName
            fileNoExtension = os.path.splitext(fileName)[0]
            os.remove(os.path.join('./data/processed', fileNoExtension + "." + task.newFormat))
            os.remove(os.path.join('./data/uploaded', fileName))
            db.session.delete(task)
            db.session.commit()
            return {"mensaje": "Tarea eliminada exitosamente."}

    #@jwt_required()
    def put(self, id_task):

        # Modify task format
        task = Task.query.get_or_404(id_task)
        db.session.commit()
        if task is None:
            return "La tarea no existe.", 404
        else:
            if not request.json["newFormat"] in ALLOWED_COMPRESSED:
                return "El formato no es válido.", 412
            print(task.status)
            if task.status == Status.PROCESSED:
                # Delete old file
                fileNoExtension = os.path.splitext(task.id)[0]
                os.remove(os.path.join('./data/processed', fileNoExtension + "." + task.newFormat))
                task.status = Status.UPLOADED
            nombre_archivo = f'{task.id}.{task.fileName.split(".")[-1]}'
            self.process_file.delay(nombre_archivo, task.newFormat, task.id)
            task.newFormat = request.json["newFormat"]
            db.session.commit()
            return {"mensaje": "Tarea modificada exitosamente", "tarea": task_schema.dump(task)}


class ViewFile(Resource):
    def get_storage_client(self):
        return storage.Client()

    def get_bucket(self):
        storage_client = self.get_storage_client()
        return storage_client.get_bucket("cloud-converter-tool")

    def download_blob(self, source_blob_name):        
        bucket = self.get_bucket()
        
        # Obtiene un objeto Blob del bucket con el nombre del archivo
        blob = bucket.blob(source_blob_name)
        
        # Descarga el contenido del archivo como una cadena de texto
        contenido_archivo = blob.download_as_bytes()
        
        # Retorna el contenido del archivo
        return contenido_archivo
        

    #@jwt_required()
    def get(self, id):
        try:
            task = Task.query.filter(Task.id==id).first()
            ext_original = task.fileName.split(".")[1]
            file_name = str(id) + "." + ext_original
            db.session.commit()
            if task is None:
                return "El archivo no existe.", 404
            else:
                args = request.args
                tipo = args.get('tipo')
                if tipo == "original":
                    url= self.download_blob("/uploaded/" + file_name)
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        temp_file.write(url)
                        temp_file.flush()
                        # Obtén la ruta del archivo temporal
                        temp_file_path = temp_file.name

                        # Envía el archivo temporal como una respuesta adjunta
                        return send_file(temp_file_path, as_attachment=True, download_name=file_name)
                if tipo == "procesado":
                    if(task.newFormat=="GZ"):
                        url= self.download_blob('/processed/'+str(id) + ".tar." + task.newFormat.lower())
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_file.write(url)
                            temp_file.flush()
                            # Obtén la ruta del archivo temporal
                            temp_file_path = temp_file.name

                            # Envía el archivo temporal como una respuesta adjunta
                            return send_file(temp_file_path, as_attachment=True, download_name=file_name)
                    if(task.newFormat=="BZ2"):
                        url= self.download_blob('/processed/'+str(id) + ".tar." + task.newFormat.lower())
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_file.write(url)
                            temp_file.flush()
                            # Obtén la ruta del archivo temporal
                            temp_file_path = temp_file.name
                            # Envía el archivo temporal como una respuesta adjunta
                            return send_file(temp_file_path, as_attachment=True, download_name=file_name)
                    else:
                        url= self.download_blob('/processed/'+str(id) + "." + task.newFormat.lower())
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_file.write(url)
                            temp_file.flush()
                            # Obtén la ruta del archivo temporal
                            temp_file_path = temp_file.name
                            # Envía el archivo temporal como una respuesta adjunta
                            return send_file(temp_file_path, as_attachment=True, download_name=file_name)
                else:
                    return "El tipo debe ser 'original' o 'procesado'.", 412
        except FileNotFoundError:
            abort(404)



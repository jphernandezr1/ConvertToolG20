from datetime import datetime
from conversion import convert_audio, convert_video, convert_image, convert_document
from models.models import Task, TaskSchema, db
from flask_restful import Resource
from flask_jwt_extended import jwt_required, create_access_token
from flask import request
from flask_uploads import UploadSet, configure_uploads, IMAGES, DOCUMENTS
import app

audio_files = UploadSet('audio', extensions=('mp3', 'acc', 'ogg', 'wav', 'wma'))
video_files = UploadSet('video', extensions=('mp4', 'webm', 'avi', 'mpeg', 'wmv'))
image_files = UploadSet('image', extensions=('jpg', 'png', 'webp'))
document_files = UploadSet('document', extensions=('doc', 'docx', 'ppt', 'pptx', 'xlsx', 'odt'))
compressed_files = UploadSet('compressed', extensions=('zip', '7z', 'tar.gz', 'tar.bz2'))

configure_uploads(app, (audio_files, video_files, image_files, document_files, compressed_files))

task_schema = TaskSchema()

class TaskView(Resource):
    @jwt_required()
    def get(self, id_task):
        return task_schema.dump(Task.query.get_or_404(id_task))

    @jwt_required()
    def put(self, id_task):
        task = Task.query.get_or_404(id_task)
        task.file_name = request.json["file_name"]
        task.new_format = request.json["new_format"]
        task.time_stamp = request.json["time_stamp"]
        task.status = request.json["status"]
        db.session.commit()
        return task_schema.dump(task)

    @jwt_required()
    def delete(self, id_task):
        task = Task.query.get_or_404(id_task)
        db.session.delete(task)
        db.session.commit()
        return '', 204
class TasksView(Resource):
    @jwt_required()
    def get(self):
        tasks = Task.query.all()
        return [task_schema.dump(task) for task in tasks]

    @jwt_required()
    def post(self):
        file_name = request.files['file_name']
        new_format = request.form['new_format']
        time_stamp = datetime.now()
        status = 'uploaded'

        if new_format in ('mp3', 'acc', 'ogg', 'wav', 'wma'):
            converted_file = convert_audio(file_name, new_format)
            storage = audio_files.save(converted_file)
        elif new_format in ('mp4', 'webm', 'avi', 'mpeg', 'wmv'):
            converted_file = convert_video(file_name, new_format)
            storage = video_files.save(converted_file)
        elif new_format in ('jpg', 'png', 'webp'):
            converted_file = convert_image(file_name, new_format)
            storage = image_files.save(converted_file)
        elif new_format == 'pdf':
            converted_file = convert_document(file_name)
            storage = document_files.save(converted_file)
        else:
            return {'error': 'Formato Inválido.'}, 400

        task = Task(file_name=storage, new_format=new_format, time_stamp=time_stamp, status='processed')
        db.session.add(task)
        db.session.commit()

        return {'message': 'Se creó la tarea exitosamente.'}, 201





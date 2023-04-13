from datetime import datetime
from conversion import convert_audio, convert_video, convert_image, convert_document
from models.models import Task, TaskSchema, db
from flask_restful import Resource
from flask_jwt_extended import jwt_required
import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
import app

UPLOAD_FOLDER = '../uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
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
    print("entro")
    @jwt_required()
    def get(self):
        tasks = Task.query.all()
        return self.response, 200

    
    @jwt_required()
    def post(self):
        file_name = request.files['file_name']
        new_format = request.form['new_format']
        time_stamp = datetime.now()
        status = 'uploaded'

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return redirect(url_for('download_file', name=filename))
        task = Task(file_name, new_format=new_format, time_stamp=time_stamp, status='processed')
        db.session.add(task)
        db.session.commit()

        return {'message': 'Se creó la tarea exitosamente.'}, 201
    
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





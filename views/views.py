from models.models import db, Task, TaskSchema
from flask_restful import Resource
from flask_jwt_extended import jwt_required, create_access_token
from flask import request

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
        new_task = Task(file_name = request.json["file_name"],
                        new_format = request.json["new_format"],
                        time_stamp = request.json["time_stamp"],
                        status = request.json["status"] )
        db.session.add(new_task)
        db.session.commit()
        return task_schema.dump(new_task)

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from views.views import TaskView, TasksView, db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://cloud-user:cloud-user@34.170.195.29:5432/cloud-converter-tool'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(TasksView, '/api/tasks')
api.add_resource(TaskView, '/api/tasks/<int:id_task>')
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

jwt = JWTManager(app)
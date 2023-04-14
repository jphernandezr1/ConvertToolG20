from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from models import db
from views import ViewSignUp, ViewLogIn, ViewTask, ViewFile

app = Flask(__name__)
##app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/postgres"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@34.170.195.29:5432/cloud-converter-tool"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'frase-secreta'
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['UPLOAD_FOLDER'] = "./data/uploaded"

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(ViewSignUp, '/auth/signup')
api.add_resource(ViewLogIn, '/auth/login')
api.add_resource(ViewTask, '/tasks','/tasks/<int:id_task>', '/tasks/<int:order>/<int:max>')
api.add_resource(ViewFile, '/files/<filename>')

jwt = JWTManager(app)
from models import db
from models.models import Task, User
from celery import Celery
from pydub import AudioSegment
import os
from email.message import EmailMessage
import smtplib
from celery.signals import task_postrun

celery_app = Celery("tasks", broker='redis://localhost:6379/0')

@celery_app.task(name='file.conversion')
def process_file(fileName, newFormat, newTask_id, user_id):
    ## Convert an audio file to a different format
    ## @param fileName: The name of the file to convert
    ## @param newFormat: The format to convert the file to
    ## @return: The name of the converted file
    print(fileName)
    sound = AudioSegment.from_file("./data/uploaded/"+fileName)
    if sound:
        fileNoExtension = fileName.split(".")[0]
        sound.export("./data/processed/"+fileNoExtension+".wav", format=newFormat)
        task = Task.query.filter(Task.id == newTask_id).first()
        task.status = "PROCESSED"
        db.session.commit()
        db.session.remove()
        return "Archivo convertido exitosamente"
    else:
        return "no se encontro el archivo"


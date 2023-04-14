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
    sound = AudioSegment.from_file("./data/uploaded/"+fileName)
    fileNoExtension = os.path.splitext(fileName)
    sound.export("./data/processed/"+fileNoExtension[0]+".wav", format=newFormat)
    task = Task.query.filter(Task.id == newTask_id).first()
    task.status = "PROCESSED"
    db.session.commit()
    ## Send email to user
    user = User.query.filter(User.id == user_id).first()
    db.session.commit()
    remitente = "pruebasoftwarenube@hotmail.com"
    destinatario = user.email
    mensaje = "Archivo convertido exitosamente"
    email = EmailMessage()
    email["From"] = remitente
    email["To"] = destinatario
    email["Subject"] = "Se ha procesado su archivo"
    email.set_content(mensaje)
    smtp = smtplib.SMTP("smtp-mail.outlook.com", port=587)
    smtp.starttls()
    smtp.login(remitente, "Software589$")
    smtp.sendmail(remitente, destinatario, email.as_string())
    smtp.quit()
    db.session.remove()
    return "Archivo convertido exitosamente"


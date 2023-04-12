from celery import app
from datetime import datetime
from models.models import db, Task

@app.task
def convert_file(task_id):
    task = Task.query.get(task_id)
    # TODO: Convertir el archivo al formato deseado
    converted_file = ""
    # TODO: Guardar el archivo convertido al sistema de archivos
    storage = ""
    # Actualizar el estatus a procesado y guardarlo en la db
    task.status = "processed"
    task.file_name = storage
    task.time_stamp = datetime.now()
    db.session.commit()

@app.task
def process_files():
    tasks = Task.query.filter_by(status='uploaded').all()
    for task in tasks:
        convert_file.delay(task.id)


from models import db
from models.models import Task
from celery import Celery
import zipfile
import tarfile
import pylzma

celery_app = Celery("tasks", broker='redis://localhost:6377/0')

@celery_app.task
def process_file(fileName, newFormat, newTask_id):
    ## Compress a file in different formats
    ## @param fileName: The name of the file to compress
    ## @param newFormat: The format to compress the file to
    ## @return: The name of the compressed file

    ##sound = AudioSegment.from_file("./data/uploaded/"+fileName)
    if newFormat == "ZIP":
        with zipfile.ZipFile(f'{fileName}.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write("./data/uploaded/"+fileName)
            task = Task.query.filter(Task.id == newTask_id).first()
            task.status = "PROCESSED"
            db.session.commit()
            db.session.remove()
            return "Archivo comprimido exitosamente"
    elif newFormat == "7Z":
        with open(f'{fileName}.7z', 'wb') as outfile, pylzma.open(outfile, 'w') as lzma:
            with open("./data/uploaded/"+fileName, 'rb') as f:
                lzma.write(f.read())
                task = Task.query.filter(Task.id == newTask_id).first()
                task.status = "PROCESSED"
                db.session.commit()
                db.session.remove()
                return "Archivo comprimido exitosamente"
    elif newFormat == "TAR.GZ":
        with tarfile.open(f"{fileName}.tar.gz", "w:gz") as tar:
            tar.add("./data/uploaded/"+fileName)
            task = Task.query.filter(Task.id == newTask_id).first()
            task.status = "PROCESSED"
            db.session.commit()
            db.session.remove()
            return "Archivo comprimido exitosamente"
    elif newFormat == "TAR.BZ2":
        with tarfile.open(f"{fileName}.tar.bz2", "w:bz2") as tar:
            tar.add("./data/uploaded/"+fileName)
            task = Task.query.filter(Task.id == newTask_id).first()
            task.status = "PROCESSED"
            db.session.commit()
            db.session.remove()
            return "Archivo comprimido exitosamente"
    else:
        return "Formato no soportado"
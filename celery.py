from celery import Celery
import celery.schedules import crontab


app = Celery('ConvertTool', broker='pyamqp://guest@localhost//', backend='rpc://')

app.conf.beat_schedule = {
    'process_files': {
        'task': 'app.tasks.process_files',
        'schedule': crontab(minute='*/10')  # Corre cada 10 minutos
    }
}

if __name__ == '___main___':
    app.start()


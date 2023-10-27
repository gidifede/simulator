from celery import Celery
from dotenv import load_dotenv
import os
from kombu import Queue


load_dotenv()  # take environment variables from .env.


redis_host = os.environ.get("REDIS_HOST", "localhost")

print("REDIS_HOST", redis_host)

print("ENV", os.environ)

app = Celery('celery_cmds', broker=f'redis://{redis_host}:6379/0', include=["logistic_backbone_commands"])
app.conf.broker_url = f'redis://{redis_host}:6379/0'
app.conf.result_backend = f'redis://{redis_host}:6379/0'
app.conf.event_serializer = 'pickle' # this event_serializer is optional. somehow i missed this when writing this solution and it still worked without.
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['application/json', 'application/x-python-serialize']
app.conf.task_queues = [
    Queue('cmds-queue', routing_key='cmds-queue'),
]
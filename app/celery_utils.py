import os
from celery import Celery

def make_celery(app_name=__name__):
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    return Celery(
        app_name, 
        broker=redis_url, 
        backend=redis_url,
        include=['worker_service.worker']  # <-- Ajoutez le chemin exact de votre fichier de tâches
    )

celery_app = make_celery()
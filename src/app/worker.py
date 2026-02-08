from app.config import get_settings

from celery import Celery

settings = get_settings()

celery_app = Celery(__name__)
celery_app.conf.broker_url = settings.CELERY_BROKER_URL
celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND

celery_app.autodiscover_tasks(['app'])

from app import tasks

# DEBUG: Print registered tasks
print("=" * 50)
print("REGISTERED TASKS:")
print(celery_app.tasks.keys())
print("=" * 50)
from celery import Celery

from data_layer_manager.core.config import get_settings

settings = get_settings()

app = Celery(
    "data_layer_manager",
    broker=settings.redis.url,
    backend=settings.redis.url,
    include=["apps.worker.src.consumers"],  # Register your task modules here
)

# Optional configuration overrides
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

if __name__ == "__main__":
    app.start()

import os
from celery import Celery

os.environ.setdefault('CELERY_CONFIG_MODULE', 'space_diary.config')

app = Celery(
    "SpaceDiary",
    include=["space_diary.tasks"]
)
app.config_from_envvar('CELERY_CONFIG_MODULE')


if __name__ == '__main__':
    app.start()

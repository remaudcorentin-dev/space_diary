"""Configuration for Space Diary

if environment var 'SPACE_DIARY_CONFIG' is given, then the value will be open
by yaml parser and contents will override variables here.
"""
import os
import sys

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "Europe/Paris"

BROKER_URL = "redis://"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

COUCH_DB_HOST = "http://localhost:5984/"

diary_config = None
_config_loaded = False


def load(reload=False):
    """Load configuration from file."""
    global diary_config, _config_loaded
    if not _config_loaded or reload:
        try:
            diary_config = os.environ.get("SPACE_DIARY_CONFIG", None)
            if diary_config is not None and os.path.exists(diary_config):
                import yaml  # NOQA
                import pydash  # NOQA
                with open(diary_config, 'r') as diary_config_file:
                    this = sys.modules[__name__]
                    yaml_config = yaml.load(diary_config_file.read())
                    print(yaml_config)
                    for key, val in yaml_config.items():
                        setattr(this, pydash.snake_case(key).upper(), val)
        except KeyError:
            diary_config = None

load()

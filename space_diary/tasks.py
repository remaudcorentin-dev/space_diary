"""Space Diary tasks"""
from space_diary.celery import app
from space_diary.config import COUCH_DB_HOST
import couchdb
from couchdb.http import ResourceNotFound
from uuid import uuid4


@app.task
def add_api_operation(operation):
    """Add api operation to couchdb."""
    server = couchdb.Server(url=COUCH_DB_HOST)
    try:
        db = server['logs']
    except ResourceNotFound:
        db = server.create('logs')

    doc_id = uuid4().hex
    db[doc_id] = operation

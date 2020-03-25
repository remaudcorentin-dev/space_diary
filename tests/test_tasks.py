"""Task tests."""

import os
from unittest import TestCase, mock
from datetime import datetime
from tests.mock_couchdb import couchdb_patch
import builtins
import importlib
from space_diary import config


class TestTasks(TestCase):
    """Test tasks."""

    @couchdb_patch
    def test_adding_document_to_db(self, server_mock):
        """Test adding documents to db."""
        from space_diary import tasks

        operation = {
            "url": "/api/v1/user/1",
            "method": "PATCH",
            "data": {"full_name": "smth"},
            "timestamp": datetime.utcnow().isoformat()
        }

        tasks.add_api_operation(operation)

        self.assertEqual(1, len(server_mock.server['logs']))


def test_config(monkeypatch):


    with mock.patch("builtins.open") as open_mock:
        monkeypatch.setenv("SPACE_DIARY_CONFIG", "/etc/space_diary.yaml")
        enter = open_mock.return_value
        mock_file = enter.__enter__.return_value

        def mock_read(buf=None):
            return """
            couchDbHost: http://couchdb:5984/
            """

        mock_file.read.side_effect = mock_read

        importlib.reload(config)
        monkeypatch.setattr("os.path.exists", lambda x: True)
        config.load(reload=True)

        assert "/etc/space_diary.yaml" == config.diary_config
        assert "http://couchdb:5984/" == config.COUCH_DB_HOST

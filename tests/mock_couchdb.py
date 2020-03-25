"""This module contains couchdb mocking"""

from collections import defaultdict
from functools import reduce, wraps
from hashlib import md5
from unittest.mock import Mock
from unittest.mock import patch
from uuid import uuid4

from couchdb.client import Database
from couchdb.client import Document
from couchdb.client import Server
from couchdb.client import View
from couchdb.client import ViewResults
from couchdb.http import ResourceNotFound

import pydash
from addict import Dict


def hash_query(map_fun, reduce_fun=""):
    """Calculate hash for query"""
    hash = md5()
    hash.update(map_fun)
    hash.update(reduce_fun)
    return hash.hexdigest()


class UnexpectedQuery(Exception):
    pass


class QueryNotExecuted(Exception):
    pass


class IteratedList(list):

    def __init__(self, *args, **kwargs):
        """Init the object"""
        self.position = 0
        super(IteratedList, self).__init__(*args, **kwargs)

    def next(self):
        """Return the next value."""
        try:
            value = list[self.position]
            self.position += 1
            return value
        except IndexError:
            # come back to the beginning
            self.position = 0
            return self.next()


class MockViewResults(ViewResults):

    def __init__(self, view, when_object, database, options=None):
        self.options = options or {}
        self.view = view
        self.when_object = when_object
        self.database = database

    def _fetch(self):
        offset = 0
        if self.options.get('key', None) is None:
            start_key = self.options.get('startkey', 0)
            end_key = self.options.get('endkey',
                                       len(self.when_object.document_ids))
            self._rows = [
                Row(self.database[row_id])
                for row_id in self.when_object.document_ids[start_key:end_key]
                ]
            offset = start_key
        else:
            key = self.options['key']
            # wrap it in list, as _rows has to be a list
            self._rows = [Row(
                self.database[self.when_object.document_ids[key]])]
            offset = key

        self._total_rows = len(self.when_object.document_ids)
        self._offset = offset
        self._update_seq = 0

    def __getitem__(self, key):
        options = self.options.copy()
        if isinstance(key, slice):
            if key.start is not None:
                options['startkey'] = key.start
            if key.end is not None:
                options['endkey'] = key.end
        else:
            options['key'] = key

        return MockViewResults(self.view, self.when_object, self.database,
                               options)


class MockView(View):

    def __init__(self, database, when_object):

        self.database = database
        self.when_object = when_object

    def __call__(self, **options):
        return MockViewResults(self, self.when_object, self.database, options)


class CouchDbDatabaseMock(Database):
    """Mock class for CouchDB Database."""

    def __init__(self, url, name, *args, **kwargs):
        """Init of the mock.

        :param url: url to the resource
        :param name: string name of the database
        :param session: not used, kept for consistency
        """
        self._name = name
        self.resource = Dict()
        self.resource.url = url
        self.__expected_queries = defaultdict(IteratedList)
        self.__documents = {}

    @property
    def name(self):
        """Name of the database."""
        return self._name

    @property
    def documents(self):
        """Return documents for this mock."""
        return self.__documents

    @documents.setter
    def set_documents(self, documents):
        """Set mock documents.

        :param documents: dictionary of documents
        :type documents: dict
        """
        self.__documents = documents

    def __contains__(self, document_id):
        """Check if document is in mocked documents."""
        def find_key(result, key):
            if result:
                return result
            else:
                return key == document_id
        return reduce(find_key, self.documents.keys(), False)

    def __iter__(self):
        """Return IDs of mocked documents"""
        return iter(self.documents.keys())

    def __len__(self):
        """Number of mocked documents"""
        return len(self.documents)

    def __nonzero__(self):
        """Check if any documents are available."""
        return len(self.documents) > 0

    def __delitem__(self, id):
        """Remove mocked document."""
        del self.__documents[id]

    def __getitem__(self, id):
        """Return mocked document by id."""
        doc = self.documents[id]
        if "_id" not in doc:
            doc['_id'] = id

        return Document(self.documents[id])

    def __setitem__(self, id, content):
        """Save the document."""
        self.documents[id] = content

    def save(self, doc, **options):
        """Save the document if exists or create new one."""
        if "_id" not in doc:
            doc['_id'] = uuid4().hex
        if "_rev" in doc:
            doc['_rev'] = doc['_rev']+1
        else:
            doc['_rev'] = 1
        self.documents[doc['_id']] = doc
        return doc['_id'], doc['_rev']

    def set_reponse_for_query(self, query, when_object):
        """Set response for query."""
        if isinstance(query, tuple):
            query = hash_query(query[0], query[1])
        else:
            query = hash_query(query)
        self.__expected_queries[query].append(when_object)

    def query(self, map_fun, reduce_fun="", language="javascript",
              wrapper=None, **options):
        """Return mocked results for query."""
        query_hash = hash_query(map_fun, reduce_fun)

        try:
            when_object = self.__expected_queries[query_hash]
            return MockView(self, when_object)()
        except KeyError:
            raise UnexpectedQuery("{} {}".format(map_fun, reduce_fun))


class CouchWhen(object):
    """Helper class for defining mocks."""
    def __init__(self, server, database_name, query_func=None,
                 reduce_func=None):
        """Init object.

        :param server: object of the server mock for back reference
        :param database_name: name of the database to mock
        :param query_func: string with query function that should be passed
            to couch db
        """
        self.server = server
        self.database_name = database_name
        self.query_func = query_func or ""
        self.reduce_func = reduce_func or ""
        self.document_ids = []
        self.executed = False

    def respond(self, documents):
        """Save the documents for the query

        :param documents: documents that should be returned
        """
        self.documents = documents

        if self.database_name not in self.server:
            db = self.server.create(self.database_name)
        else:
            db = self.server[self.database_name]

        for document in documents:
            id, _ = db.save(document)
            self.document_ids.append(id)

    def mark_executed(self):
        """Mark this when object as executed."""
        self.executed = True

    def __repr__(self):

        return "<CouchWhen : {} : {}>".format(self.query_func,
                                              self.reduce_func)

    def verify(self):
        """Verify if the object was executed.

        If not it will raise QueryNotExecuted.

        :raise QueryNotExecuted:
        """
        if not self.executed:
            raise QueryNotExecuted(str(self))


class CouchDbServerMock(Server):
    """Mock class for CouchDB Server connection."""

    def __init__(self, url, *args, **kwargs):
        """Init mock server connection"""
        self.resource = Dict()
        self.resource.url = url
        self.__databases = []
        self.__database_objects = {}
        self.__when_objects = []

    @property
    def databases(self):
        """Return databases"""
        return self.__databases

    @databases.setter
    def set_databases(self, databases):
        """Set databases for mock.

        :param databases: list of databases
        :type databases: list[str]
        """
        self.__databases = databases

    def create(self, name):
        """Create database."""
        self.__databases.append(name)
        self.__database_objects[name] = CouchDbDatabaseMock(
            self.resource.url, name=name
        )
        return self[name]

    def when(self, database_name, query_func, reduce_func=None):
        """Helper for declaring mocked documents"""
        when_object = CouchWhen(server, database_name, query_func, reduce_func)
        self.__when_objects.append(when_object)
        return when_object

    def verify_outstanding_requests(self):
        """Verify all when objects if they were executed."""
        [when_object.verify() for when_object in self.__when_objects]

    def __contains__(self, name):
        """Mock."""
        return name in self.databases

    def __nonzero__(self):
        """Mock."""
        return len(self.databases) > 0

    def __len__(self):
        """Return number of mocked databases."""
        return len(self.databases)

    def __delitem__(self, name):
        """Mock delete of database."""
        self.databases = [db for db in self.databases if db != name]

    def __getitem__(self, name):
        """Return mocked database."""
        try:
            return self.__database_objects[name]
        except KeyError:
            raise ResourceNotFound("Not found")


class CouchMock(object):

    def __init__(self):
        self.server = None

    def __call__(self, *args, **kwargs):
        if self.server is None:
            self.server = CouchDbServerMock(*args, **kwargs)
        return self.server


def couchdb_patch(func):
    """Add monkey patching for couchdb."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """Monkey patch couchdb"""
        with patch("couchdb.Server", CouchMock()) as couch_mock:
            args = args + (couch_mock, )
            return func(*args, **kwargs)
    return wrapper

#!/usr/bin/env python
# coding: utf-8
import logging

from pymongo.cursor import Cursor
from pymongo.collection import Collection
from bson.son import SON


class MongoLogEvent(object):
    """
    Interface betwen patched pymongo objects and extractors
    """
    def __init__(self, obj=None, method_name=None, run_time=None, call_args=None, call_kwargs=None, return_data=None):
        self.obj = obj
        self.method_name = method_name
        self.run_time = run_time if isinstance(run_time, float) else -1.0
        self.call_args = call_args if isinstance(call_args, tuple) else []
        self.call_kwargs = call_kwargs if isinstance(call_kwargs, dict) else {}
        self.return_data = return_data


class BaseExtractor(object):
    def __init__(self, event):
        if not isinstance(event, MongoLogEvent):
            raise TypeError('"MongoLogEvent" obj required.')
        self.event = event

    def log(self):
        logger = logging.getLogger('mongolog')
        #extracted_data = {"x_%s" % k: v for k, v in self.extract_data().iteritems()}
        extracted_data = self.extract_data()
        logger.info('', extra=extracted_data)

    def extract_data(self):
        event = self.event
        extracted_data = {
            'conn_host': None,
            'conn_port': None,
            'db_name':  None,
            'coll_name': None,
            'coll_full_name': None,
            'coll_read_preference': None,

            'run_time': event.run_time,
            'method': None,
            'response': None,
            'docs_involved': None,
            'spec': None,
            'limit': None,
            'skip': None,
            'fields': None,
            'document': None,
            'upsert': None,
            'multi': None,
            'w': None,
            'wtimeout': None,
            'wtimeoutms': None,
            'fsync': None,
            'j': None,
            'journal': None,
        }
        extracted_data.update(self.event_obj_data(event.obj))

        if event.method_name in ('insert', 'remove', 'update') and isinstance(event.obj, Collection):
            req_data = self.extract_collection_data()
        elif event.method_name == '__send_message' and isinstance(event.obj, Cursor):
            req_data = self.extract_cursor_data()
        else:
            raise NotImplementedError()

        extracted_data.update(req_data)
        return extracted_data

    def extract_collection_data(self):
        extracted_data = {}
        event = self.event

        #_, write_concern_dict =  event.obj._get_write_mode(None, **event.call_kwargs)

        extracted_data['spec'] = event.call_args[0]
        extracted_data['method'] = event.method_name
        extracted_data['response'] = event.return_data

        if event.method_name == 'insert':
            extracted_data['docs_involved'] = len(event.return_data)
        elif event.method_name == 'remove':
            extracted_data['docs_involved'] = event.return_data.get('n')
        elif event.method_name == 'update':
            extracted_data['document'] = event.call_args[1]
            extracted_data['docs_involved'] = event.return_data.get('n')
            extracted_data['document'] = event.call_args[1]
            extracted_data['upsert'] = event.call_args[2] if len(event.call_args) >= 3 else event.call_kwargs.get('upsert')
            extracted_data['multi'] = event.call_args[5] if len(event.call_args) >= 6 else event.call_kwargs.get('multi')

        return extracted_data

    def extract_cursor_data(self):
        extracted_data = {}
        cursor = self.event.obj

        spec = cursor._Cursor__spec
        extracted_data['response'] = cursor._Cursor__data
        if isinstance(spec, SON):
            son_data = dict(spec)
            extracted_data['method'] = 'count'
            extracted_data['spec'] = son_data.pop('query')
            extracted_data['fields'] = son_data.pop('fields')
            extracted_data['coll_name'] = son_data.pop('count')
            extracted_data['docs_involved'] = cursor._Cursor__data[0].get('n')
        else:
            extracted_data['method'] = 'find'
            extracted_data['docs_involved'] = cursor._Cursor__retrieved
            extracted_data['spec'] = spec
            extracted_data['limit'] = cursor._Cursor__limit
            extracted_data['skip'] = cursor._Cursor__skip
            extracted_data['fields'] = cursor._Cursor__fields
        return extracted_data

    @classmethod
    def event_obj_data(cls, obj):
        if isinstance(obj, Cursor):
            mongo_objs = cls.mongo_objs_from_cursor(obj)
        elif isinstance(obj, Collection):
            mongo_objs = cls.mongo_objs_from_collection(obj)
        else:
            raise NotImplementedError()
        return cls.mongo_objs_data(*mongo_objs)

    @classmethod
    def mongo_objs_from_cursor(cls, cursor):
        return cls.mongo_objs_from_collection(cursor._Cursor__collection)

    @staticmethod
    def mongo_objs_from_collection(collection):
        database = collection.database
        connection = database.connection
        return connection, database, collection

    @staticmethod
    def mongo_objs_data(connection=None, database=None, collection=None):
        result = {}
        if connection:
            result.update({
                'conn_host': connection.host,
                'conn_port': connection.port,
            })
        if database:
            result.update({'db_name': database.name})
        if collection:
            result.update({
                'coll_name': collection.name,
                'coll_full_name': collection.full_name,
                'coll_read_preference': collection.read_preferences,
            })
        return result

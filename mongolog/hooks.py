#!/usr/bin/env python
# coding: utf-8
import time
import copy

from pymongo.cursor import Cursor
from pymongo.collection import Collection
from mongolog.extractors import BaseExtractor, MongoLogEvent


class MongoLogBasePatch(object):
    """
    Base class for patched pymongo objects
    """
    monog_log_extractor_class = BaseExtractor

    def mongo_log_callback(self, event):
        self.monog_log_extractor_class(event).log()


class MongoLogCursor(MongoLogBasePatch, Cursor):
    """
    Patched pymongo.cursor.Cursor
    """

    def _Cursor__send_message(self, *args, **kwargs):
        start = time.time()
        super(MongoLogCursor, self)._Cursor__send_message(*args, **kwargs)
        run_time = time.time() - start

        callback_obj = MongoLogEvent(obj=self, run_time=run_time,
                                     method_name='__send_message',
                                     call_args=args, call_kwargs=kwargs)
        self.mongo_log_callback(callback_obj)


class MongoLogCollection(MongoLogBasePatch, Collection):
    """
    Patched pymongo.collection.Collection
    """
    MONGO_LOG_PATCH_METHODS = ('insert', 'remove', 'update')

    def __init__(self, *args, **kwargs):
        super(MongoLogCollection, self).__init__(*args, **kwargs)
        for method_name in self.MONGO_LOG_PATCH_METHODS:
            setattr(self, method_name, self._mongo_log_plug(method_name))

    def _mongo_log_plug(self, method_name):
        def patched_method(*args, **kwargs):
            call_args = copy.deepcopy(args)
            call_kwargs = copy.deepcopy(kwargs)

            start_time = time.time()
            result = getattr(super(MongoLogCollection, self), method_name)(*args, **kwargs)
            run_time = time.time() - start_time
            callback_obj = MongoLogEvent(obj=self, run_time=run_time,
                                         method_name=method_name,
                                         call_args=call_args, call_kwargs=kwargs,
                                         return_data=result)
            self.mongo_log_callback(callback_obj)
            return result
        return patched_method

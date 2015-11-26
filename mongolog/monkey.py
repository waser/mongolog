#!/usr/bin/env python
# coding: utf-8

import pymongo
from contextlib import contextmanager

from mongolog.hooks import MongoLogCursor, MongoLogCollection

SUPPORTED_PYMONGO_VERSIONS = ('2.6.3',)

if pymongo.version not in SUPPORTED_PYMONGO_VERSIONS:
    raise NotImplementedError('"mongolog" supports only versions: %s pymongo' % SUPPORTED_PYMONGO_VERSIONS)


@contextmanager
def patched_pymongo():
    """
    Allow localy patch pymongo

    with patch_pymongo:
        coll.find({_id: '1'})
    """
    original_cursor = pymongo.cursor.Cursor
    original_collection = pymongo.collection.Collection
    try:
        pymongo.collection.Cursor = MongoLogCursor
        pymongo.database.Collection = MongoLogCollection
        yield
    finally:
        pymongo.collection.Cursor = original_cursor
        pymongo.database.Collection = original_collection


def patch_pymongo():
    """
    Patch pymongo
    """
    pymongo.collection.Cursor = MongoLogCursor
    pymongo.database.Collection = MongoLogCollection

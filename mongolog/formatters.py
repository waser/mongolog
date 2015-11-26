#!/usr/bin/env python
# coding: utf-8

import logging


class MongoLogFormatter(logging.Formatter):
    prefix = '%(asctime)s %(name)s %(conn_host)s:%(conn_port)s.%(db_name)s.%(coll_name)s.%(method)s'
    suffix = ' %(docs_involved)s %(run_time)0.4f'
    format_map = {
        'find': '%s%s%s' % (prefix, '(%(spec)s, fields=%(fields)s, skip=%(skip)s, limit=%(limit)s)', suffix),
        'count': '%s%s%s' % (prefix, '(%(spec)s) %(docs_involved)s', suffix),
        'update': '%s%s%s' % (prefix, '(%(spec)s, multi=%(multi)s, upsert=%(upsert)s)', suffix),
        'insert': '%s%s%s' % (prefix, '(%(spec)s)', suffix),
        'remove': '%s%s%s' % (prefix, '(%(spec)s)', suffix),
    }

    def format(self, record):
        original_fmt = self._fmt
        try:
            if getattr(record, 'method') in self.format_map:
                self._fmt = self.format_map[record.method]
            return super(MongoLogFormatter, self).format(record)
        finally:
            self._fmt = original_fmt

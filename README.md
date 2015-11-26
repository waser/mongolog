# mongolog
Client side logging for pymongo
## Usage
To start logging requests to mongo you need:

1. Setup loggers using `logging`
2. Patch pymongo driver

Example:
```
import sys
import logging
from pymongo import MongoClient
from mongolog.monkey import patch_pymongo
from mongolog.formatters import MongoLogFormatter

# Prepare logging
fmt = MongoLogFormatter()
hdlr = logging.StreamHandler(sys.stdout)
hdlr.setFormatter(fmt)
logging.root.addHandler(hdlr)
logging.root.setLevel(logging.INFO)

# Patch pymongo driver
patch_pymongo()

# Now, try it!
client = MongoClient()
collection = client['test_db']['test_coll']

collection.insert([{'num': i} for i in xrange(3)])
collection.find({'num': {'$gte': 1}}).count()
collection.update({'num': {'$gte': 1}}, {'$set': {'num': 2}}, multi=True)
collection.find({'num': {'$gte': 1}}, {'num': 1})[:]
collection.remove({})
```
Will be promted to STDOUT
```
2015-11-26 15:40:06,805 mongolog localhost:27017.test_db.test_coll.insert([{'num': 0}, {'num': 1}, {'num': 2}]) 3 0.1102
2015-11-26 15:40:06,806 mongolog localhost:27017.test_db.test_coll.count({'num': {'$gte': 1}}) 2 2 0.0006
2015-11-26 15:40:06,806 mongolog localhost:27017.test_db.test_coll.update({'num': {'$gte': 1}}, multi=True, upsert=None) 2 0.0002
2015-11-26 15:40:06,806 mongolog localhost:27017.test_db.test_coll.remove({}) 3 0.0002
```

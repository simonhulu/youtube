import __builtin__, sys
import re
import codecs
import json
import jsonpickle
from flask import Response
from bson import ObjectId

class YTBJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o,ObjectId):
            return str(o)
        return json.JSONEncoder.default(self,o)

try:
    from _codecs import *
except ImportError, why:
    raise SystemError('Failed to load the builtin codecs: %s' % why)
def uppercase_escape(s):
    unicode_escape = codecs.getdecoder('unicode_escape')
    return re.sub(
        r'\\U[0-9a-fA-F]{8}',
        lambda m: unicode_escape(m.group(0))[0],
        s)
def jsonresponse(data):
    return Response(jsonpickle.encode(data,unpicklable=False),mimetype='application/json')
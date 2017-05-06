import __builtin__, sys
import re
import codecs
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
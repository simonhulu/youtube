
from enum import IntEnum
class Imeili100ResultStatus(IntEnum):
        ok,failed = range(2)


class Imeili100Result():
    def __init__(self):
        self.status = Imeili100ResultStatus.ok
        self.res = None



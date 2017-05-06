
from enum import Enum
class Imeili100ResultStatus(Enum):
        ok,failed = range(2)


class Imeili100Result():
    def __init__(self):
        self.status = Imeili100ResultStatus.ok
        self.res = None



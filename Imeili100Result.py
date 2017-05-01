
from enum import Enum
class Imeili100ResultStatus(Enum):
        ok = 0
        failed = 1


class Imeili100Result():
    def __init__(self):
        self.status = Imeili100ResultStatus.ok
        self.res = None



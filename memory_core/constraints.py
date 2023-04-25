from enum import Enum
import random


class SparseSequenceConstraints(Enum):
    ZERO = 1
    ONE = 2
    LT100 = 3
    LT250 = 4


class SparseOpMatchDensity(Enum):
    NONE = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    ALL = 5


class SparseSequenceGenerator():

    const_class = SparseSequenceConstraints.ZERO

    def __init__(self, constraint_class=SparseSequenceConstraints.ZERO):
        self.const_class = constraint_class

    def set_constraint_class(self, constraint_class):
        self.const_class = constraint_class

    def get_length(self):
        print(f"Getting length on class {self.const_class}")
        if self.const_class == SparseSequenceConstraints.ZERO:
            return 0
        elif self.const_class == SparseSequenceConstraints.ONE:
            return 1
        elif self.const_class == SparseSequenceConstraints.LT100:
            return random.randint(2, 100)
        elif self.const_class == SparseSequenceConstraints.LT250:
            return random.randint(101, 250)
        else:
            return 0


class SparseOpMatchGenerator():
    def __init__(self):
        return

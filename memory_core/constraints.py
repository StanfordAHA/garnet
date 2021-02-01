from enum import Enum
import random

class SparseSequenceConstraints(Enum):
    ZERO = 1
    ONE = 2
    LT100 = 3
    LT250 = 4

class SparseSequenceGenerator():
    const_class = SparseSequenceConstraints.ZERO
    def __init__(constraint_class):
        self.const_class = constraint_class

    def get_length(self):
        if self.const_class == SparseSequenceConstraints.ZERO:
            return 0
        elif self.const_class == SparseSequenceConstraints.ONE:
            return 1
        elif self.const_class == SparseSequenceConstraints.LT100:
            return random.randint(0, 100)
        elif self.const_class == SparseSequenceConstraints.LT250:
            return random.randint(0, 100)
        else:
            return 0

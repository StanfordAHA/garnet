from enum import Enum


class MemoryMode(Enum):
    UNIFIED_BUFFER = 0
    ROM = 1
    SRAM = 2
    FIFO = 3

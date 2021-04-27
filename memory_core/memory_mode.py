from enum import Enum


class MemoryMode(Enum):
    UNIFIED_BUFFER = "lake"
    ROM = 1
    SRAM = 2
    FIFO = 3

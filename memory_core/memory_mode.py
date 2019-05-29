from enum import Enum


class Mode(Enum):
    LINE_BUFFER = 0
    FIFO = 1
    SRAM = 2
    DB = 3

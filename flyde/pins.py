from enum import Enum


class InputPinMode(Enum):
    QUEUE = "queue"
    STICKY = "sticky"
    STATIC = "static"


class InputPin:
    """Input pin definition for a node"""
    description: str
    mode: InputPinMode

    def __init__(self, description: str = '', mode: InputPinMode = InputPinMode.QUEUE):
        self.description = description
        self.mode = mode


class OutputPin:
    """Output pin definition for a node"""
    description: str
    delayed: bool

    def __init__(self, description: str = '', delayed: bool = False):
        self.description = description
        self.delayed = delayed

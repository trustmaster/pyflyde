from _typeshed import Incomplete as Incomplete
from enum import Enum
from queue import Queue
from typing import Any

EOF: Incomplete

def is_EOF(value: Any) -> bool: ...

class InputMode(Enum):
    QUEUE: str
    STICKY: str
    STATIC: str

class Requiredness(Enum):
    REQUIRED: str
    OPTIONAL: str
    REQUIRED_IF_CONNECTED: str

class OutputMode(Enum):
    REF: str
    VALUE: str
    CIRCLE: str

class Input:
    id: Incomplete
    description: Incomplete
    type: Incomplete
    required: Incomplete
    def __init__(self, /, id: str = '', description: str = '', mode: InputMode = ..., type: type | None = None, value: Any = None, required: Requiredness = ...) -> None: ...
    @property
    def queue(self) -> Queue: ...
    @property
    def value(self) -> Any: ...
    @value.setter
    def value(self, value: Any): ...
    def get(self) -> Any: ...
    def empty(self) -> bool: ...
    def count(self) -> int: ...

class Output:
    id: Incomplete
    description: Incomplete
    type: Incomplete
    delayed: Incomplete
    def __init__(self, /, id: str = '', description: str = '', mode: OutputMode = ..., type: type | None = None, delayed: bool = False) -> None: ...
    def connect(self, queue: Queue): ...
    @property
    def connected(self) -> bool: ...
    def send(self, value: Any): ...

class RedirectQueue:
    def __init__(self, output: Output) -> None: ...
    def put(self, item: Any, block: bool = True, timeout: Incomplete | None = None): ...

class GraphPort(Input, Output):
    def __init__(self, id: str = '', description: str = '', type: type | None = None, value: Any = None, required: Requiredness = ..., output_mode: OutputMode = ..., delayed: bool = False) -> None: ...

class ConnectionNode:
    ins_id: Incomplete
    pin_id: Incomplete
    def __init__(self, ins_id: str, pin_id: str) -> None: ...

class Connection:
    from_node: Incomplete
    to_node: Incomplete
    delayed: Incomplete
    hidden: Incomplete
    def __init__(self, from_node: ConnectionNode, to_node: ConnectionNode, delayed: bool = False, hidden: bool = False) -> None: ...
    @classmethod
    def from_yaml(cls, yml: dict): ...
    def to_dict(self) -> dict: ...

from _typeshed import Incomplete
from enum import Enum
from queue import Queue
from typing import Any

EOF: Incomplete

def is_EOF(value: Any) -> bool:
    """Checks if a value is an EOF signal."""

class InputMode(Enum):
    """InputMode is the mode of an input.

    QUEUE: The input is connected to a queue. On each node invocation, a new value is taken from the queue.
    If the queue is empty, the node invocation is blocked.
    STICKY: The input has a sticky value. It has a queue attached to it, but the last received value is returned in
    absence of new values in the queue. Thus sticky inputs are non-blocking.
    STATIC: The input has a static value that does not change."""
    QUEUE = 'queue'
    STICKY = 'sticky'
    STATIC = 'static'

class Requiredness(Enum):
    """Requiredness of an input.

    REQUIRED: The input is required to be connected.
    OPTIONAL: The input is optional.
    REQUIRED_IF_CONNECTED: The input is required if it is connected to a queue."""
    REQUIRED = 'required'
    OPTIONAL = 'optional'
    REQUIRED_IF_CONNECTED = 'required-if-connected'

class OutputMode(Enum):
    """OutputMode defines the behavior of an output if it is connected to multiple input queues.

    REF: Copy-by-reference. Each connected input will receive the same object.
    VALUE: Copy-by-value. Each connected input will receive a deep copy of the object.
    CIRCLE: Circular. Each connected input will receive the object in a round-robin fashion.
    """
    REF = 'ref'
    VALUE = 'value'
    CIRCLE = 'circle'

class Input:
    """Input is an interface for getting input/output data for a node."""
    id: Incomplete
    description: Incomplete
    type: Incomplete
    _input_mode: Incomplete
    _value: Incomplete
    required: Incomplete
    _ref_count: int
    def __init__(self, /, id: str = '', description: str = '', mode: InputMode = ..., type: type | None = None, value: Any = None, required: Requiredness = ...) -> None:
        """Create a new input object.

        Args:
            id (str): The ID of the input
            description (str): The description of the input
            mode (InputMode): The mode of the input
            typ (type): The type of the input
            value (Any): The value of the input for InputMode = InputMode.STATIC or InputMode = InputMode.STICKY
            required (Required): The requiredness of the input
        """
    _queue: Incomplete
    @property
    def queue(self) -> Queue:
        """Get the queue of the input."""
    @property
    def is_connected(self) -> bool:
        """Check if the input is connected to a queue."""
    @property
    def value(self) -> Any:
        """Get the static value associated with the input."""
    @value.setter
    def value(self, value: Any):
        """Set the static value of the input."""
    def get(self) -> Any:
        """Get the value of the input from either the queue or static value."""
    def empty(self) -> bool:
        """Check if the input queue is empty."""
    def count(self) -> int:
        """Get the number of elements in the input queue."""
    def inc_ref_count(self) -> None:
        """Increment the reference count of the input."""
    def dec_ref_count(self) -> None:
        """Decrement the reference count of the input."""
    @property
    def ref_count(self) -> int:
        """Get the reference count of the input."""

class Output:
    """Output is an interface for setting output data for a component."""
    id: Incomplete
    description: Incomplete
    _output_mode: Incomplete
    type: Incomplete
    delayed: Incomplete
    _queues: Incomplete
    _circle_index: int
    def __init__(self, /, id: str = '', description: str = '', mode: OutputMode = ..., type: type | None = None, delayed: bool = False) -> None:
        """Create a new output object.

        Args:
            id (str): The ID of the output
            description (str): The description of the output
            type (type): The type of the output
            delayed (bool): If the output is delayed [not implemented yet]
        """
    def connect(self, queue: Queue):
        """Connect a queue to the output.

        This method can be called multiple times to connect multiple queues to the same output.
        """
    @property
    def connected(self) -> bool:
        """Check if the output is connected to a queue."""
    def send(self, value: Any):
        """Put a value in the output queue."""

class RedirectQueue:
    """RedriveQueue is a fake write-only queue that is used by GraphPort
    to redrive input values to the output queues."""
    _output: Incomplete
    _ref_count: int
    def __init__(self, output: Output) -> None: ...
    @property
    def ref_count(self) -> int: ...
    def inc_ref_count(self) -> None: ...
    def dec_ref_count(self) -> None: ...
    def put(self, item: Any, block: bool = True, timeout: Incomplete | None = None): ...

class GraphPort(Input, Output):
    """GraphPort is an interface between inside and outside of the graph used for input/output.

    It combines Input and Output, because Graph Input acts as an Input for outside world,
    but outputs values inside the graph. Similarly, Graph Output acts as an Output for outside world,
    but receives values from inside the graph."""
    _queue: Incomplete
    def __init__(self, id: str = '', description: str = '', type: type | None = None, value: Any = None, required: Requiredness = ..., output_mode: OutputMode = ..., delayed: bool = False) -> None: ...
    def inc_ref_count(self): ...
    def dec_ref_count(self): ...

class ConnectionNode:
    """ConnectionNode is a combination of a node and an input/output pin.

    It is used as a source or destination of a connection."""
    ins_id: Incomplete
    pin_id: Incomplete
    def __init__(self, ins_id: str, pin_id: str) -> None: ...

class Connection:
    """Connection is a connection between two nodes in a graph."""
    from_node: Incomplete
    to_node: Incomplete
    delayed: Incomplete
    hidden: Incomplete
    def __init__(self, from_node: ConnectionNode, to_node: ConnectionNode, delayed: bool = False, hidden: bool = False) -> None: ...
    @classmethod
    def from_yaml(cls, yml: dict):
        """Create a connection from a parsed YAML dictionary."""
    def to_dict(self) -> dict: ...

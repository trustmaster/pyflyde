from enum import Enum
from typing import Any, Optional
from queue import Queue

EOF = Exception("__EOF__")
"""EOF is a signal to indicate the end of data."""


def is_EOF(value: Any) -> bool:
    """Checks if a value is an EOF signal."""
    return isinstance(value, Exception) and value.args[0] == "__EOF__"


class InputMode(Enum):
    """InputMode is the mode of an input.

    QUEUE: The input is connected to a queue. On each node invocation, a new value is taken from the queue.
    If the queue is empty, the node invocation is blocked.
    STICKY: The input has a sticky value. It has a queue attached to it, but the last received value is returned in
    absence of new values in the queue. Thus sticky inputs are non-blocking.
    STATIC: The input has a static value that does not change."""
    QUEUE = "queue"
    STICKY = "sticky"
    STATIC = "static"


class Requiredness(Enum):
    """Requiredness of an input.

    REQUIRED: The input is required to be connected.
    OPTIONAL: The input is optional.
    REQUIRED_IF_CONNECTED: The input is required if it is connected to a queue."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    REQUIRED_IF_CONNECTED = "required-if-connected"


class Input:
    """Input is an interface for getting input/output data for a node."""

    def __init__(
        self,
        /,
        id: str = "",
        description: str = "",
        mode: InputMode = InputMode.QUEUE,
        type: Optional[type] = None,
        value: Any = None,
        required: Requiredness = Requiredness.REQUIRED,
    ):
        """Create a new input object.

        Args:
            id (str): The ID of the input
            description (str): The description of the input
            mode (InputMode): The mode of the input
            typ (type): The type of the input
            value (Any): The value of the input for InputMode = InputMode.STATIC or InputMode = InputMode.STICKY
            required (Required): The requiredness of the input
        """
        self.id = id
        self.description = description
        self.type = type
        self.mode = mode
        self.value = None
        if value is not None:
            if self.type is not None and not isinstance(value, type):  # type: ignore
                raise ValueError(f"Value {value} is not of type {self.type}")
            self.value = value
        self.required = required

    def connect(self, queue: Queue):
        """Connect the input to a queue."""
        self.queue = queue

    def set_value(self, value: Any):
        """Set the value of the input."""
        # Can be set to EOF to indicate end of data
        if self.type is not None and not is_EOF(value) and not isinstance(value, self.type):  # type: ignore
            raise ValueError(f"Value {value} is not of type {self.type}")
        self.value = value

    def get(self) -> Any:
        """Get the value of the input."""
        if self.mode == InputMode.QUEUE:
            value = self.queue.get()
            if is_EOF(value):
                raise EOF
            return value

        return self.value

    def empty(self) -> bool:
        """Check if the input queue is empty."""
        if self.mode == InputMode.QUEUE:
            return self.queue.empty()
        return self.value is None

    def count(self) -> int:
        """Get the number of elements in the input queue."""
        if self.mode == InputMode.QUEUE:
            return self.queue.qsize()
        return 1


class Output:
    """Output is an interface for setting output data for a component."""

    def __init__(
        self,
        /,
        id: str = "",
        description: str = "",
        type: Optional[type] = None,
        delayed: bool = False
    ):
        """Create a new output object.

        Args:
            id (str): The ID of the output
            description (str): The description of the output
            type (type): The type of the output
            delayed (bool): If the output is delayed [not implemented yet]
        """
        self.id = id
        self.description = description
        self.type = type
        self.delayed = delayed

    def connect(self, queue: Queue):
        """Connect the output to a queue."""
        self.queue = queue

    def send(self, value: Any):
        """Put a value in the output queue."""
        if self.type is not None and not is_EOF(value) and not isinstance(value, self.type):  # type: ignore
            raise ValueError(
                f'Error in output "{self.id}": value {value} is not of type {self.type}'
            )
        self.queue.put(value)


class ConnectionNode:
    """ConnectionNode is a combination of a node and an input/output pin.

    It is used as a source or destination of a connection."""

    def __init__(self, ins_id: str, pin_id: str):
        self.ins_id = ins_id
        self.pin_id = pin_id


class Connection:
    """Connection is a connection between two nodes.

    Typically a connection has a queue attached to it."""

    def __init__(
        self,
        from_node: ConnectionNode,
        to_node: ConnectionNode,
        delayed: bool = False,
        hidden: bool = False,
    ):
        self.from_node = from_node
        self.to_node = to_node
        self.delayed = delayed
        self.hidden = hidden

    def set_queue(self, queue: Queue):
        """Set the queue for the connection."""
        self.queue = queue

    @classmethod
    def from_yaml(cls, yml: dict):
        """Create a connection from a parsed YAML dictionary."""
        return cls(
            ConnectionNode(yml["from"]["insId"], yml["from"]["pinId"]),
            ConnectionNode(yml["to"]["insId"], yml["to"]["pinId"]),
            yml.get("delayed", False),
            yml.get("hidden", False),
        )

    def to_dict(self) -> dict:
        return {
            "from": {"insId": self.from_node.ins_id, "pinId": self.from_node.pin_id},
            "to": {"insId": self.to_node.ins_id, "pinId": self.to_node.pin_id},
            "delayed": self.delayed,
            "hidden": self.hidden,
        }

from copy import deepcopy
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


class OutputMode(Enum):
    """OutputMode defines the behavior of an output if it is connected to multiple input queues.

    REF: Copy-by-reference. Each connected input will receive the same object.
    VALUE: Copy-by-value. Each connected input will receive a deep copy of the object.
    CIRCLE: Circular. Each connected input will receive the object in a round-robin fashion.
    """

    REF = "ref"
    VALUE = "value"
    CIRCLE = "circle"


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
        self._input_mode = mode
        self._value = None
        if value is not None:
            if self.type is not None and not isinstance(value, type):  # type: ignore
                raise ValueError(f"Value {value} is not of type {self.type}")
            self._value = value
        self.required = required
        self._ref_count = 0

    @property
    def queue(self) -> Queue:
        """Get the queue of the input."""
        # Lazy initialization of the queue because initializing it in constructor prevents pickling
        if not hasattr(self, "_queue"):
            self._queue: Queue = Queue()
        return self._queue

    @property
    def is_connected(self) -> bool:
        """Check if the input is connected to a queue."""
        return hasattr(self, "_queue") and self._queue is not None

    @property
    def value(self) -> Any:
        """Get the static value associated with the input."""
        return self._value

    @value.setter
    def value(self, value: Any):
        """Set the static value of the input."""
        # Can be set to EOF to indicate end of data
        if self.type is not None and not is_EOF(value) and not isinstance(value, self.type):  # type: ignore
            raise ValueError(f"Value {value} is not of type {self.type}")
        self._value = value

    def get(self) -> Any:
        """Get the value of the input from either the queue or static value."""
        if not self.is_connected and (
            self.required == Requiredness.OPTIONAL or
            self.required == Requiredness.REQUIRED_IF_CONNECTED):
            return self._value
        if self._input_mode == InputMode.QUEUE:
            return self._queue.get()
        elif self._input_mode == InputMode.STICKY:
            if not self._queue.empty() or self._value is None:
                value = self._queue.get()
                if not is_EOF(value):
                    # Ignore EOFs on sticky inputs, only queue inputs matter for termination
                    self._value = value
        return self._value

    def empty(self) -> bool:
        """Check if the input queue is empty."""
        if self._input_mode == InputMode.QUEUE:
            return self._queue.empty()
        return self._value is None

    def count(self) -> int:
        """Get the number of elements in the input queue."""
        if self._input_mode == InputMode.QUEUE:
            return self._queue.qsize()
        return 0 if self._value is None else 1

    def inc_ref_count(self):
        """Increment the reference count of the input."""
        self._ref_count += 1

    def dec_ref_count(self):
        """Decrement the reference count of the input."""
        self._ref_count -= 1

    @property
    def ref_count(self) -> int:
        """Get the reference count of the input."""
        return self._ref_count


class Output:
    """Output is an interface for setting output data for a component."""

    def __init__(
        self,
        /,
        id: str = "",
        description: str = "",
        mode: OutputMode = OutputMode.REF,
        type: Optional[type] = None,
        delayed: bool = False,
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
        self._output_mode = mode
        self.type = type
        self.delayed = delayed
        self._queues: list[Queue] = []
        self._circle_index = 0

    def connect(self, queue: Queue):
        """Connect a queue to the output.

        This method can be called multiple times to connect multiple queues to the same output.
        """
        self._queues.append(queue)

    @property
    def connected(self) -> bool:
        """Check if the output is connected to a queue."""
        return len(self._queues) > 0

    def send(self, value: Any):
        """Put a value in the output queue."""
        if self.type is not None and not is_EOF(value) and not isinstance(value, self.type):  # type: ignore
            raise ValueError(
                f'Output "{self.id}": value {value} is not of type {self.type}'
            )
        if len(self._queues) == 0:
            raise ValueError(f'Output "{self.id}": has no connected queues')

        if len(self._queues) == 1:
            self._queues[0].put(value)
            return

        if self._output_mode == OutputMode.CIRCLE:
            # Round-robin output queue selection
            self._queues[self._circle_index].put(value)
            self._circle_index = (self._circle_index + 1) % len(self._queues)
            return

        for i, queue in enumerate(self._queues):
            if self._output_mode == OutputMode.REF:
                queue.put(value)
            elif self._output_mode == OutputMode.VALUE:
                if i == 0:
                    # Send the original value to the first queue
                    queue.put(value)
                else:
                    # Send a deep copy of the value to the rest of the queues
                    queue.put(deepcopy(value))


class RedirectQueue:
    """RedriveQueue is a fake write-only queue that is used by GraphPort
    to redrive input values to the output queues."""

    def __init__(self, output: Output):
        self._output = output
        self._ref_count = 0

    @property
    def ref_count(self) -> int:
        return self._ref_count

    def inc_ref_count(self):
        self._ref_count += 1

    def dec_ref_count(self):
        self._ref_count -= 1

    def put(self, item: Any, block=True, timeout=None):
        if item is EOF:
            # Count references and only send EOF when all references are removed as we might have multiple inputs connected
            self.dec_ref_count()
            if self._ref_count <= 0:
                self._output.send(item)
        else:
            self._output.send(item)


class GraphPort(Input, Output):
    """GraphPort is an interface between inside and outside of the graph used for input/output.

    It combines Input and Output, because Graph Input acts as an Input for outside world,
    but outputs values inside the graph. Similarly, Graph Output acts as an Output for outside world,
    but receives values from inside the graph."""

    def __init__(
        self,
        id: str = "",
        description: str = "",
        type: Optional[type] = None,
        value: Any = None,
        required: Requiredness = Requiredness.REQUIRED,
        output_mode: OutputMode = OutputMode.REF,
        delayed: bool = False,
    ):
        input_mode = InputMode.QUEUE
        Input.__init__(
            self,
            id=id,
            description=description,
            type=type,
            mode=input_mode,
            value=value,
            required=required,
        )
        Output.__init__(
            self,
            id=id,
            description=description,
            type=type,
            mode=output_mode,
            delayed=delayed,
        )

        # Use RedriveQueue instead of the normal input queue
        self._queue = RedirectQueue(self)  # type: ignore

    def inc_ref_count(self):
        # Need to increase ref count of the RedriveQueue
        self._queue.inc_ref_count() # type: ignore
        return super().inc_ref_count()

    def dec_ref_count(self):
        self._queue.dec_ref_count() # type: ignore
        return super().dec_ref_count()


class ConnectionNode:
    """ConnectionNode is a combination of a node and an input/output pin.

    It is used as a source or destination of a connection."""

    def __init__(self, ins_id: str, pin_id: str):
        self.ins_id = ins_id
        self.pin_id = pin_id


class Connection:
    """Connection is a connection between two nodes in a graph."""

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

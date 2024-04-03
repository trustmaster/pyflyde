from enum import Enum
from typing import Any, Optional, Union, get_args
from asyncio import Queue as AsyncQueue
from queue import Queue

EOF = Exception('__EOF__')

class InputMode(Enum):
    QUEUE = "queue"
    STICKY = "sticky"
    STATIC = "static"


class Input:
    """Input is an interface for getting input/output data for a component."""

    """Create a new input object.

    Args:
        id (str): The ID of the input
        description (str): The description of the input
        mode (InputMode): The mode of the input
        typ (type): The type of the input
        value (Any): The value of the input for InputMode = InputMode.STATIC or InputMode = InputMode.STICKY
    """
    def __init__(self, /,
        id: str = '',
        description: str = '',
        mode: InputMode = InputMode.QUEUE,
        type: Optional[type] = None,
        value: Any = None
    ):
        self.id = id
        self.description = description
        self.type = type
        self.mode = mode
        if value != None:
            if self.type != None and not isinstance(value, type): # type: ignore
                raise ValueError(f'Value {value} is not of type {self.type}')
            self.value = value

    def connect(self, queue: Queue):
        """Connect the input to a queue."""
        self.queue = queue

    def set_value(self, value: Any):
        """Set the value of the input."""
        if self.type != None and not isinstance(value, self.type): # type: ignore
            raise ValueError(f'Value {value} is not of type {self.type}')
        self.value = value

    def get(self) -> Any:
        """Get the value of the input."""
        if self.mode == InputMode.QUEUE:
            value = self.queue.get()
            if value == EOF:
                raise EOF
            return value

        return self.value

    def empty(self) -> bool:
        """Check if the input queue is empty."""
        if self.mode == InputMode.QUEUE:
            return self.queue.empty()
        return self.value == None

    def count(self) -> int:
        """Get the number of elements in the input queue."""
        if self.mode == InputMode.QUEUE:
            return self.queue.qsize()
        return 1


# class AsyncInput(Input):
#     """AsyncInput is an interface for getting input/output data for a component."""

#     def connect(self, queue: AsyncQueue):
#         """Connect the input to a queue."""
#         self.queue = queue

#     def get(self):
#         """Get the value of the input."""
#         return self.queue.get()


class Output:
    """Output is an interface for setting output data for a component."""

    """Create a new output object.

    Args:
        id (str): The ID of the output
        description (str): The description of the output
        type (type): The type of the output
        delayed (bool): If the output is delayed
    """
    def __init__(self, /,
        id: str = '',
        description: str = '',
        type: Optional[type] = None,
        delayed: bool = False
    ):
        self.id = id
        self.description = description
        self.type = type
        self.delayed = delayed

    def connect(self, queue: Queue):
        """Connect the output to a queue."""
        self.queue = queue

    def send(self, value: Any):
        """Put a value in the output queue."""
        if self.type != None and not isinstance(value, self.type): # type: ignore
            raise ValueError(f'Value {value} is not of type {self.type}')
        self.queue.put(value)

import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from flyde.io import Connection as Connection, EOF as EOF, GraphPort as GraphPort, Input as Input, InputConfig as InputConfig, InputMode as InputMode, InputType as InputType, Output as Output, Requiredness as Requiredness, is_EOF as is_EOF
from threading import Event
from typing import Any, Callable

logger: Incomplete
SUPPORTED_MACROS: Incomplete

class InstanceType(Enum):
    """InstanceType is the type of an instance.

    VISUAL: The instance is a visual node.
    CODE: The instance is a code node.
    """
    VISUAL = 'visual'
    CODE = 'code'

class InstanceSourceType(Enum):
    """InstanceSourceType is the source type of an instance.

    FILE: The instance is created from a file.
    PACKAGE: The instance is created from a built in package."""
    FILE = 'file'
    PACKAGE = 'package'

@dataclass
class InstanceSource:
    """Source configuration of an instance."""
    type: InstanceSourceType
    data: str
    def __init__(self, type, data) -> None: ...

@dataclass
class InstanceArgs:
    """Arguments to pass to the instance factory."""
    id: str
    display_name: str
    stopped: Event | None
    config: dict[str, Any]
    type: InstanceType = ...
    source: InstanceSource | None = ...
    def to_dict(self) -> dict:
        """Convert the instance arguments to a dictionary."""
    def __init__(self, id, display_name, stopped, config, type=..., source=...) -> None: ...
InstanceFactory = Callable[[str, InstanceArgs], Any]

class Node(ABC, metaclass=abc.ABCMeta):
    """Node is the main building block of an application.

    Attributes:
        id (str): A unique identifier for the node.
        node_type (str): The node type identifier.
        config (dict): A dictionary of input pin configurations.
        display_name (str): A human-readable name for the node.
        inputs (dict[str, Input]): Node input map.
        outputs (dict[str, Output]): Node output map.
    """
    inputs: dict[str, Input]
    outputs: dict[str, Output]
    _node_type: Incomplete
    _id: Incomplete
    _display_name: Incomplete
    _config_raw: Incomplete
    _config: Incomplete
    _stopped: Incomplete
    def __init__(self, /, id: str, node_type: str = '', display_name: str = '', inputs: dict[str, Input] = {}, outputs: dict[str, Output] = {}, stopped: Event = ..., config: dict[str, InputConfig] = {}) -> None: ...
    def parse_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Parse the raw config into a typed config dictionary."""
    @abstractmethod
    def run(self):
        """Run the node. This method should be overridden by subclasses."""
    @abstractmethod
    def stop(self):
        """Stop the node. This method should be overridden by subclasses."""
    def finish(self) -> None:
        """Finish the component execution gracefully by closing all its outputs and notifying others."""
    @property
    def stopped(self) -> Event: ...
    def shutdown(self) -> None:
        """Shutdown the component. This method is optional and can be overridden by subclasses."""
    def send(self, output_id: str, value: Any):
        """Send a value to an output."""
    def receive(self, input_id: str) -> Any:
        """Receive a value from an input."""
    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict):
        """Create a node from a parsed YAML dictionary."""
    def to_dict(self) -> dict: ...

class Component(Node):
    """A node that runs a function when executed."""
    _stop: Incomplete
    _mutex: Incomplete
    def __init__(self, **kwargs) -> None: ...
    def run(self) -> None: ...
    def stop(self) -> None:
        """Stop the component execution."""
    @classmethod
    def to_ts(cls, name: str = '') -> str:
        """Convert the node to a TypeScript definition."""

class Graph(Node):
    """A visual graph node that contains other nodes."""
    inputs: Incomplete
    outputs: Incomplete
    _connections: Incomplete
    _instances: Incomplete
    _instances_stopped: Incomplete
    def __init__(self, /, id: str = '', node_type: str = '', config: dict[str, InputConfig] = {}, display_name: str = '', instances: dict[str, Node] = {}, instances_stopped: dict[str, Event] = {}, connections: list[Connection] = [], inputs: dict[str, GraphPort] = {}, outputs: dict[str, GraphPort] = {}, stopped: Event = ...) -> None: ...
    def _check_pin(self, pin_type: str, instance_id: str, pin_id: str):
        """Check if the instance and pin exist."""
    def run(self) -> None:
        """Run the graph."""
    def shutdown(self) -> None:
        """Call shutdown handlers on all instances.

        This method is called from the main thread to allow cleanup and things like UI."""
    def stop(self) -> None:
        """Stop all instances gracefully."""
    def terminate(self) -> None:
        """Terminate all instances immediately."""
    @property
    def stopped(self) -> Event:
        """Return the stopped event which is set when the node has stopped."""
    _stopped: Incomplete
    @stopped.setter
    def stopped(self, value: Event):
        """Set the stopped event."""
    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict):
        """Create a Graph node from a parsed YAML dictionary."""
    def to_dict(self) -> dict:
        """Return a dictionary representation of the node."""

def create_instance_id(node_type: str) -> str:
    """Create a unique instance ID."""

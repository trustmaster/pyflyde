import abc
from _typeshed import Incomplete as Incomplete
from abc import ABC, abstractmethod
from flyde.io import Connection as Connection, GraphPort as GraphPort, Input as Input, InputMode as InputMode, Output as Output
from threading import Event
from typing import Any, Callable

logger: Incomplete
InstanceFactory = Callable[[str, dict], Any]

class Node(ABC, metaclass=abc.ABCMeta):
    inputs: dict[str, Input]
    outputs: dict[str, Output]
    def __init__(self, /, id: str, node_type: str = '', input_config: dict[str, InputMode] = {}, display_name: str = '', inputs: dict[str, Input] = {}, outputs: dict[str, Output] = {}, stopped: Event = ...) -> None: ...
    @abstractmethod
    def run(self): ...
    @abstractmethod
    def stop(self): ...
    def finish(self) -> None: ...
    @property
    def stopped(self) -> Event: ...
    def shutdown(self) -> None: ...
    def send(self, output_id: str, value: Any): ...
    def receive(self, input_id: str) -> Any: ...
    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict): ...
    def to_dict(self) -> dict: ...

class Component(Node):
    def __init__(self, **kwargs) -> None: ...
    def run(self) -> None: ...
    def stop(self) -> None: ...
    @classmethod
    def to_ts(cls, name: str = '') -> str: ...

class Graph(Node):
    inputs: Incomplete
    outputs: Incomplete
    def __init__(self, /, id: str = '', node_type: str = '', input_config: dict[str, InputMode] = {}, display_name: str = '', instances: dict[str, Node] = {}, instances_stopped: dict[str, Event] = {}, connections: list[Connection] = [], inputs: dict[str, GraphPort] = {}, outputs: dict[str, GraphPort] = {}, stopped: Event = ...) -> None: ...
    def run(self) -> None: ...
    def shutdown(self) -> None: ...
    def stop(self) -> None: ...
    def terminate(self) -> None: ...
    @property
    def stopped(self) -> Event: ...
    @stopped.setter
    def stopped(self, value: Event): ...
    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict): ...
    def to_dict(self) -> dict: ...

def create_instance_id(node_type: str) -> str: ...

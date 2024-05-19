from _typeshed import Incomplete
from flyde.node import Graph as Graph
from threading import Event

logger: Incomplete

class Flow:
    """Flow is a root-level runnable directed acyclic graph of nodes."""
    _imports: Incomplete
    _path: str
    _node: Incomplete
    _components: Incomplete
    _graphs: Incomplete
    def __init__(self, imports: dict[str, list[str]]) -> None: ...
    def _preload_imports(self, base_path: str, imports: dict[str, list[str]]): ...
    def factory(self, class_name: str, args: dict):
        """Factory method to create a node from a class name and arguments.

        It is used by the runtime to create nodes from the YAML definition or on the fly."""
    def run(self) -> None:
        """Start the flow running. This is a non-blocking call as the flow runs in a separate thread."""
    def run_sync(self) -> None:
        """Run the flow synchronously. Shutdown handlers will be executed after the flow has finished."""
    @property
    def node(self) -> Graph:
        """The root node of the flow."""
    @property
    def stopped(self) -> Event:
        """Stopped event is set when the flow has finished working."""
    @classmethod
    def from_yaml(cls, path: str, yml: dict):
        """Load Flyde Flow definition from parsed YAML dict."""
    @classmethod
    def from_file(cls, path: str):
        """Load Flyde Flow definition from a *.flyde YAML file."""
    def to_dict(self) -> dict: ...

def add_folder_to_path(path: str): ...
def load_yaml_file(yaml_file: str) -> dict: ...

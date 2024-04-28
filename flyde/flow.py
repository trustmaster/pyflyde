import importlib
import logging
import os
import sys
import yaml  # type: ignore
from threading import Event

from flyde.node import Graph

logger = logging.getLogger(__name__)


class Flow:
    """Flow is a root-level runnable directed acyclic graph of nodes."""
    def __init__(self, imports: dict[str, list[str]], node: Graph = Graph()):
        self._imports = imports
        self._node = node

    def factory(self, class_name: str, args: dict):
        """Factory method to create a node from a class name and arguments.

        It is used by the runtime to create nodes from the YAML definition or on the fly."""
        if class_name == "VisualNode":
            return Graph(**args)

        # Look up the class in the imports
        for module, classes in self._imports.items():
            if class_name in classes:
                # Translate typescript file path to python module
                module = (
                    module.replace("/", ".").replace(".flyde.ts", "").replace("@", "")
                )
                logger.debug(f"Importing {module} for class {class_name}")
                mod = importlib.import_module(module)
                return getattr(mod, class_name)(**args)

        raise ValueError(f"Unknown class name: {class_name}")

    def run(self):
        """Start the flow running. This is a non-blocking call as the flow runs in a separate thread."""
        self._node.run()

    def run_sync(self):
        """Run the flow synchronously. Shutdown handlers will be executed after the flow has finished."""
        self._node.run()
        self._node.stopped.wait()
        self._node.shutdown()

    @property
    def node(self) -> Graph:
        """The root node of the flow."""
        return self._node

    @property
    def stopped(self) -> Event:
        """Stopped event is set when the flow has finished working."""
        return self._node.stopped

    @classmethod
    def from_yaml(cls, yml: dict):
        """Load Flyde Flow definition from parsed YAML dict."""
        imports = yml.get("imports", {})

        if "node" not in yml:
            raise ValueError("No node in flow definition")

        ins = cls(imports)
        ins._node = Graph.from_yaml(ins.factory, yml["node"])
        ins._node.stopped = Event()
        return ins

    @classmethod
    def from_file(cls, path: str):
        """Load Flyde Flow definition from a *.flyde YAML file."""
        yml = load_yaml_file(path)
        if not isinstance(yml, dict):
            raise ValueError("Invalid YAML file")

        # Get the absolute path from the yaml_file path and add it to the sys.path for discoverability
        add_folder_to_path(path)

        return cls.from_yaml(yml)

    def to_dict(self) -> dict:
        return {"imports": self._imports, "node": self._node.to_dict()}


def add_folder_to_path(path: str):
    # Get the absolute path from the relative file path provided
    folder = os.path.abspath(os.path.dirname(path))
    if folder not in sys.path:
        sys.path.append(folder)


def load_yaml_file(yaml_file: str) -> dict:
    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)
    return data

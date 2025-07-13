import importlib
import importlib.util
import logging
import os
import sys
from threading import Event
from typing import Callable

import yaml  # type: ignore

from flyde.node import Graph, InstanceArgs, InstanceType

logger = logging.getLogger(__name__)


class Flow:
    """Flow is a root-level runnable directed acyclic graph of nodes."""

    def __init__(self, imports: dict[str, list[str]]):
        self._imports = imports
        self._path = ""
        self._base_path = ""
        self._node: Graph
        self._components: dict[str, Callable] = {}
        self._graphs: dict[str, dict] = {}

    def _preload_imports(self, base_path: str, imports: dict[str, list[str]]):
        if not imports:
            return

        for module, classes in imports.items():
            logger.debug(f"Importing {module}")
            # If module name ends with .flyde it's a Graph
            if module.endswith(".flyde"):
                node_id = classes[0]
                logger.debug(f"Importing graph {node_id} from {base_path}/{module}")
                yml = load_yaml_file(f"{base_path}/{module}")
                if not isinstance(yml, dict):
                    raise ValueError(f"Invalid YAML file {module}")
                # Merge the imports from the graph with the current imports recursively
                self._preload_imports(base_path, yml.get("imports", {}))
                # Save the blueprint YAML for the graph to be instantiated later
                self._graphs[node_id] = yml["node"]
                continue
            # Convert module path format
            module = module.replace("/", ".").replace("@", "")
            logger.debug(f"Importing module {module}")
            mod = importlib.import_module(module)
            for class_name in classes:
                logger.debug(f"Importing {class_name} from {module}")
                self._components[class_name] = getattr(mod, class_name)

    def _load_graph(self, name: str, path: str):
        """Loads a graph YAML."""
        full_path = os.path.join(self._base_path, path)
        yml = load_yaml_file(full_path)
        if not isinstance(yml, dict):
            raise ValueError(f"Invalid YAML file {path}")
        # Save the blueprint YAML for the graph to be instantiated later
        self._graphs[name] = yml["node"]
        return

    def _load_component(self, name: str, path: str):
        """Loads a component from a Python module."""
        # If component is already loaded, return
        if name in self._components:
            return

        # Handle custom://path/to/mod.py/ClassName format
        if path.startswith("custom://"):
            custom_path = path[9:]  # Remove "custom://" prefix
            if "/" in custom_path and custom_path.count("/") >= 1:
                # Split into module path and class name
                parts = custom_path.rsplit("/", 1)
                if len(parts) == 2:
                    module_path, class_name = parts

                    # Resolve the module path relative to the flow file's directory
                    if module_path.endswith(".py"):
                        # It's a file path, resolve it relative to the flow file directory
                        absolute_module_path = os.path.join(self._base_path, module_path)
                        # Convert to module name for importing
                        spec = importlib.util.spec_from_file_location(class_name, absolute_module_path)
                        if spec and spec.loader:
                            mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            self._components[name] = getattr(mod, class_name)
                            return
                    else:
                        # It's already a module path, convert file path to module path
                        module_path = module_path.replace("/", ".").replace(".py", "")

                        # Add the flow file's directory to sys.path temporarily for relative imports
                        original_path = sys.path[:]
                        if self._base_path not in sys.path:
                            sys.path.insert(0, self._base_path)

                        try:
                            logger.debug(f"Importing custom module {module_path}, class {class_name}")
                            mod = importlib.import_module(module_path)
                            self._components[name] = getattr(mod, class_name)
                            return
                        finally:
                            # Restore original sys.path
                            sys.path[:] = original_path

        # Handle @flyde/nodes package format for stdlib components
        if path == "@flyde/nodes":
            logger.debug(f"Loading stdlib component {name}")
            from flyde.nodes import Conditional, GetAttribute, Http, InlineValue

            stdlib_components = {
                "InlineValue": InlineValue,
                "Conditional": Conditional,
                "GetAttribute": GetAttribute,
                "Http": Http,
            }
            if name in stdlib_components:
                self._components[name] = stdlib_components[name]
                return

        raise ValueError(
            f"Invalid component source path: {path}. Only custom:// and @flyde/nodes formats are supported."
        )

    def create_graph(self, name: str, args: InstanceArgs):
        if name not in self._graphs:
            if args.source is None:
                raise ValueError(f"Graph {name} does not have a valid source")
            self._load_graph(name, args.source.data)

        # Merge the blueprint YAML with the arguments
        yml = self._graphs[name] | args.to_dict()
        node = Graph.from_yaml(self.factory, yml)
        return node

    def create_component(self, name: str, args: InstanceArgs):
        if name not in self._components:
            if args.source is None:
                raise ValueError(f"Component {name} does not have a valid source")
            self._load_component(name, args.source.data)

        if name not in self._components:
            raise ValueError(f"Component {name} could not be loaded")

        # Create the component instance
        component = self._components[name]
        return component(**args.to_dict())

    def factory(self, class_name: str, args: InstanceArgs):
        """Factory method to create a node from a class name and arguments.

        It is used by the runtime to create nodes from the YAML definition or on the fly.
        """
        if args.type == InstanceType.VISUAL:
            return self.create_graph(class_name, args)

        return self.create_component(class_name, args)

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
    def from_yaml(cls, path: str, yml: dict):
        """Load Flyde Flow definition from parsed YAML dict."""
        imports = yml.get("imports", {})

        if "node" not in yml:
            raise ValueError("No node in flow definition")

        ins = cls(imports)
        ins._path = path
        ins._base_path = os.path.dirname(path)
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

        return cls.from_yaml(path, yml)

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

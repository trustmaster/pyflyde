import importlib
import logging
import os
import sys
import yaml  # type: ignore
from threading import Event

from flyde.node import Graph

logger = logging.getLogger(__name__)


class FlydeFlow:
    def __init__(self, imports: dict[str, list[str]], node: Graph = Graph()):
        self._imports = imports
        self._node = node

    def factory(self, class_name: str, args: dict):
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
        """Start the flow running."""
        self._node.run()

    @property
    def stopped(self) -> Event:
        """ "Stopped event is set when the flow has finished working."""
        return self._node.stopped

    @classmethod
    def from_yaml(cls, yml: dict):
        """Load Flyde Flow definition from parsed YAML"""
        imports = yml.get("imports", dict())

        if "node" not in yml:
            raise ValueError("No node in flow definition")

        ins = cls(imports)
        ins._node = Graph.from_yaml(ins.factory, yml["node"])
        ins._node.stopped = Event()
        return ins

    @classmethod
    def from_file(cls, path: str):
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

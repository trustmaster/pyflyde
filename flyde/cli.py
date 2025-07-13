#!/usr/bin/env python3
import argparse
import glob
import importlib
import importlib.util
import json
import logging
import os
import pprint
import sys

from flyde.flow import Flow, add_folder_to_path
from flyde.node import SUPPORTED_MACROS, Component

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


def py_path_to_module(py_path: str) -> str:
    return py_path.replace("/", ".").replace(".py", "")


def convert_class_name_to_display_name(class_name: str) -> str:
    """Convert a class name like 'MyCustomNode' to 'My Custom Node'."""
    # Insert space before uppercase letters that follow lowercase letters
    import re

    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", class_name)


def is_stdlib_node(node_name: str) -> bool:
    """Check if a node name matches a stdlib node."""
    return node_name in SUPPORTED_MACROS


def collect_components_from_directory(directory_path: str) -> dict:
    """Collect all Component subclasses from .py files in a directory and its subdirectories."""
    components = {}

    # Convert directory path to absolute path
    abs_dir = os.path.abspath(directory_path)

    # Add the directory to Python path for imports
    if abs_dir not in sys.path:
        sys.path.insert(0, abs_dir)

    # Find all .py files in the directory and subdirectories recursively
    py_files = glob.glob(os.path.join(directory_path, "**", "*.py"), recursive=True)

    for py_file in py_files:
        # Skip __init__.py files
        if os.path.basename(py_file) == "__init__.py":
            continue

        try:
            # Get relative path from the directory
            relative_path = os.path.relpath(py_file, directory_path)

            # Convert file path to module name (handle subdirectories)
            module_path = relative_path.replace(os.path.sep, ".").replace(".py", "")

            # Import the module
            spec = importlib.util.spec_from_file_location(module_path, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find all Component subclasses
                for name in dir(module):
                    obj = getattr(module, name)
                    if (
                        name != "Component"
                        and isinstance(obj, type)
                        and issubclass(obj, Component)
                        and obj.__module__ == module_path
                    ):
                        components[name] = {"class": obj, "file_path": relative_path}

        except Exception as e:
            logger.warning(f"Failed to import module from {py_file}: {e}")

    return components


def generate_node_json(node_name: str, component_class, file_path: str = "") -> dict:
    """Generate JSON structure for a single component."""
    # Get description from docstring
    description = (component_class.__doc__ or "").strip()

    # Generate display name
    display_name = convert_class_name_to_display_name(node_name)

    # Determine source
    if is_stdlib_node(node_name):
        source = {"type": "package", "data": "@flyde/nodes"}
        display_name = f"Overridden {display_name}"
        description = f"This overrides the standard {node_name} node"
    else:
        source = {"type": "custom", "data": f"custom://{file_path}/{node_name}"}

    # Build inputs structure
    inputs = {}
    if hasattr(component_class, "inputs") and component_class.inputs:
        for input_name, input_obj in component_class.inputs.items():
            inputs[input_name] = {"description": input_obj.description or f"{input_name} input"}

    # Build outputs structure
    outputs = {}
    if hasattr(component_class, "outputs") and component_class.outputs:
        for output_name, output_obj in component_class.outputs.items():
            outputs[output_name] = {"description": output_obj.description or f"{output_name} output"}

    # Build the node structure
    node_data = {
        "id": node_name,
        "type": "code",
        "displayName": display_name,
        "description": description,
        "source": source,
        "editorNode": {
            "id": node_name,
            "displayName": display_name,
            "description": description,
            "inputs": inputs,
            "outputs": outputs,
            "editorConfig": {"type": "structured"},
        },
        "config": {},
    }

    # Add icon for custom nodes
    if not is_stdlib_node(node_name):
        node_data["icon"] = "fa-solid fa-user"
        node_data["editorNode"]["icon"] = "fa-solid fa-user"

    return node_data


def gen_json(directory_path: str):
    """Generate JSON file for all components in a directory."""
    print(f"Generating JSON file for components in directory {directory_path}")

    # Collect all components
    components = collect_components_from_directory(directory_path)

    if not components:
        print(f"No Component subclasses found in directory {directory_path}")
        return

    # Build nodes structure
    nodes = {}
    custom_nodes = []
    stdlib_nodes = []

    for node_name, component_info in components.items():
        component_class = component_info["class"]
        file_path = component_info["file_path"]
        nodes[node_name] = generate_node_json(node_name, component_class, file_path)

        if is_stdlib_node(node_name):
            stdlib_nodes.append(node_name)
        else:
            custom_nodes.append(node_name)

    # Build groups
    groups = []
    if custom_nodes:
        groups.append({"title": "Custom Runtime Nodes", "nodeIds": custom_nodes})
    if stdlib_nodes:
        groups.append({"title": "Overridden Stdlib", "nodeIds": stdlib_nodes})

    # Build final JSON structure
    json_data = {"nodes": nodes, "groups": groups}

    # Write to file
    output_file = os.path.join(directory_path, ".flyde-nodes.json")
    with open(output_file, "w") as f:
        json.dump(json_data, f, indent=2)

    print(f"Generated {output_file} with {len(components)} components")
    print(f"Custom nodes: {custom_nodes}")
    print(f"Stdlib overrides: {stdlib_nodes}")


def main():
    parser = argparse.ArgumentParser(
        description="""PyFlyde CLI that runs Flyde graphs and provides other useful functions.

Examples:
    flyde.py path/to/MyFlow.flyde # Runs a flow
    flyde.py gen path/to/directory/ # Generates .flyde-nodes.json for directory
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        type=str,
        nargs="?",
        choices=["run", "gen"],
        default="run",
        help='Command to run. Default is "run"',
    )
    parser.add_argument(
        "path",
        type=str,
        help='Path to a ".flyde" flow file to run, or a directory to generate .flyde-nodes.json for',
    )

    args = parser.parse_args()

    if args.command == "run":
        # Get the yaml file path from the command line argument
        yaml_file = args.path

        flow = Flow.from_file(yaml_file)

        if logging.getLevelName(logging.root.level) == "DEBUG":
            print("Loaded flow:")
            pprint.pprint(flow.to_dict())

        flow.run_sync()
    elif args.command == "gen":
        add_folder_to_path(args.path)
        # Add current folder to path when resolving modules relative to the current folder
        add_folder_to_path(".")

        # Generate JSON for directory
        if os.path.isdir(args.path):
            gen_json(args.path)
        else:
            raise ValueError(f"Path {args.path} is not a directory. Only directory generation is supported.")
    else:
        raise ValueError(f"Unknown command: {args.command}")

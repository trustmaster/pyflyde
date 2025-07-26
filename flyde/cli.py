#!/usr/bin/env python3
import argparse
import glob
import importlib
import importlib.util
import json
import logging
import os
import pprint
import re
import sys

import yaml

from flyde.flow import Flow, add_folder_to_path
from flyde.node import SUPPORTED_MACROS, Component

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


def py_path_to_module(py_path: str) -> str:
    return py_path.replace("/", ".").replace(".py", "")


def convert_class_name_to_display_name(class_name: str) -> str:
    """Convert a class name like 'MyCustomNode' to 'My Custom Node'."""

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
                        components[name] = {"class": obj, "file_path": relative_path, "type": "python"}

        except Exception as e:
            logger.warning(f"Failed to import module from {py_file}: {e}")

    return components


def collect_flyde_nodes_from_directory(directory_path: str) -> dict:
    """Collect all .flyde files from a directory and its subdirectories."""
    flyde_nodes = {}

    # Find all .flyde files in the directory and subdirectories recursively
    flyde_files = glob.glob(os.path.join(directory_path, "**", "*.flyde"), recursive=True)

    for flyde_file in flyde_files:
        try:
            # Get relative path from the directory
            relative_path = os.path.relpath(flyde_file, directory_path)

            # Load the YAML content
            with open(flyde_file, "r") as f:
                flyde_data = yaml.safe_load(f)

            # Extract node information
            node_data = flyde_data.get("node", {})
            node_id = os.path.splitext(os.path.basename(flyde_file))[0]
            description = node_data.get("description", flyde_data.get("description", ""))

            # Extract inputs and outputs
            inputs = node_data.get("inputs", {})
            outputs = node_data.get("outputs", {})

            flyde_nodes[node_id] = {
                "file_path": relative_path,
                "description": description,
                "inputs": inputs,
                "outputs": outputs,
                "type": "flyde",
            }

        except Exception as e:
            logger.warning(f"Failed to parse .flyde file {flyde_file}: {e}")

    return flyde_nodes


def generate_flyde_node_json(node_name: str, flyde_info: dict) -> dict:
    """Generate JSON structure for a .flyde file node."""
    file_path = flyde_info["file_path"]
    description = flyde_info["description"]
    inputs = flyde_info["inputs"]
    outputs = flyde_info["outputs"]

    display_name = convert_class_name_to_display_name(node_name)

    # Build inputs structure
    editor_inputs = {}
    for input_name, input_data in inputs.items():
        mode = input_data.get("mode", "required")
        input_description = f"{input_name} input"
        if mode == "required":
            input_description += " (required)"
        editor_inputs[input_name] = {"description": input_description}

    # Build outputs structure
    editor_outputs = {}
    for output_name, output_data in outputs.items():
        output_description = f"{output_name} output"
        editor_outputs[output_name] = {"description": output_description}

    # Build the node structure
    node_data = {
        "id": node_name,
        "type": "visual",
        "displayName": display_name,
        "description": description,
        "icon": "fa-diagram-project",
        "source": {"type": "file", "data": file_path},
        "editorNode": {
            "id": node_name,
            "displayName": display_name,
            "description": description,
            "inputs": editor_inputs,
            "outputs": editor_outputs,
            "editorConfig": {"type": "structured"},
        },
        "config": {},
    }

    return node_data


def generate_node_json(node_name: str, component_class, file_path: str = "") -> dict[str, object] | str:
    """Generate JSON structure for a single component."""
    # Get node metadata
    description = (component_class.__doc__ or "").strip()
    display_name = convert_class_name_to_display_name(node_name)
    # Use package source for stdlib nodes, custom source for others
    if is_stdlib_node(node_name):
        return "@flyde/nodes"
    else:
        source = {"type": "custom", "data": f"custom://{file_path}/{node_name}"}
    icon = getattr(component_class, "icon", "fa-brands fa-python")

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
        "icon": icon,
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

    return node_data


def gen_json(directory_path: str):
    """Generate JSON file for all components in a directory."""
    print(f"Generating JSON file for components in directory {directory_path}")

    # Collect all components
    components = collect_components_from_directory(directory_path)

    # Collect all .flyde nodes
    flyde_nodes = collect_flyde_nodes_from_directory(directory_path)

    # Always include stdlib nodes from flyde/nodes.py
    stdlib_dir = os.path.join(os.path.dirname(__file__), "nodes.py")
    stdlib_components = collect_components_from_directory(os.path.dirname(stdlib_dir))
    stdlib_node_names = [name for name in stdlib_components if is_stdlib_node(name)]

    if not components and not flyde_nodes and not stdlib_node_names:
        print(f"No Component subclasses or .flyde files found in directory {directory_path} or stdlib")
        return

    # Build nodes structure
    nodes = {}
    custom_nodes = []
    stdlib_nodes = []

    # Add user components
    for node_name, component_info in components.items():
        component_class = component_info["class"]
        file_path = component_info["file_path"]
        nodes[node_name] = generate_node_json(node_name, component_class, file_path)
        custom_nodes.append(node_name)

    # Add .flyde nodes
    for node_name, flyde_info in flyde_nodes.items():
        nodes[node_name] = generate_flyde_node_json(node_name, flyde_info)
        custom_nodes.append(node_name)

    # Add stdlib nodes (from flyde/nodes.py) as custom nodes, but group as stdlib overrides
    for node_name in stdlib_node_names:
        if node_name not in nodes:
            component_class = stdlib_components[node_name]["class"]
            file_path = stdlib_components[node_name]["file_path"]
            nodes[node_name] = generate_node_json(node_name, component_class, file_path)
        stdlib_nodes.append(node_name)

    # Build groups
    groups = []
    if custom_nodes:
        groups.append({"title": "Your PyFlyde Nodes", "nodeIds": custom_nodes})
    if stdlib_nodes:
        groups.append({"title": "PyFlyde Standard Nodes", "nodeIds": stdlib_nodes})

    # Build final JSON structure
    json_data = {"nodes": nodes, "groups": groups}

    # Write to file
    output_file = os.path.join(directory_path, "flyde-nodes.json")
    with open(output_file, "w") as f:
        json.dump(json_data, f, indent=2)

    print(f"Generated {output_file} with {len(nodes)} components")
    print(f"Custom nodes: {custom_nodes}")
    print(f"Stdlib nodes: {stdlib_nodes}")


def main():
    parser = argparse.ArgumentParser(
        description="""PyFlyde CLI that runs Flyde graphs and provides other useful functions.

Examples:
    flyde.py path/to/MyFlow.flyde # Runs a flow
    flyde.py gen path/to/directory/ # Generates flyde-nodes.json for directory
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
        help='Path to a ".flyde" flow file to run, or a directory to generate flyde-nodes.json for',
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

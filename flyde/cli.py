#!/usr/bin/env python3
import argparse
import importlib
import logging
import pprint

from flyde.flow import Flow, add_folder_to_path
from flyde.node import Component

logging.basicConfig(level=logging.INFO)


def py_path_to_module(py_path: str) -> str:
    return py_path.replace("/", ".").replace(".py", "")


def gen(path: str):
    """Generate TypeScript files for a module."""
    print(f"Generating TypeScript files for module {path}")
    module = py_path_to_module(path)
    mod = importlib.import_module(module)
    ts_file_path = path.replace(".py", ".flyde.ts")
    typescript = 'import { CodeNode } from "@flyde/core";\n\n'
    for name in mod.__dict__.keys():
        c = getattr(mod, name)
        if name != "Component" and isinstance(c, type) and issubclass(c, Component):
            typescript += c.to_ts(name)

    print(f"Writing TypeScript to {ts_file_path}")
    with open(ts_file_path, "w") as f:
        f.write(typescript)


def main():
    parser = argparse.ArgumentParser(
        description="""PyFlyde CLI that runs Flyde graphs and provides other useful functions.

Examples:
    flyde.py path/to/MyFlow.flyde # Runs a flow
    flyde.py gen path/to/module.py # Generates TS files for visual editor
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
        help='Path to a ".flyde" flow file to run or a Python ".py" module to generate typescript definitions for',
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
        gen(args.path)
    else:
        raise ValueError(f"Unknown command: {args.command}")

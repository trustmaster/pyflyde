#!/usr/bin/env python3
import argparse
import importlib
import logging
import pprint
import sys
import yaml

from flyde.flow import FlydeFlow
from flyde.node import Component

logging.basicConfig(level=logging.INFO)

def load_yaml_file(yaml_file: str) -> dict:
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    return data


def gen(module: str):
    """Generate TypeScript files for a module."""
    print(f'Generating TypeScript files for module {module}')
    mod = importlib.import_module(module)
    ts_file_path = f'{module.replace(".", "/")}.flyde.ts'
    typescript = 'import { CodeNode } from "@flyde/core";\n\n'
    for name in mod.__dict__.keys():
        c = getattr(mod, name)
        if name != 'Component' and isinstance(c, type) and issubclass(c, Component):
            typescript += c.to_ts(name)

    print(f'Writing TypeScript to {ts_file_path}')
    with open(ts_file_path, 'w') as f:
        f.write(typescript)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="PyFlyde CLI that runs Flyde graphs and provides other useful functions.\n\nExamples:\n\n  flyde.py path/to/MyFlow.flyde # Runs a flow\n  flyde.py gen my.module # Generates TS files for visual editor",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('command', type=str, nargs='?', choices=['run', 'gen'], default='run', help='Command to run. Default is "run"')
    parser.add_argument('graph_or_module', type=str, help='Path to a ".flyde" flow file to run or a Python module to generate typescript definitions for')

    args = parser.parse_args()

    if args.command == 'run':
        # Get the yaml file path from the command line argument
        yaml_file = args.graph_or_module

        # Load the yaml file
        yml = load_yaml_file(yaml_file)

        if isinstance(yml, dict):
            flow = FlydeFlow.from_yaml(yml)

            if logging.getLevelName(logging.root.level) == 'DEBUG':
                print('Loaded flow:')
                pprint.pprint(flow.to_dict())

            flow.run()
            flow.stopped.wait()
        else:
            raise ValueError('Invalid YAML file')
    elif args.command == 'gen':
        gen(args.graph_or_module)
    else:
        raise ValueError(f'Unknown command: {args.command}')

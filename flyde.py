#!/usr/bin/env python3
import logging
import pprint
import sys
import yaml

from flyde.flow import FlydeFlow

logging.basicConfig(level=logging.INFO)

def load_yaml_file(yaml_file: str) -> dict:
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    return data

# Get the yaml file path from the command line argument
yaml_file = sys.argv[1]

# Load the yaml file
yml = load_yaml_file(yaml_file)

if isinstance(yml, dict):
    flow = FlydeFlow.from_yaml(yml)

    if logging.getLevelName(logging.root.level) == 'DEBUG':
        print('Loaded flow:')
        pprint.pprint(flow.to_dict())

    flow.node.run()
    flow.node.stopped.wait()
else:
    raise ValueError('Invalid YAML file')

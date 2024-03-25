from dataclasses import dataclass
from typing import Any, Callable
from uuid import uuid4

from flyde.connection import Connection
from flyde.pins import InputPin, OutputPin, InputPinMode


@dataclass
class Metadata:
    """Contains meta information about a node type."""
    name: str
    display_name: str
    description: str
    search_keywords: list[str]
    namespace: str


# InstanceFactory is a function that creates a new instance of a node.
# It can create instances dynamically based on the node ID.
InstanceFactory = Callable[[str, dict], Any]


class Node:
    """An abstract node in a flow."""
    meta: Metadata
    inputs: dict[str, InputPin]
    outputs: dict[str, OutputPin]

    def __init__(self, *,
        id: str,
        input_config: dict[str, InputPinMode] = {},
        display_name: str = ''
    ):
        self.id = id
        self.input_config = input_config
        self.display_name = display_name

    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict):
        # TODO: make it a factory method that can create any node type
        node_class_name = yml.get('nodeId', 'VisualNode')
        if node_class_name == 'VisualNode':
            return VisualNode.from_yaml(create, yml)
        args = {
            'id': yml['id'],
            'input_config': yml.get('inputConfig', {}),
            'display_name': yml.get('displayName', '')
        }
        return create(node_class_name, args)


    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nodeId': self.meta.name,
            'inputConfig': self.input_config
        }


RunNodeFunction = Callable[[Node, dict[str, Any], dict[str, Any]], None]


class CodeNode(Node):
    """A node that runs a function when executed."""
    run: RunNodeFunction


class VisualNode(Node):
    """A visual graph node that contains other nodes."""

    def __init__(self, *,
        id: str = '',
        node_id: str = '',
        input_config: dict[str, InputPinMode] = {},
        display_name: str = '',
        instances: list[Node] = [],
        connections: list[Connection] = [],
        inputs: dict[str, InputPin] = {},
        outputs: dict[str, OutputPin] = {}
    ):
        node_id = node_id if node_id else __name__
        id = id if id else create_instance_id(node_id)
        super().__init__(
            id=id,
            input_config=input_config,
            display_name=display_name
        )
        self.node_id = node_id
        self.connections = connections
        self.instances = instances
        self.inputs = inputs
        self.outputs = outputs

    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict):
        node_id = yml.get('nodeId', __name__)
        id = yml['id'] if 'id' in yml else create_instance_id(node_id)
        input_config = yml.get('inputConfig', {})
        display_name = yml.get('displayName', node_id)
        instances = [Node.from_yaml(create, ins) for ins in yml.get('instances', [])]
        connections = [Connection.from_yaml(conn) for conn in yml.get('connections', [])]
        inputs = yml.get('inputs', {})
        outputs = yml.get('outputs', {})
        return cls(
            id=id,
            node_id=node_id,
            input_config=input_config,
            display_name=display_name,
            instances=instances,
            connections=connections,
            inputs=inputs,
            outputs=outputs
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nodeId': self.node_id,
            'inputConfig': self.input_config,
            'displayName': self.display_name,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'instances': [ins.to_dict() for ins in self.instances],
            'connections': [conn.to_dict() for conn in self.connections]
        }


def create_instance_id(node_id: str) -> str:
    return f"{node_id}-{uuid4()}"

import logging
from copy import deepcopy
from dataclasses import dataclass
from queue import Queue
from threading import Event, Lock, Thread
from typing import Any, Callable
from uuid import uuid4

from flyde.connection import Connection
from flyde.io import InputMode, Input, Output, EOF
logger = logging.getLogger(__name__)


# InstanceFactory is a function that creates a new instance of a node.
# It can create instances dynamically based on the node ID.
InstanceFactory = Callable[[str, dict], Any]


class Node:
    """Node is the main building block of an application.
    
    Attributes:
        id (str): A unique identifier for the node.
        node_type (str): The node type identifier.
        input_config (dict): A dictionary of input pin configurations.
        display_name (str): A human-readable name for the node.
        inputs (dict[str, Input]): Node input map.
        outputs (dict[str, Output]): Node output map.
    """

    def __init__(self, /,
        id: str,
        node_type: str = '',
        input_config: dict[str, InputMode] = {},
        display_name: str = '',
        inputs: dict[str, Input] = {},
        outputs: dict[str, Output] = {},
        stopped: Event = Event()
    ):
        node_type = node_type if node_type else self.__class__.__name__
        self.node_type = node_type
        self.id = id if id else create_instance_id(node_type)
        self.input_config = input_config
        self.display_name = display_name if display_name else node_type

        if len(inputs) > 0:
            self.inputs = inputs
        elif hasattr(self.__class__, 'inputs') and len(self.inputs) > 0:
            # Copy from class definition, but instance will have own connections
            self.inputs = deepcopy(self.inputs)
        else:
            self.inputs = {}
        
        if len(outputs) > 0:
            self.outputs = outputs
        elif hasattr(self.__class__, 'outputs') and len(self.outputs) > 0:
            # Copy from class definition, but instance will have own connections
            self.outputs = deepcopy(self.outputs)
        else:
            self.outputs = {}

        self._stopped = stopped

    def finish(self):
        """Finish the component execution gracefully by closing all its outputs and notifying others."""
        for output in self.outputs.values():
                output.queue.put(EOF)
        self._stopped.set()

    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict):
        node_class_name = yml.get('nodeId', 'VisualNode')
        if node_class_name == 'VisualNode':
            return Graph.from_yaml(create, yml)
        args = {
            'id': yml['id'],
            'input_config': yml.get('inputConfig', {}),
            'display_name': yml.get('displayName', ''),
            'stopped': yml['stopped'],
        }
        # If yml['macroData']['value'] is set, pass it in the args as value
        if 'macroData' in yml and 'value' in yml['macroData']:
            args['value'] = yml['macroData']['value']
        return create(node_class_name, args)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nodeId': self.node_type,
            'inputConfig': self.input_config
        }


RunFunction = Callable[[Any, dict[str, str], dict[str, str]], None]


class Component(Node):
    """A node that runs a function when executed."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stop = Event()
        self._mutex = Lock()

    """Run the main component function.
    
    Defaut implementation looks for a reactive method called `process()` and calls it passing the input values.
    """
    def run(self):
        if not hasattr(self, 'process'):
            raise NotImplementedError('Component does not have neither run() nor process() method. No code to run.')

        def worker():
            logger.debug(f'Running {self.id} worker')
            while not self._stop.is_set():
                logger.debug(f'Waiting for inputs on {self.id}')
                inputs = {k: v.queue.get() for k, v in self.inputs.items()}
                # If all of the input values are EOF, stop the component
                if len(inputs) > 0 and all(v == EOF for v in inputs.values()):
                    logger.debug(f'All inputs are EOF, stopping {self.id}')
                    self.stop()
                    break
                logger.debug(f'Processing {self.id} with inputs: {inputs}')
                res = self.process(**inputs)
                if type(res) == dict or (isinstance(res, tuple) and hasattr(res, '_fields')):
                    # Send values to the outputs named as keys
                    for k, v in res.items():
                        if k not in self.outputs:
                            raise ValueError(f'{self.node_type}.process(): sending to non-existing output "{k}" from return value')
                        self.outputs[k].send(v)
            self.finish()
        
        logger.debug(f'Starting {self.id} thread')
        thread = Thread(target=worker, daemon=True)
        thread.start()

    def stop(self):
        """Stop the component execution."""
        logger.debug(f'Stopping {self.id}')
        self._stop.set()
        

class Graph(Node):
    """A visual graph node that contains other nodes."""

    def __init__(self, /,
        id: str = '',
        node_type: str = '',
        input_config: dict[str, InputMode] = {},
        display_name: str = '',
        instances: dict[str, Node] = {},
        instances_stopped: dict[str, Event] = {},
        connections: list[Connection] = [],
        inputs: dict[str, Input] = {},
        outputs: dict[str, Output] = {},
        stopped: Event = Event()
    ):
        super().__init__(
            id=id,
            node_type=node_type,
            input_config=input_config,
            display_name=display_name,
            inputs=inputs,
            outputs=outputs,
            stopped=stopped
        )

        self.connections = connections
        self.instances = instances
        self.instances_stopped = instances_stopped
    
        # Wire all connections
        for conn in self.connections:
            queue: Queue = Queue(maxsize=0)
            conn.set_queue(queue)

            from_id = conn.from_node.ins_id
            from_pin = conn.from_node.pin_id
            to_id = conn.to_node.ins_id
            to_pin = conn.to_node.pin_id

            if from_id == '__this':
                # Own ports are reversed: we read from inputs and write to outputs
                if from_pin not in self.inputs:
                    raise ValueError(f'Input {from_pin} not found in node {self.id}')
                self.inputs[from_pin].queue = queue
            else:
                if from_id not in self.instances:
                    raise ValueError(f'Instance {from_id} not found')
                if from_pin not in self.instances[from_id].outputs:
                    raise ValueError(f'Output {from_pin} not found in instance {from_id}')
                self.instances[from_id].outputs[conn.from_node.pin_id].queue = queue
            if to_id == '__this':
                if to_pin not in self.outputs:
                    raise ValueError(f'Output {to_pin} not found in node {self.id}')
                self.outputs[to_pin].queue = queue
            else:
                if to_id not in self.instances:
                    raise ValueError(f'Instance {to_id} not found')
                if to_pin not in self.instances[to_id].inputs:
                    raise ValueError(f'Input {to_pin} not found in instance {to_id}')
                self.instances[to_id].inputs[conn.to_node.pin_id].queue = queue

    def run(self):
        for instance in self.instances.values():
            logger.debug(f'Running instance {instance.id} of type {instance.node_type}')
            instance.run()
    
        # Wait for all instances to finish
        for v in self.instances_stopped.values():
            logger.debug(f'Waiting for instance to stop')
            v.wait()
        
        self.finish()
        logger.debug(f'Graph {self.id} finished')

    def stop(self):
        # Close all inputs and wait for all instances to stop
        for v in self.inputs.values():
            v.queue.put(EOF)

    def terminate(self):
        """Terminate all instances immediately."""
        for instance in self.instances.values():
            instance.stop()
        self.stop()
        self.finish()

    @property
    def stopped(self) -> Event:
        return self._stopped
    
    @stopped.setter
    def stopped(self, value: Event):
        self._stopped = value

    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict):
        # Load metadata
        node_type = yml.get('nodeId', __name__)
        id = yml['id'] if 'id' in yml else create_instance_id(node_type)
        input_config = yml.get('inputConfig', {})
        display_name = yml.get('displayName', node_type)

        # Load instances and macros
        instances = {}
        instances_stopped = {}
        for ins in yml.get('instances', []):
            ins_id = ins['id']
            if 'macroId' in ins:
                # Only InlineValue macros are supported for now
                if ins['macroId'] != 'InlineValue':
                    raise ValueError(f'Unsupported macro: {ins["macroId"]}')
                ins['nodeId'] = 'InlineValue'
            stopped = Event()
            ins['stopped'] = stopped
            instances[ins_id] = Node.from_yaml(create, ins)
            instances_stopped[ins_id] = stopped
            logger.debug(f'Loaded instance {ins_id}')
    
        # Load connections and graph inputs/outputs
        connections = [Connection.from_yaml(conn) for conn in yml.get('connections', [])]
        inputs = {k: Input(**v) for k, v in yml.get('inputs', {}).items()}
        outputs = {k: Output(**v) for k, v in yml.get('outputs', {}).items()}

        # Instatiate through the constructor
        return cls(
            id=id,
            node_type=node_type,
            input_config=input_config,
            display_name=display_name,
            instances=instances,
            instances_stopped=instances_stopped,
            connections=connections,
            inputs=inputs,
            outputs=outputs
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nodeId': self.node_type,
            'inputConfig': self.input_config,
            'displayName': self.display_name,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'instances': [v.to_dict() for k, v in self.instances.items()],
            'connections': [conn.to_dict() for conn in self.connections]
        }


def create_instance_id(node_type: str) -> str:
    return f"{node_type}-{uuid4()}"

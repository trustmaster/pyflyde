import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from queue import Queue
from threading import Event, Lock, Thread
from typing import Any, Callable
from uuid import uuid4

from flyde.io import InputMode, Input, Output, EOF, isEOF, Connection

logger = logging.getLogger(__name__)


# InstanceFactory is a function that creates a new instance of a node.
# It can create instances dynamically based on the node ID.
InstanceFactory = Callable[[str, dict], Any]


class Node(ABC):
    """Node is the main building block of an application.

    Attributes:
        id (str): A unique identifier for the node.
        node_type (str): The node type identifier.
        input_config (dict): A dictionary of input pin configurations.
        display_name (str): A human-readable name for the node.
        inputs (dict[str, Input]): Node input map.
        outputs (dict[str, Output]): Node output map.
    """

    inputs: dict[str, Input] = {}
    outputs: dict[str, Output] = {}

    def __init__(
        self,
        /,
        id: str,
        node_type: str = "",
        input_config: dict[str, InputMode] = {},
        display_name: str = "",
        inputs: dict[str, Input] = {},
        outputs: dict[str, Output] = {},
        stopped: Event = Event(),
    ):
        node_type = node_type if node_type else self.__class__.__name__
        self._node_type = node_type
        self._id = id if id else create_instance_id(node_type)
        self._input_config = input_config
        self._display_name = display_name if display_name else node_type

        if len(inputs) > 0:
            self.inputs = inputs
        elif hasattr(self.__class__, "inputs") and len(self.inputs) > 0:
            # Copy from class definition, but instance will have own connections
            self.inputs = deepcopy(self.inputs)
        else:
            self.inputs = {}

        for k, v in self.inputs.items():
            v.id = f"{self._id}.{k}"

        if len(outputs) > 0:
            self.outputs = outputs
        elif hasattr(self.__class__, "outputs") and len(self.outputs) > 0:
            # Copy from class definition, but instance will have own connections
            self.outputs = deepcopy(self.outputs)
        else:
            self.outputs = {}

        for k, vv in self.outputs.items():
            vv.id = f"{self._id}.{k}"

        self._stopped = stopped

    @abstractmethod
    def run(self):
        """Run the node. This method should be overridden by subclasses."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the node. This method should be overridden by subclasses."""
        pass

    def finish(self):
        """Finish the component execution gracefully by closing all its outputs and notifying others."""
        for output in self.outputs.values():
            output.queue.put(EOF)
        self._stopped.set()

    @property
    def stopped(self) -> Event:
        return self._stopped

    def shutdown(self):
        """Shutdown the component. This method is optional and can be overridden by subclasses."""
        pass

    def send(self, output_id: str, value: Any):
        """Send a value to an output."""
        if output_id not in self.outputs:
            raise ValueError(f"Output {output_id} not found in node {self._id}")
        self.outputs[output_id].send(value)

    def receive(self, input_id: str) -> Any:
        """Receive a value from an input."""
        if input_id not in self.inputs:
            raise ValueError(f"Input {input_id} not found in node {self._id}")
        return self.inputs[input_id].get()

    @classmethod
    def from_yaml(cls, create: InstanceFactory, yml: dict):
        """Create a node from a parsed YAML dictionary."""
        node_class_name = yml.get("nodeId", "VisualNode")
        if node_class_name == "VisualNode":
            return Graph.from_yaml(create, yml)
        args = {
            "id": yml["id"],
            "input_config": yml.get("inputConfig", {}),
            "display_name": yml.get("displayName", ""),
            "stopped": yml["stopped"],
        }
        # If macro parameters are present, pass them to the constructor
        if "macroData" in yml:
            if "value" in yml["macroData"]:
                args["value"] = yml["macroData"]["value"]
            if "key" in yml["macroData"]:
                args["key"] = yml["macroData"]["key"]
        return create(node_class_name, args)

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "nodeId": self._node_type,
            "inputConfig": self._input_config,
        }


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
        if not hasattr(self, "process"):
            raise NotImplementedError(
                "Component does not have neither run() nor process() method. No code to run."
            )

        def worker():
            logger.debug(f"Running {self._id} worker")
            while not self._stop.is_set():
                logger.debug(f"Waiting for inputs on {self._id}")
                inputs = {}
                non_static_count = 0
                non_static_closed_count = 0
                for key, inp in self.inputs.items():
                    non_static = True
                    if inp.mode == InputMode.STICKY:
                        if not inp.queue.empty():
                            # Update the sticky value with the new value from the queue
                            value = inp.queue.get()
                            inp.set_value(value)
                        elif hasattr(inp, "value") and inp.value is not None:
                            # Use the sticky value if the queue is empty
                            value = inp.value
                        else:
                            # If no value is set, wait for the next value
                            value = inp.queue.get()
                            inp.set_value(value)
                    elif inp.mode == InputMode.STATIC:
                        # Static input values don't change at all
                        non_static = False
                        value = inp.value
                    else:
                        # InputMode.QUEUE is the default mode
                        value = inp.queue.get()

                    inputs[key] = value

                    # Count EOFs received on non-static inputs
                    if non_static:
                        non_static_count += 1
                    if isEOF(value):
                        if non_static:
                            non_static_closed_count += 1

                # If all of the input values are EOF, stop the component
                if non_static_count > 0 and non_static_count == non_static_closed_count:
                    logger.debug(f"All inputs are EOF, stopping {self._id}")
                    self.stop()
                    break

                logger.debug(f"Processing {self._id} with inputs: {inputs}")
                res = self.process(**inputs)  # type: ignore
                if isinstance(res, dict) or (
                    isinstance(res, tuple) and hasattr(res, "_fields")
                ):
                    # Send values to the outputs named as keys
                    for k, v in res.items():  # type: ignore
                        if k not in self.outputs:
                            raise ValueError(
                                f'{self._node_type}.process(): sending to non-existing output "{k}" from return value'
                            )
                        self.outputs[k].send(v)

            self.finish()

        logger.debug(f"Starting {self._id} thread")
        thread = Thread(target=worker, daemon=True)
        thread.start()

    def stop(self):
        """Stop the component execution."""
        logger.debug(f"Stopping {self._id}")
        self._stop.set()

    @classmethod
    def to_ts(cls, name: str = "") -> str:
        """Convert the node to a TypeScript definition."""

        name = cls.__class__.__name__ if name == "" else name  # type: ignore

        inputs_str = ""
        if hasattr(cls, "inputs") and len(cls.inputs) > 0:
            inputs_str = (
                "\n"
                + ",\n".join(
                    [
                        f'    {k}: {{"description": "{v.description}"}}'
                        for k, v in cls.inputs.items()
                    ]
                )
                + "\n"
            )
        outputs_str = ""
        if hasattr(cls, "outputs") and len(cls.outputs) > 0:
            outputs_str = (
                "\n"
                + ",\n".join(
                    [
                        f'    {k}: {{"description": "{v.description}"}}'
                        for k, v in cls.outputs.items()
                    ]
                )
                + "\n"
            )

        safe_doc = ""
        if hasattr(cls, "__doc__") and cls.__doc__:
            safe_doc = (
                cls.__doc__.replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace('"', '\\"')
            )

        return (
            f"export const {name}: CodeNode = {{\n"
            f'  id: "{name}",\n'
            f'  description: "{safe_doc}",\n'
            f"  inputs: {{ {inputs_str} }},\n"
            f"  outputs: {{ {outputs_str} }},\n"
            f"  run: () => {{ return; }},\n"
            f"}};\n\n"
        )


class Graph(Node):
    """A visual graph node that contains other nodes."""

    def __init__(
        self,
        /,
        id: str = "",
        node_type: str = "",
        input_config: dict[str, InputMode] = {},
        display_name: str = "",
        instances: dict[str, Node] = {},
        instances_stopped: dict[str, Event] = {},
        connections: list[Connection] = [],
        inputs: dict[str, Input] = {},
        outputs: dict[str, Output] = {},
        stopped: Event = Event(),
    ):
        super().__init__(
            id=id,
            node_type=node_type,
            input_config=input_config,
            display_name=display_name,
            inputs=inputs,
            outputs=outputs,
            stopped=stopped,
        )

        self._connections = connections
        self._instances = instances
        self._instances_stopped = instances_stopped

        # Wire all connections
        for conn in self._connections:
            queue: Queue = Queue(maxsize=0)
            conn.set_queue(queue)

            from_id = conn.from_node.ins_id
            from_pin = conn.from_node.pin_id
            to_id = conn.to_node.ins_id
            to_pin = conn.to_node.pin_id

            if from_id == "__this":
                # Own ports are reversed: we read from inputs and write to outputs
                if from_pin not in self.inputs:
                    raise ValueError(f"Input {from_pin} not found in node {self._id}")
                self.inputs[from_pin].queue = queue
            else:
                if from_id not in self._instances:
                    raise ValueError(f"Instance {from_id} not found")
                if from_pin not in self._instances[from_id].outputs:
                    raise ValueError(
                        f"Output {from_pin} not found in instance {from_id}"
                    )
                self._instances[from_id].outputs[conn.from_node.pin_id].queue = queue
            if to_id == "__this":
                if to_pin not in self.outputs:
                    raise ValueError(f"Output {to_pin} not found in node {self._id}")
                self.outputs[to_pin].queue = queue
            else:
                if to_id not in self._instances:
                    raise ValueError(f"Instance {to_id} not found")
                if to_pin not in self._instances[to_id].inputs:
                    raise ValueError(f"Input {to_pin} not found in instance {to_id}")
                self._instances[to_id].inputs[conn.to_node.pin_id].queue = queue

    def run(self):
        for instance in self._instances.values():
            logger.debug(
                f"Running instance {instance._id} of type {instance._node_type}"
            )
            instance.run()

        # Wait for all instances to finish
        for k, v in self._instances_stopped.items():
            logger.debug("Waiting for instance to stop")
            v.wait()
            # If the instance has a `shutdown()` handler method, call it at this point
            if hasattr(self._instances[k], "shutdown"):
                self._instances[k].shutdown()

        self.finish()
        logger.debug(f"Graph {self._id} finished")

    def stop(self):
        # Close all inputs and wait for all instances to stop
        for v in self.inputs.values():
            v.queue.put(EOF)

    def terminate(self):
        """Terminate all instances immediately."""
        for instance in self._instances.values():
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
        node_type = yml.get("nodeId", __name__)
        id = yml["id"] if "id" in yml else create_instance_id(node_type)
        input_config = yml.get("inputConfig", {})
        display_name = yml.get("displayName", node_type)

        # Load instances and macros
        instances = {}
        instances_stopped = {}
        for ins in yml.get("instances", []):
            ins_id = ins["id"]
            if "macroId" in ins:
                # Only InlineValue macros are supported for now
                if ins["macroId"] not in ["InlineValue", "GetAttribute"]:
                    raise ValueError(f'Unsupported macro: {ins["macroId"]}')
                ins["nodeId"] = ins["macroId"]
            stopped = Event()
            ins["stopped"] = stopped
            instances[ins_id] = Node.from_yaml(create, ins)
            instances_stopped[ins_id] = stopped
            logger.debug(f"Loaded instance {ins_id}")

        # Load connections and graph inputs/outputs
        connections = [
            Connection.from_yaml(conn) for conn in yml.get("connections", [])
        ]
        inputs = {k: Input(**v) for k, v in yml.get("inputs", {}).items()}
        outputs = {k: Output(**v) for k, v in yml.get("outputs", {}).items()}

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
            outputs=outputs,
        )

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "nodeId": self._node_type,
            "inputConfig": self._input_config,
            "displayName": self._display_name,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "instances": [v.to_dict() for k, v in self._instances.items()],
            "connections": [conn.to_dict() for conn in self._connections],
        }


def create_instance_id(node_type: str) -> str:
    return f"{node_type}-{uuid4()}"

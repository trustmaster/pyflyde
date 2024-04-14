from threading import Event
import unittest
from queue import Queue
from flyde.io import Input, InputMode, Output, EOF
from flyde.node import Component

class RepeatWordNTimes(Component):
    """A component that has both inputs and outputs and a sticky input."""

    inputs = {
        "word": Input(description="The input", type=str),
        "times": Input(description="The number of times to repeat the input", type=int, mode=InputMode.STICKY)
    }

    outputs = {
        "out": Output(description="The output", type=str)
    }

    def process(self, word: str, times: int) -> dict[str, str]:
        return {"out": word * times}


class TestComponentWithStickyInput(unittest.TestCase):
    def setUp(self):
        self.node = RepeatWordNTimes(id="repeat", display_name="Repeat")

    def test_init(self):
        node = self.node
        self.assertEqual(node._id, "repeat")
        self.assertEqual(node._display_name, "Repeat")
        self.assertEqual(node._node_type, "RepeatWordNTimes")
        self.assertEqual(len(node.inputs), 2)
        self.assertEqual(len(node.outputs), 1)
        self.assertEqual(node.inputs["word"].description, "The input")
        self.assertEqual(node.inputs["word"].type, str)
        self.assertEqual(node.inputs["word"].mode, InputMode.QUEUE)
        self.assertEqual(node.inputs["times"].mode, InputMode.STICKY)

    def test_run(self):
        test_cases = [
            {
                "name": "queue input arrives first",
                "sticky_first": False,
                "words": ["meow!", "woof!", "quack!"],
                "times": [3, 2],
                "expected": ["meow!meow!meow!", "woof!woof!", "quack!quack!"]
            },
            {
                "name": "sticky input arrives first",
                "sticky_first": True,
                "words": ["meow!", "woof!", "quack!"],
                "times": [3],
                "expected": ["meow!meow!meow!", "woof!woof!woof!", "quack!quack!quack!"]
            },
        ]
        for test_case in test_cases:
            with self.subTest(test_case["name"]):
                node = self.node
                in_q = Queue()
                times_q = Queue()
                out_q = Queue()
                node.inputs["word"].connect(in_q)
                node.inputs["times"].connect(times_q)
                node.outputs["out"].connect(out_q)
                node.run()
                for i in range(len(test_case["words"])):
                    if test_case["sticky_first"]:
                        if i < len(test_case["times"]):
                            times_q.put(test_case["times"][i])
                        in_q.put(test_case["words"][i])
                    else:
                        in_q.put(test_case["words"][i])
                        if i < len(test_case["times"]):
                            times_q.put(test_case["times"][i])
                    self.assertEqual(out_q.get(), test_case["expected"][i])


class SourceComponent(Component):
    """A component that only has outputs."""

    outputs = {
        "out": Output(description="The output", type=str)
    }

    def process(self) -> dict[str, str]:
        self.stop()
        return {"out": "Hello, world!"}


class TestSourceComponent(unittest.TestCase):
    def setUp(self):
        self.node = SourceComponent(id="source", display_name="Source")

    def test_init(self):
        node = self.node
        self.assertEqual(node._id, "source")
        self.assertEqual(node._display_name, "Source")
        self.assertEqual(node._node_type, "SourceComponent")

    def test_run(self):
        node = self.node
        q = Queue()
        node.outputs["out"].connect(q)
        node.run()
        self.assertEqual(q.get(), "Hello, world!")
        self.assertEqual(q.get(), EOF)
        node.stopped.wait()


class SinkComponent(Component):
    """A component that only has inputs."""

    inputs = {
        "funnel": Input(description="The input", type=str)
    }

    def process(self, funnel: str):
        self.funnel = funnel


class TestSinkComponent(unittest.TestCase):
    def setUp(self):
        self.node = SinkComponent(id="sink", display_name="Sink")

    def test_init(self):
        node = self.node
        self.assertEqual(node._id, "sink")
        self.assertEqual(node._display_name, "Sink")
        self.assertEqual(node._node_type, "SinkComponent")

    def test_run(self):
        node = self.node
        q = Queue()
        node.inputs["funnel"].connect(q)
        node.run()
        q.put("Hello, world!")
        q.put(EOF) # Stop the node
        # Wait for the node to stop
        node.stopped.wait()
        self.assertEqual(node.funnel, "Hello, world!")

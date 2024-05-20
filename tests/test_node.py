import threading
import unittest
from threading import Thread
from queue import Queue
from flyde.io import Input, InputMode, Output, EOF
from flyde.node import Component
from tests.components import RepeatWordNTimes


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
        self.assertEqual(node.inputs["word"]._input_mode, InputMode.QUEUE)
        self.assertEqual(node.inputs["times"]._input_mode, InputMode.STICKY)

    def test_run(self):
        test_cases = [
            {
                "name": "queue input arrives first",
                "sticky_first": False,
                "words": ["meow!", "woof!", "quack!"],
                "times": [3, 2],
                "expected": ["meow!meow!meow!", "woof!woof!", "quack!quack!"],
                "stops": False,
                "remaining": 0,
            },
            {
                "name": "sticky input arrives first",
                "sticky_first": True,
                "words": ["meow!", "woof!", "quack!"],
                "times": [3],
                "expected": [
                    "meow!meow!meow!",
                    "woof!woof!woof!",
                    "quack!quack!quack!",
                ],
                "stops": False,
                "remaining": 0,
            },
            {
                "name": "queue input gets closed",
                "sticky_first": True,
                "words": ["meow!", EOF, "quack!"],
                "times": [3],
                "expected": ["meow!meow!meow!", EOF],
                "stops": True,
                "remaining": 1,
            },
        ]

        node = self.node
        in_q = node.inputs["word"].queue
        times_q = node.inputs["times"].queue

        out_q = Queue()
        node.outputs["out"].connect(out_q)

        node.run()

        for test_case in test_cases:
            with self.subTest(test_case["name"]):
                for i in range(len(test_case["words"])):
                    if test_case["sticky_first"]:
                        if i < len(test_case["times"]):
                            times_q.put(test_case["times"][i])
                        in_q.put(test_case["words"][i])
                    else:
                        in_q.put(test_case["words"][i])
                        if i < len(test_case["times"]):
                            times_q.put(test_case["times"][i])

                    if i < len(test_case["expected"]):
                        self.assertEqual(out_q.get(), test_case["expected"][i])

                if test_case["stops"]:
                    node.stopped.wait()

                self.assertEqual(in_q.qsize(), test_case["remaining"])

    def test_static_input(self):
        node = RepeatWordNTimes(
            id="repeat",
            display_name="Repeat",
            inputs={
                "word": Input(description="The input", type=str),
                "times": Input(
                    description="The number of times to repeat the input",
                    type=int,
                    mode=InputMode.STATIC,
                    value=3,
                ),
            },
            outputs={"out": Output(description="The output", type=str)},
        )

        in_q = node.inputs["word"].queue
        out_q = Queue()
        node.outputs["out"].connect(out_q)
        node.run()

        in_q.put("meow!")
        in_q.put("woof!")
        in_q.put(EOF)
        self.assertEqual(out_q.get(), "meow!meow!meow!")
        self.assertEqual(out_q.get(), "woof!woof!woof!")
        self.assertEqual(out_q.get(), EOF)
        self.assertEqual(in_q.qsize(), 0)

    def test_to_ts(self):
        self.maxDiff = None

        def expected_typescript(name):
            return """export const {NAME}: CodeNode = {
  id: "{NAME}",
  description: "A component that has both inputs and outputs and a sticky input.",
  inputs: {
    word: { description: "The input" },
    times: { description: "The number of times to repeat the input" }
  },
  outputs: {
    out: { description: "The output" }
  },
  run: () => { return; },
};

""".replace(
                "{NAME}", name
            )

        self.assertEqual(
            RepeatWordNTimes.to_ts(), expected_typescript("RepeatWordNTimes")
        )
        self.assertEqual(
            RepeatWordNTimes.to_ts("RepeatWord"), expected_typescript("RepeatWord")
        )

    def test_from_yaml(self):
        yaml = {
            "id": "repeat",
            "nodeId": "RepeatWordNTimes",
            "inputConfig": {},
            "displayName": "Repeat",
        }

        def factory(class_name: str, args: dict):
            return RepeatWordNTimes(**args)

        node = Component.from_yaml(factory, yaml)
        self.assertEqual(node._id, "repeat")
        self.assertEqual(node._display_name, "Repeat")
        self.assertEqual(node._node_type, "RepeatWordNTimes")
        self.assertEqual(len(node.inputs), 2)

    def test_from_yaml_with_macrodata(self):
        yaml = {
            "id": "repeat",
            "nodeId": "RepeatWordNTimes",
            "inputConfig": {},
            "displayName": "Repeat",
            "macroData": {"value": 100, "key": "foo"},
        }

        def factory(class_name: str, args: dict):
            self.assertEqual(args["macro_data"]["value"], yaml["macroData"]["value"])
            self.assertEqual(args["macro_data"]["key"], yaml["macroData"]["key"])
            # Drop macro_data from the args, otherwise there will be an exception
            # because the constructor doesn't support it.
            del args["macro_data"]
            return RepeatWordNTimes(**args)

        node = Component.from_yaml(factory, yaml)
        self.assertEqual(node._id, "repeat")
        self.assertEqual(node._display_name, "Repeat")
        self.assertEqual(node._node_type, "RepeatWordNTimes")
        self.assertEqual(len(node.inputs), 2)

    def test_to_dict(self):
        node = self.node
        expected = {
            "id": "repeat",
            "nodeId": "RepeatWordNTimes",
            "inputConfig": {},
            "displayName": "Repeat",
        }
        self.assertEqual(node.to_dict(), expected)


class SourceComponent(Component):
    """A component that only has outputs."""

    outputs = {"out": Output(description="The output", type=str)}

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
        "word": Input(description="The input", type=str),
        "output": Input(description="Object to store result in", type=Queue),
    }

    def process(self, word: str, output: Queue):
        output.put(word)


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
        q = node.inputs["word"].queue
        o = node.inputs["output"].queue
        res = Queue()

        node.run()
        q.put("Hello, world!")
        q.put(EOF)  # Stop the node
        o.put(res)
        o.put(EOF)
        # Wait for the node to stop
        node.stopped.wait()
        msg = res.get()
        self.assertEqual(msg, "Hello, world!")


class CustomRunComponent(Component):
    """A component that has a custom run and shutdown handlers."""

    inputs = {
        "s": Input(description="Individual strings", type=str),
    }

    outputs = {"l": Output(description="List of strings", type=list)}

    def run(self):
        self.strings = []

        def run_loop(self):
            while not self._stop.is_set():
                try:
                    string = self.receive("s")
                except Exception as e:
                    if e == EOF:
                        self.stop()
                    break
                self.strings.append(string)
            self.send("l", self.strings)

        thread = Thread(target=run_loop, args=(self,))
        thread.start()
        thread.join()
        self.finish()


class TestCustomRunComponent(unittest.TestCase):
    def test_run(self):
        test_cases = [
            {
                "name": "normal run",
                "inputs": ["a", "b", "c"],
                "expected": ["a", "b", "c"],
            },
        ]

        for test_case in test_cases:
            with self.subTest(test_case["name"]):
                node = CustomRunComponent(id="custom_run", display_name="Custom Run")
                in_q = node.inputs["s"].queue
                out_q = Queue()
                node.outputs["l"].connect(out_q)

                for i in range(len(test_case["inputs"])):
                    in_q.put(test_case["inputs"][i])
                in_q.put(EOF)

                node.run()

                self.assertEqual(out_q.get(), test_case["expected"])
                self.assertEqual(out_q.get(), EOF)

                node.stopped.wait()


class NoProcessComponent(Component):
    """A component to test no inputs, outputs, and no process method."""


class TestNoProcessComponent(unittest.TestCase):
    def test_no_process(self):
        node = NoProcessComponent(id="invalid", display_name="Invalid")
        with self.assertRaises(NotImplementedError):
            node.run()


class InvalidSendProcess(Component):
    """A component that tries to send a message without a corresponding output."""

    inputs = {
        "s": Input(description="Individual strings", type=str),
    }

    def process(self, s: str) -> dict[str, str]:
        return {"out": s}


class TestInvalidSendProcess(unittest.TestCase):
    def test_invalid_send(self):
        node = InvalidSendProcess(id="invalid", display_name="Invalid")
        in_q = node.inputs["s"].queue

        def handle_exception(exc):
            self.assertIsInstance(exc.exc_value, ValueError)

        threading.excepthook = handle_exception
        node.run()

        in_q.put("a")
        in_q.put(EOF)
        node.stopped.wait()

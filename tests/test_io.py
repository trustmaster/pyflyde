import unittest
from queue import Queue
from flyde.io import (
    Input,
    InputMode,
    Output,
    EOF,
    Connection,
    ConnectionNode,
    Requiredness,
)


class TestInput(unittest.TestCase):
    def setUp(self):
        self.input = Input()

    def test_init(self):
        test_cases = [
            {"name": "default input", "expected": (InputMode.QUEUE, None, None)},
            {
                "name": "input with type",
                "type": int,
                "expected": (InputMode.QUEUE, int, None),
            },
            {
                "name": "input with value",
                "value": 10,
                "expected": (InputMode.QUEUE, None, 10),
            },
            {
                "name": "input with type and invalid value",
                "type": int,
                "value": "string",
                "expected": (InputMode.QUEUE, int, None),
                "raises": ValueError,
            },
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case["name"]):
                args = {}
                if "type" in test_case:
                    args["type"] = test_case["type"]
                if "value" in test_case:
                    args["value"] = test_case["value"]
                if "raises" in test_case:
                    with self.assertRaises(test_case["raises"]):
                        self.input = Input(**args)
                else:
                    self.input = Input(**args)
                    self.assertEqual(
                        (self.input._input_mode, self.input.type, self.input._value),
                        test_case["expected"],
                    )

    def test_set_value(self):
        test_cases = [
            {
                "name": "valid integer",
                "type": int,
                "value": 10,
                "expected": 10,
                "raises": None,
            },
            {
                "name": "invalid string",
                "type": int,
                "value": "string",
                "expected": None,
                "raises": ValueError,
            },
            {
                "name": "EOF as a valid case",
                "type": int,
                "value": EOF,
                "expected": EOF,
                "raises": None,
            },
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case["name"]):
                self.input = Input(type=test_case["type"])
                if test_case["raises"]:
                    with self.assertRaises(test_case["raises"]):
                        self.input.value = test_case["value"]
                else:
                    self.input.value = test_case["value"]
                    self.assertEqual(self.input._value, test_case["expected"])

    def test_is_connected(self):
        test_cases = [
            {
                "name": "input not connected",
                "expected": False,
                "connect_queue": False,
            },
            {
                "name": "input connected",
                "expected": True,
                "connect_queue": True,
            },
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case["name"]):
                self.input = Input()
                if test_case["connect_queue"]:
                    _ = self.input.queue  # Accessing the queue to connect it
                self.assertEqual(self.input.is_connected, test_case["expected"])

    def test_get(self):
        test_cases = [
            {
                "name": "get valid value in queue mode",
                "mode": InputMode.QUEUE,
                "queue_values": [10],
                "expected": 10,
                "connected": True,
                "required": Requiredness.REQUIRED,
            },
            {
                "name": "get value in static mode",
                "mode": InputMode.STATIC,
                "value": 10,
                "expected": 10,
                "connected": False,
                "required": Requiredness.REQUIRED,
            },
            {
                "name": "get value in sticky mode",
                "mode": InputMode.STICKY,
                "value": 10,
                "expected": 10,
                "connected": True,
                "required": Requiredness.REQUIRED,
            },
            {
                "name": "get value in queue mode with optional input",
                "mode": InputMode.QUEUE,
                "value": 5,
                "queue_values": [],
                "expected": 5,
                "connected": False,
                "required": Requiredness.OPTIONAL,
            },
            {
                "name": "get value in sticky mode with required if connected",
                "mode": InputMode.STICKY,
                "value": 10,
                "expected": 10,
                "connected": True,
                "required": Requiredness.REQUIRED_IF_CONNECTED,
            },
            {
                "name": "get value in sticky mode with required if not connected",
                "mode": InputMode.STICKY,
                "value": 10,
                "expected": 10,
                "connected": False,
                "required": Requiredness.REQUIRED_IF_CONNECTED,
            },
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case["name"]):
                self.input = Input(
                    mode=test_case["mode"],
                    required=test_case["required"],
                    value=test_case.get("value"),
                )
                if test_case["connected"]:
                    _ = self.input.queue  # Accessing the queue to connect it
                if "queue_values" in test_case and len(test_case["queue_values"]) > 0:
                    queue = self.input.queue
                    for value in test_case["queue_values"]:
                        queue.put(value)

                result = self.input.get()
                self.assertEqual(result, test_case["expected"])

    def test_empty(self):
        test_cases = [
            {
                "name": "empty input in queue mode",
                "mode": InputMode.QUEUE,
                "queue_values": [],
                "expected": True,
            },
            {
                "name": "non-empty input in queue mode",
                "mode": InputMode.QUEUE,
                "queue_values": [10],
                "expected": False,
            },
            {
                "name": "empty input in static mode",
                "mode": InputMode.STATIC,
                "value": None,
                "expected": True,
            },
            {
                "name": "non-empty input in static mode",
                "mode": InputMode.STATIC,
                "value": 10,
                "expected": False,
            },
            {
                "name": "empty input in sticky mode",
                "mode": InputMode.STICKY,
                "value": None,
                "expected": True,
            },
            {
                "name": "non-empty input in sticky mode",
                "mode": InputMode.STICKY,
                "value": 10,
                "expected": False,
            },
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case["name"]):
                self.input = Input(mode=test_case["mode"])
                if "queue_values" in test_case:
                    queue = self.input.queue
                    for value in test_case["queue_values"]:
                        queue.put(value)
                if "value" in test_case:
                    self.input.value = test_case["value"]
                self.assertEqual(self.input.empty(), test_case["expected"])

    def test_count(self):
        test_cases = [
            {
                "name": "count with one item in queue mode",
                "mode": InputMode.QUEUE,
                "queue_values": [10],
                "expected": 1,
            },
            {
                "name": "count with no item in queue mode",
                "mode": InputMode.QUEUE,
                "queue_values": [],
                "expected": 0,
            },
            {
                "name": "count in static mode",
                "mode": InputMode.STATIC,
                "value": 10,
                "expected": 1,
            },
            {
                "name": "count in sticky mode",
                "mode": InputMode.STICKY,
                "value": 10,
                "expected": 1,
            },
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case["name"]):
                self.input = Input(mode=test_case["mode"])
                if "queue_values" in test_case:
                    queue = self.input.queue
                    for value in test_case["queue_values"]:
                        queue.put(value)
                if "value" in test_case:
                    self.input.value = test_case["value"]
                self.assertEqual(self.input.count(), test_case["expected"])

    def test_ref_count(self):
        # Initial ref count is 0
        input = Input()
        self.assertEqual(input.ref_count, 0)
        # Increment ref count to 1
        input.inc_ref_count()
        self.assertEqual(input.ref_count, 1)
        # Decrement ref count to 0
        input.dec_ref_count()
        self.assertEqual(input.ref_count, 0)


class TestOutput(unittest.TestCase):
    def setUp(self):
        self.output = Output()

    def test_init(self):
        test_cases = [
            {"name": "default output", "expected": None},
            {"name": "output with type", "type": int, "expected": int},
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case["name"]):
                args = {}
                if "type" in test_case:
                    args["type"] = test_case["type"]
                self.output = Output(**args)
                self.assertEqual(self.output.type, test_case["expected"])

    def test_connect(self):
        queue = Queue()
        self.output.connect(queue)
        self.assertEqual(self.output._queues[0], queue)

    def test_send(self):
        test_cases = [
            {
                "name": "put valid integer",
                "type": int,
                "value": 10,
                "expected": 10,
                "raises": None,
            },
            {
                "name": "put invalid string",
                "type": int,
                "value": "string",
                "expected": None,
                "raises": ValueError,
            },
            {
                "name": "put EOF as a valid case",
                "type": int,
                "value": EOF,
                "expected": EOF,
                "raises": None,
            },
        ]
        for test_case in test_cases:
            with self.subTest(case=test_case["name"]):
                self.output = Output(type=test_case["type"])
                queue = Queue()
                self.output.connect(queue)
                if test_case["raises"]:
                    with self.assertRaises(test_case["raises"]):
                        self.output.send(test_case["value"])
                else:
                    self.output.send(test_case["value"])
                    value = queue.get()
                    self.assertEqual(value, test_case["expected"])


class TestConnection(unittest.TestCase):
    def setUp(self):
        self.from_node = ConnectionNode("from_id", "from_pin")
        self.to_node = ConnectionNode("to_id", "to_pin")
        self.connection = Connection(self.from_node, self.to_node)

    def test_init(self):
        self.assertEqual(self.connection.from_node, self.from_node)
        self.assertEqual(self.connection.to_node, self.to_node)
        self.assertFalse(self.connection.delayed)
        self.assertFalse(self.connection.hidden)

    def test_from_yaml(self):
        yml = {
            "from": {"insId": "from_id", "pinId": "from_pin"},
            "to": {"insId": "to_id", "pinId": "to_pin"},
            "delayed": True,
            "hidden": True,
        }
        connection = Connection.from_yaml(yml)
        self.assertEqual(connection.from_node.ins_id, "from_id")
        self.assertEqual(connection.from_node.pin_id, "from_pin")
        self.assertEqual(connection.to_node.ins_id, "to_id")
        self.assertEqual(connection.to_node.pin_id, "to_pin")
        self.assertTrue(connection.delayed)
        self.assertTrue(connection.hidden)

    def test_to_dict(self):
        self.connection.delayed = True
        self.connection.hidden = True
        expected_dict = {
            "from": {"insId": "from_id", "pinId": "from_pin"},
            "to": {"insId": "to_id", "pinId": "to_pin"},
            "delayed": True,
            "hidden": True,
        }
        self.assertEqual(self.connection.to_dict(), expected_dict)

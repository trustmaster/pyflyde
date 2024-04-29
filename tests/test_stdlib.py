import unittest
from queue import Queue
from types import SimpleNamespace

from flyde.io import EOF
from flyde.stdlib import InlineValue, GetAttribute


class TestInlineValue(unittest.TestCase):
    def test_inline_value(self):
        test_case = {
            "inputs": {},
            "outputs": {"value": "Hello"},
        }
        out_q = Queue()
        node = InlineValue("Hello", id="test_inline_value")
        node.outputs["value"].connect(out_q)
        node.run()
        self.assertEqual(
            test_case["outputs"]["value"], node.outputs["value"].queue.get()
        )
        node.stopped.wait()
        self.assertTrue(node.stopped.is_set())


class TestGetAttribute(unittest.TestCase):
    def test_get_attribute(self):
        test_cases = [
            {
                "name": "static attribute from a dict",
                "key": {
                    "mode": "static",
                    "value": "name",
                },
                "inputs": {
                    "object": [
                        {"name": "Alice"},
                        {"name": "Bob"},
                        {"nananan": "Charlie"},
                        EOF,
                    ],
                    "attribute": [],
                },
                "outputs": ["Alice", "Bob", None, EOF],
            },
            {
                "name": "sticky attribute from an object",
                "key": {
                    "mode": "sticky",
                    "value": "name",
                },
                "inputs": {
                    "object": [
                        SimpleNamespace(name="Alice"),
                        SimpleNamespace(name="Bob"),
                        SimpleNamespace(nananan="Charlie"),
                        EOF,
                    ],
                    "attribute": ["name"],
                },
                "outputs": ["Alice", "Bob", None, EOF],
            },
            {
                "name": "dynamic attribute from a dict",
                "key": {},
                "inputs": {
                    "object": [
                        {"name": "Alice"},
                        {"name": "Bob"},
                        {"nananan": "Charlie"},
                        EOF,
                    ],
                    "attribute": ["name", "name", "nananan", EOF],
                },
                "outputs": ["Alice", "Bob", "Charlie", EOF],
            },
            {
                "name": "sticky attribute and non-object",
                "key": {
                    "mode": "sticky",
                    "value": "name",
                },
                "inputs": {
                    "object": [
                        {"name": "Alice"},
                        "bob",
                        123,
                        EOF,
                    ],
                    "attribute": ["name"],
                },
                "outputs": ["Alice", None, None, EOF],
            },
        ]

        for test_case in test_cases:
            obj_q = Queue()
            attr_q = Queue()
            out_q = Queue()
            node = GetAttribute(test_case["key"], id="test_get_attribute")
            node.inputs["object"].connect(obj_q)
            if len(test_case["inputs"]["attribute"]) > 0:
                node.inputs["attribute"].connect(attr_q)
            node.outputs["value"].connect(out_q)
            node.run()
            for i in range(len(test_case["inputs"]["object"])):
                obj_q.put(test_case["inputs"]["object"][i])
                if len(test_case["inputs"]["attribute"]) > 0 and i < len(
                    test_case["inputs"]["attribute"]
                ):
                    attr_q.put(test_case["inputs"]["attribute"][i])
                self.assertEqual(
                    test_case["outputs"][i], node.outputs["value"].queue.get()
                )

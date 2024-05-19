import unittest
from queue import Queue
from types import SimpleNamespace

from flyde.io import EOF
from flyde.stdlib import InlineValue, Conditional, GetAttribute


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
        self.assertEqual(test_case["outputs"]["value"], out_q.get())
        node.stopped.wait()
        self.assertTrue(node.stopped.is_set())


class TestConditional(unittest.TestCase):
    def test_conditional(self):
        test_cases = [
            {
                "name": "equal condition static string",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "Apple",
                    },
                    "propertyPath": "",
                    "condition": {
                        "type": "EQUAL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": ["Apple", "Banana", "apple", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["Apple", EOF],
                    "false": ["Banana", "apple", EOF],
                },
                "raises": None,
            },
            {
                "name": "equal condition dynamic property number",
                "yml": {
                    "compareTo": {
                        "mode": "dynamic",
                        "propertyPath": "price",
                    },
                    "propertyPath": "price",
                    "condition": {
                        "type": "EQUAL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [
                        {"price": 100},
                        {"price": 200},
                        {"price": 300},
                        EOF,
                    ],
                    "compareTo": [
                        {"price": 100},
                        {"price": 200},
                        {"price": 400},
                        EOF,
                    ],
                },
                "outputs": {
                    "true": [{"price": 100}, {"price": 200}, EOF],
                    "false": [{"price": 300}, EOF],
                },
                "raises": None,
            },
            {
                "name": "not equal condition dynamic string compare to value on false",
                "yml": {
                    "compareTo": {
                        "mode": "dynamic",
                    },
                    "condition": {
                        "type": "NOT_EQUAL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "compareTo",
                    },
                },
                "inputs": {
                    "value": ["Apple", "Banana", "apple", "Grape", EOF],
                    "compareTo": ["Apple", "Orange", "apple", "Vinegar", EOF],
                },
                "outputs": {
                    "true": ["Banana", "Grape", EOF],
                    "false": ["Apple", "apple", EOF],
                },
                "raises": None,
            },
        ]

        for test_case in test_cases:
            true_q = Queue()
            false_q = Queue()

            if test_case["raises"] is not None:
                with self.assertRaises(test_case["raises"]):
                    node = Conditional(test_case["yml"], id="test_conditional")
                    return

            node = Conditional(test_case["yml"], id="test_conditional")
            val_q = node.inputs["value"].queue
            cmp_q = node.inputs["compareTo"].queue
            node.outputs["true"].connect(true_q)
            node.outputs["false"].connect(false_q)

            node.run()

            for i in range(len(test_case["inputs"]["value"])):
                val_q.put(test_case["inputs"]["value"][i])
            for i in range(len(test_case["inputs"]["compareTo"])):
                cmp_q.put(test_case["inputs"]["compareTo"][i])
            for i in range(len(test_case["outputs"]["true"])):
                self.assertEqual(test_case["outputs"]["true"][i], true_q.get())
            for i in range(len(test_case["outputs"]["false"])):
                self.assertEqual(test_case["outputs"]["false"][i], false_q.get())

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
            attr_q = Queue()
            out_q = Queue()
            node = GetAttribute(test_case["key"], id="test_get_attribute")
            obj_q = node.inputs["object"].queue
            if len(test_case["inputs"]["attribute"]) > 0:
                attr_q = node.inputs["attribute"].queue
            node.outputs["value"].connect(out_q)
            node.run()
            for i in range(len(test_case["inputs"]["object"])):
                obj_q.put(test_case["inputs"]["object"][i])
                if len(test_case["inputs"]["attribute"]) > 0 and i < len(
                    test_case["inputs"]["attribute"]
                ):
                    attr_q.put(test_case["inputs"]["attribute"][i])
                self.assertEqual(test_case["outputs"][i], out_q.get())

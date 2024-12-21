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
        node = InlineValue(macro_data={"value": "Hello"}, id="test_inline_value")
        node.outputs["value"].connect(out_q)
        node.run()
        self.assertEqual(test_case["outputs"]["value"], out_q.get())
        node.stopped.wait()
        self.assertTrue(node.stopped.is_set())

    def test_inline_value_dict(self):
        test_case = {
            "inputs": {},
            "outputs": {"value": "Hello"},
        }
        out_q = Queue()
        node = InlineValue(
            macro_data={"value": {"type": "string", "value": "Hello"}},
            id="test_inline_value",
        )
        node.outputs["value"].connect(out_q)
        node.run()
        self.assertEqual(test_case["outputs"]["value"], out_q.get())
        node.stopped.wait()
        self.assertTrue(node.stopped.is_set())


class TestConditional(unittest.TestCase):
    def test_conditional(self):
        test_cases = [
            {
                "name": "equal static string",
                "yml": {
                    "leftOperand": {
                        "type": "static",
                        "value": "Apple",
                    },
                    "rightOperand": {
                        "type": "dynamic",
                    },
                    "condition": {
                        "type": "EQUAL",
                    },
                },
                "inputs": {
                    "leftOperand": [],
                    "rightOperand": ["Apple", "Banana", "apple", EOF],
                },
                "outputs": {
                    "true": ["Apple", EOF],
                    "false": ["Apple", "Apple", EOF],
                },
                "raises": None,
            },
            {
                "name": "not equal dynamic string",
                "yml": {
                    "leftOperand": {
                        "type": "dynamic",
                    },
                    "rightOperand": {
                        "type": "dynamic",
                    },
                    "condition": {
                        "type": "NOT_EQUAL",
                    },
                },
                "inputs": {
                    "leftOperand": ["Apple", "Banana", "apple", "Grape", EOF],
                    "rightOperand": ["Apple", "Orange", "apple", "Vinegar", EOF],
                },
                "outputs": {
                    "true": ["Banana", "Grape", EOF],
                    "false": ["Apple", "apple", EOF],
                },
            },
            {
                "name": "contains static string",
                "yml": {
                    "leftOperand": {
                        "type": "dynamic",
                    },
                    "rightOperand": {
                        "type": "static",
                        "value": "Apple",
                    },
                    "condition": {
                        "type": "CONTAINS",
                    },
                },
                "inputs": {
                    "leftOperand": [
                        "Apple Tart",
                        "Banana Bread",
                        "Grape Juice",
                        "Fresh Apple Juice",
                        EOF,
                    ],
                    "rightOperand": [],
                },
                "outputs": {
                    "true": ["Apple Tart", "Fresh Apple Juice", EOF],
                    "false": ["Banana Bread", "Grape Juice", EOF],
                },
            },
            {
                "name": "not contains static string",
                "yml": {
                    "leftOperand": {
                        "type": "dynamic",
                    },
                    "rightOperand": {
                        "type": "static",
                        "value": "Apple",
                    },
                    "condition": {
                        "type": "NOT_CONTAINS",
                    },
                },
                "inputs": {
                    "leftOperand": [
                        "Apple Tart",
                        "Banana Bread",
                        "Grape Juice",
                        "Fresh Apple Juice",
                        EOF,
                    ],
                    "rightOperand": [],
                },
                "outputs": {
                    "true": ["Banana Bread", "Grape Juice", EOF],
                    "false": ["Apple Tart", "Fresh Apple Juice", EOF],
                },
            },
            {
                "name": "regex matches static",
                "yml": {
                    "leftOperand": {
                        "type": "dynamic",
                    },
                    "rightOperand": {
                        "type": "static",
                        "value": "^[A-Z]",
                    },
                    "condition": {
                        "type": "REGEX_MATCHES",
                    },
                },
                "inputs": {
                    "leftOperand": ["Apple", "banana", "Grape", "apple", "2cherries", EOF],
                    "rightOperand": [],
                },
                "outputs": {
                    "true": ["Apple", "Grape", EOF],
                    "false": ["banana", "apple", "2cherries", EOF],
                },
            },
            {
                "name": "exists",
                "yml": {
                    "leftOperand": {
                        "type": "dynamic",
                    },
                    "rightOperand": {
                        "type": "static",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "EXISTS",
                    },
                },
                "inputs": {
                    "leftOperand": ["Apple", "", " ", "  ", "banana", EOF],
                    "rightOperand": [],
                },
                "outputs": {
                    "true": ["Apple", " ", "  ", "banana", EOF],
                    "false": ["", EOF],
                },
            },
            {
                "name": "does not exist",
                "yml": {
                    "leftOperand": {
                        "type": "dynamic",
                    },
                    "rightOperand": {
                        "type": "static",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "DOES_NOT_EXIST",
                    },
                },
                "inputs": {
                    "leftOperand": ["Apple", "", " ", "  ", "banana", EOF],
                    "rightOperand": [],
                },
                "outputs": {
                    "true": ["", EOF],
                    "false": ["Apple", " ", "  ", "banana", EOF],
                },
            },
            {
                "name": "unsupported condition type",
                "yml": {
                    "leftOperand": {
                        "type": "dynamic",
                    },
                    "rightOperand": {
                        "type": "dynamic",
                    },
                    "condition": {
                        "type": "UNSUPPORTED",
                    },
                },
                "inputs": {
                    "leftOperand": ["Apple", "Banana", "apple", EOF],
                    "rightOperand": [],
                },
                "outputs": {
                    "true": [EOF],
                    "false": [EOF],
                },
                "raises": ValueError,
            },
        ]

        for test_case in test_cases:
            true_q = Queue()
            false_q = Queue()

            if "raises" in test_case and test_case["raises"] is not None:
                with self.assertRaises(test_case["raises"]):
                    node = Conditional(test_case["yml"], id="test_conditional")
                continue

            node = Conditional(test_case["yml"], id="test_conditional")
            left_q = node.inputs["leftOperand"].queue
            right_q = node.inputs["rightOperand"].queue
            node.outputs["true"].connect(true_q)
            node.outputs["false"].connect(false_q)

            node.run()

            for i in range(len(test_case["inputs"]["leftOperand"])):
                left_q.put(test_case["inputs"]["leftOperand"][i])
            for i in range(len(test_case["inputs"]["rightOperand"])):
                right_q.put(test_case["inputs"]["rightOperand"][i])
            for i in range(len(test_case["outputs"]["true"])):
                self.assertEqual(
                    test_case["outputs"]["true"][i],
                    true_q.get(),
                    f"Test case: {test_case['name']} #{i} true",
                )
            for i in range(len(test_case["outputs"]["false"])):
                self.assertEqual(
                    test_case["outputs"]["false"][i],
                    false_q.get(),
                    f"Test case: {test_case['name']} #{i} false",
                )

            node.stopped.wait()
            self.assertTrue(node.stopped.is_set())


class TestGetAttribute(unittest.TestCase):
    def test_get_attribute(self):
        test_cases = [
            {
                "name": "static attribute from a dict",
                "key": {
                    "type": "static",
                    "value": "name",
                },
                "inputs": {
                    "object": [
                        {"name": "Alice"},
                        {"name": "Bob"},
                        {"nananan": "Charlie"},
                        EOF,
                    ],
                    "key": [],
                },
                "outputs": ["Alice", "Bob", None, EOF],
            },
            {
                "name": "sticky attribute from an object",
                "key": {
                    "type": "sticky",
                    "value": "name",
                },
                "inputs": {
                    "object": [
                        SimpleNamespace(name="Alice"),
                        SimpleNamespace(name="Bob"),
                        SimpleNamespace(nananan="Charlie"),
                        EOF,
                    ],
                    "key": ["name"],
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
                    "key": ["name", "name", "nananan", EOF],
                },
                "outputs": ["Alice", "Bob", "Charlie", EOF],
            },
            {
                "name": "sticky attribute and non-object",
                "key": {
                    "type": "sticky",
                    "value": "name",
                },
                "inputs": {
                    "object": [
                        {"name": "Alice"},
                        "bob",
                        123,
                        EOF,
                    ],
                    "key": ["name"],
                },
                "outputs": ["Alice", None, None, EOF],
            },
        ]

        for test_case in test_cases:
            attr_q = Queue()
            out_q = Queue()
            node = GetAttribute(macro_data={"key": test_case["key"]}, id="test_get_attribute")
            obj_q = node.inputs["object"].queue
            if len(test_case["inputs"]["key"]) > 0:
                attr_q = node.inputs["key"].queue
            node.outputs["value"].connect(out_q)
            node.run()
            for i in range(len(test_case["inputs"]["object"])):
                obj_q.put(test_case["inputs"]["object"][i])
                if len(test_case["inputs"]["key"]) > 0 and i < len(test_case["inputs"]["key"]):
                    attr_q.put(test_case["inputs"]["key"][i])
                self.assertEqual(test_case["outputs"][i], out_q.get())

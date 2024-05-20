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


class TestConditional(unittest.TestCase):
    def test_conditional(self):
        test_cases = [
            {
                "name": "equal static string",
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
                "name": "equal dynamic property number",
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
            },
            {
                "name": "equal dynamic object property number, return compareTo property",
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
                        "type": "compareTo",
                    },
                    "falseValue": {
                        "type": "compareTo",
                    },
                },
                "inputs": {
                    "value": [
                        SimpleNamespace(price=100, src="value"),
                        SimpleNamespace(price=200, src="value"),
                        SimpleNamespace(price=300, src="value"),
                        EOF,
                    ],
                    "compareTo": [
                        SimpleNamespace(price=100, src="compareTo"),
                        SimpleNamespace(price=200, src="compareTo"),
                        SimpleNamespace(price=400, src="compareTo"),
                        EOF,
                    ],
                },
                "outputs": {
                    "true": [
                        SimpleNamespace(price=100, src="compareTo"),
                        SimpleNamespace(price=200, src="compareTo"),
                        EOF,
                    ],
                    "false": [SimpleNamespace(price=400, src="compareTo"), EOF],
                },
            },
            {
                "name": "not equal dynamic string compare to value on false",
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
            },
            {
                "name": "greater than static",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "number",
                        "value": 100,
                    },
                    "condition": {
                        "type": "GREATER_THAN",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [100, 200, 300, EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [200, 300, EOF],
                    "false": [100, EOF],
                },
            },
            {
                "name": "greater than or equal static",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "number",
                        "value": 100,
                    },
                    "condition": {
                        "type": "GREATER_THAN_OR_EQUAL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [100, 200, 50, 300, 70, EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [100, 200, 300, EOF],
                    "false": [50, 70, EOF],
                },
            },
            {
                "name": "less than static",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "number",
                        "value": 100,
                    },
                    "condition": {
                        "type": "LESS_THAN",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [100, 70, 200, 50, EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [70, 50, EOF],
                    "false": [100, 200, EOF],
                },
            },
            {
                "name": "less than or equal static",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "number",
                        "value": 100,
                    },
                    "condition": {
                        "type": "LESS_THAN_OR_EQUAL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [100, 70, 200, 50, 150, EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [100, 70, 50, EOF],
                    "false": [200, 150, EOF],
                },
            },
            {
                "name": "list contains static",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "Apple",
                    },
                    "condition": {
                        "type": "CONTAINS",
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
                        ["Apple", "Banana"],
                        ["Banana", "Grape"],
                        ["Grape", "Apple"],
                        EOF,
                    ],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [["Apple", "Banana"], ["Grape", "Apple"], EOF],
                    "false": [["Banana", "Grape"], EOF],
                },
            },
            {
                "name": "string contains static",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "Apple",
                    },
                    "condition": {
                        "type": "CONTAINS",
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
                        "Apple Tart",
                        "Banana Bread",
                        "Grape Juice",
                        "Fresh Apple Juice",
                        EOF,
                    ],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["Apple Tart", "Fresh Apple Juice", EOF],
                    "false": ["Banana Bread", "Grape Juice", EOF],
                },
            },
            {
                "name": "string not contains static",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "Apple",
                    },
                    "condition": {
                        "type": "NOT_CONTAINS",
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
                        "Apple Tart",
                        "Banana Bread",
                        "Grape Juice",
                        "Fresh Apple Juice",
                        EOF,
                    ],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["Banana Bread", "Grape Juice", EOF],
                    "false": ["Apple Tart", "Fresh Apple Juice", EOF],
                },
            },
            {
                "name": "regex matches static",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "^[A-Z]",
                    },
                    "condition": {
                        "type": "REGEX_MATCHES",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": ["Apple", "banana", "Grape", "apple", "2cherries", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["Apple", "Grape", EOF],
                    "false": ["banana", "apple", "2cherries", EOF],
                },
            },
            {
                "name": "is empty",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "IS_EMPTY",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": ["Apple", "", " ", "  ", "banana", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["", EOF],
                    "false": ["Apple", " ", "  ", "banana", EOF],
                },
            },
            {
                "name": "is not empty",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "IS_NOT_EMPTY",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": ["Apple", "", " ", "  ", "banana", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["Apple", " ", "  ", "banana", EOF],
                    "false": ["", EOF],
                },
            },
            {
                "name": "is null",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "IS_NULL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [None, "Apple", None, "banana", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [None, None, EOF],
                    "false": ["Apple", "banana", EOF],
                },
            },
            {
                "name": "is not null",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "IS_NOT_NULL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [None, "Apple", None, "banana", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["Apple", "banana", EOF],
                    "false": [None, None, EOF],
                },
            },
            {
                "name": "is undefined",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "IS_UNDEFINED",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [None, "Apple", None, "banana", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [None, None, EOF],
                    "false": ["Apple", "banana", EOF],
                },
            },
            {
                "name": "is not undefined",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "IS_NOT_UNDEFINED",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [None, "Apple", None, "banana", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["Apple", "banana", EOF],
                    "false": [None, None, EOF],
                },
            },
            {
                "name": "dict has property",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "name",
                    },
                    "condition": {
                        "type": "HAS_PROPERTY",
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
                        {"name": "Alice"},
                        {"name": "Bob"},
                        {"nananan": "Charlie"},
                        EOF,
                    ],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [{"name": "Alice"}, {"name": "Bob"}, EOF],
                    "false": [{"nananan": "Charlie"}, EOF],
                },
            },
            {
                "name": "object has property",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "name",
                    },
                    "condition": {
                        "type": "HAS_PROPERTY",
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
                        SimpleNamespace(name="Alice"),
                        SimpleNamespace(name="Bob"),
                        SimpleNamespace(nananan="Charlie"),
                        EOF,
                    ],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [
                        SimpleNamespace(name="Alice"),
                        SimpleNamespace(name="Bob"),
                        EOF,
                    ],
                    "false": [SimpleNamespace(nananan="Charlie"), EOF],
                },
            },
            {
                "name": "length equal",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "number",
                        "value": 3,
                    },
                    "condition": {
                        "type": "LENGTH_EQUAL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": ["apple", "abc", "def", "banana", "ghi", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["abc", "def", "ghi", EOF],
                    "false": ["apple", "banana", EOF],
                },
            },
            {
                "name": "length not equal",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "number",
                        "value": 3,
                    },
                    "condition": {
                        "type": "LENGTH_NOT_EQUAL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": ["apple", "abc", "def", "banana", "ghi", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["apple", "banana", EOF],
                    "false": ["abc", "def", "ghi", EOF],
                },
            },
            {
                "name": "length greater than",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "number",
                        "value": 3,
                    },
                    "condition": {
                        "type": "LENGTH_GREATER_THAN",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": ["apple", "xy", "abc", "def", "banana", "ghi", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["apple", "banana", EOF],
                    "false": ["xy", "abc", "def", "ghi", EOF],
                },
            },
            {
                "name": "length less than",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "number",
                        "value": 3,
                    },
                    "condition": {
                        "type": "LENGTH_LESS_THAN",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": ["apple", "xy", "abc", "def", "banana", "wv", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["xy", "wv", EOF],
                    "false": ["apple", "abc", "def", "banana", EOF],
                },
            },
            {
                "name": "type equals static string",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "int",
                    },
                    "condition": {
                        "type": "TYPE_EQUALS",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [123, "abc", 456, "def", "ghi", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [123, 456, EOF],
                    "false": ["abc", "def", "ghi", EOF],
                },
            },
            {
                "name": "type equals dynamic comparison",
                "yml": {
                    "compareTo": {
                        "mode": "dynamic",
                    },
                    "condition": {
                        "type": "TYPE_EQUALS",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "value",
                    },
                },
                "inputs": {
                    "value": [123, "abc", 456, "def", "ghi", EOF],
                    "compareTo": ["int", "sstringg", 999, "str", 777, EOF],
                },
                "outputs": {
                    "true": [123, 456, "def", EOF],
                    "false": ["abc", "ghi", EOF],
                },
            },
            {
                "name": "expression is unsupported",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "EXPRESSION",
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
                    "true": [EOF],
                    "false": [EOF],
                },
                "raises": NotImplementedError,
            },
            {
                "name": "true value expression is unsupported",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "EQUAL",
                    },
                    "trueValue": {
                        "type": "expression",
                        "data": "this is not important",
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
                    "true": [EOF],
                    "false": ["Apple", "Banana", "apple", EOF],
                },
                "raises": NotImplementedError,
            },
            {
                "name": "false value expression is unsupported",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "EQUAL",
                    },
                    "trueValue": {
                        "type": "value",
                    },
                    "falseValue": {
                        "type": "expression",
                        "data": "this is not important",
                    },
                },
                "inputs": {
                    "value": ["Apple", "Banana", "apple", EOF],
                    "compareTo": [],
                },
                "outputs": {
                    "true": ["Apple", "Banana", "apple", EOF],
                    "false": [EOF],
                },
                "raises": NotImplementedError,
            },
            {
                "name": "property path not found",
                "yml": {
                    "propertyPath": "nananan",
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
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
                        SimpleNamespace(name="Alice"),
                        SimpleNamespace(name="Bob"),
                        EOF,
                    ],
                    "compareTo": [],
                },
                "outputs": {
                    "true": [EOF],
                    "false": [
                        SimpleNamespace(name="Alice"),
                        SimpleNamespace(name="Bob"),
                        EOF,
                    ],
                },
            },
            {
                "name": "unsupported condition type",
                "yml": {
                    "compareTo": {
                        "mode": "static",
                        "type": "string",
                        "value": "this is not important",
                    },
                    "condition": {
                        "type": "UNSUPPORTED",
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
            node = GetAttribute(
                macro_data={"key": test_case["key"]}, id="test_get_attribute"
            )
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

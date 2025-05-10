import unittest
from queue import Queue
from types import SimpleNamespace

from flyde.io import EOF, InputConfig, InputType
from flyde.stdlib import Conditional, GetAttribute, InlineValue, _ConditionConfig, _ConditionType


class TestInlineValue(unittest.TestCase):
    def test_inline_value(self):
        test_case = {
            "inputs": {},
            "outputs": {"value": "Hello"},
        }
        out_q = Queue()
        node = InlineValue(id="test_inline_value", config={"value": InputConfig(type=InputType.STRING, value="Hello")})
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
        node = InlineValue(id="test_inline_value", config={"value": InputConfig(type=InputType.STRING, value="Hello")})
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
                "config": {
                    "leftOperand": InputConfig(type=InputType.STRING, value="Apple"),
                    "rightOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "condition": _ConditionConfig(
                        type=_ConditionType.Equal,
                    ),
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
                "config": {
                    "leftOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "rightOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "condition": _ConditionConfig(
                        type=_ConditionType.NotEqual,
                    ),
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
                "config": {
                    "leftOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "rightOperand": InputConfig(type=InputType.STRING, value="Apple"),
                    "condition": _ConditionConfig(
                        type=_ConditionType.Contains,
                    ),
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
                "config": {
                    "leftOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "rightOperand": InputConfig(type=InputType.STRING, value="Apple"),
                    "condition": _ConditionConfig(
                        type=_ConditionType.NotContains,
                    ),
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
                "config": {
                    "leftOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "rightOperand": InputConfig(type=InputType.STRING, value="^[A-Z]"),
                    "condition": _ConditionConfig(
                        type=_ConditionType.RegexMatches,
                    ),
                },
                "inputs": {
                    "leftOperand": [
                        "Apple",
                        "banana",
                        "Grape",
                        "apple",
                        "2cherries",
                        EOF,
                    ],
                    "rightOperand": [],
                },
                "outputs": {
                    "true": ["Apple", "Grape", EOF],
                    "false": ["banana", "apple", "2cherries", EOF],
                },
            },
            {
                "name": "exists",
                "config": {
                    "leftOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "rightOperand": InputConfig(type=InputType.STRING, value="this is not important"),
                    "condition": _ConditionConfig(
                        type=_ConditionType.Exists,
                    ),
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
                "config": {
                    "leftOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "rightOperand": InputConfig(type=InputType.STRING, value="this is not important"),
                    "condition": _ConditionConfig(
                        type=_ConditionType.NotExists,
                    ),
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
                "config": {
                    "leftOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "rightOperand": InputConfig(
                        type=InputType.DYNAMIC,
                    ),
                    "condition": {"type": "UNSUPPORTED"},  # Will cause a ValueError in parse_config
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
                    node = Conditional(id="test_conditional", config=test_case["config"])
                continue

            node = Conditional(id="test_conditional", config=test_case["config"])
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
                "config": {
                    "key": InputConfig(
                        type=InputType.STRING,
                        value="name",
                    ),
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
                "config": {
                    "key": InputConfig(
                        type=InputType.STRING,
                        value="name",
                    ),
                },
                "inputs": {
                    "object": [
                        SimpleNamespace(name="Alice"),
                        SimpleNamespace(name="Bob"),
                        SimpleNamespace(nananan="Charlie"),
                        EOF,
                    ],
                    "key": ["name", EOF],
                },
                "outputs": ["Alice", "Bob", None, EOF],
            },
            {
                "name": "dynamic attribute from a dict",
                "config": {
                    "key": InputConfig(
                        type=InputType.DYNAMIC,
                        value=None,
                    ),
                },
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
                "name": "static attribute and non-object",
                "config": {
                    "key": InputConfig(
                        type=InputType.STRING,
                        value="name",
                    ),
                },
                "inputs": {
                    "object": [
                        {"name": "Alice"},
                        "bob",
                        123,
                        EOF,
                    ],
                    "key": ["name", EOF],
                },
                "outputs": ["Alice", None, None, EOF],
            },
            {
                "name": "nested attribute with dot key notation",
                "config": {
                    "key": InputConfig(
                        type=InputType.STRING,
                        value="address.city",
                    ),
                },
                "inputs": {
                    "object": [
                        {"name": "Alice", "address": {"city": "New York"}},
                        {"name": "Bob", "address": {"city": "Los Angeles"}},
                        {"nananan": "Charlie"},
                        EOF,
                    ],
                    "key": [],
                },
                "outputs": ["New York", "Los Angeles", None, EOF],
            },
            {
                "name": "nested 3 levels deep",
                "config": {
                    "key": InputConfig(
                        type=InputType.STRING,
                        value="address.city.zip",
                    ),
                },
                "inputs": {
                    "object": [
                        {"name": "Alice", "address": {"city": {"zip": 10001}}},
                        {"name": "Bob", "address": {"city": {"zip": 90001}}},
                        {"nananan": "Charlie"},
                        EOF,
                    ],
                    "key": [],
                },
                "outputs": [10001, 90001, None, EOF],
            },
        ]

        for test_case in test_cases:
            attr_q = Queue()
            out_q = Queue()
            config = test_case["config"]

            node = GetAttribute(id="test_get_attribute", config=config)
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

            node.stopped.wait()
            self.assertTrue(node.stopped.is_set())

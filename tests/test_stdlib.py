import unittest
from queue import Queue
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from urllib import error
from http import client

from flyde.io import EOF, InputConfig, InputType
from flyde.nodes import (
    Conditional,
    GetAttribute,
    Http,
    InlineValue,
    _ConditionConfig,
    _ConditionType,
)


class TestInlineValue(unittest.TestCase):
    def test_inline_value(self):
        test_case = {
            "inputs": {},
            "outputs": {"value": "Hello"},
        }
        out_q = Queue()
        node = InlineValue(
            id="test_inline_value",
            config={"value": InputConfig(type=InputType.STRING, value="Hello")},
        )
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
            id="test_inline_value",
            config={"value": InputConfig(type=InputType.STRING, value="Hello")},
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
                    "rightOperand": InputConfig(
                        type=InputType.STRING, value="this is not important"
                    ),
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
                    "rightOperand": InputConfig(
                        type=InputType.STRING, value="this is not important"
                    ),
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
                    "condition": {
                        "type": "UNSUPPORTED"
                    },  # Will cause a ValueError in parse_config
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
                    node = Conditional(
                        id="test_conditional", config=test_case["config"]
                    )
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
                if len(test_case["inputs"]["key"]) > 0 and i < len(
                    test_case["inputs"]["key"]
                ):
                    attr_q.put(test_case["inputs"]["key"][i])
                self.assertEqual(test_case["outputs"][i], out_q.get())

            node.stopped.wait()
            self.assertTrue(node.stopped.is_set())


class TestHttp(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_http_get(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.read.return_value = b'{"message": "Hello, World!"}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        test_case = {
            "name": "simple GET request",
            "config": {
                "method": InputConfig(type=InputType.STRING, value="GET"),
                "url": InputConfig(
                    type=InputType.STRING, value="https://example.com/api"
                ),
                "headers": InputConfig(
                    type=InputType.JSON, value={"User-Agent": "PyFlyde Test"}
                ),
                "params": InputConfig(type=InputType.JSON, value={"q": "test"}),
            },
        }

        data_q = Queue()

        node = Http(id="test_http", config=test_case["config"])
        node.outputs["data"].connect(data_q)

        node.process(
            url="https://example.com/api",
            method="GET",
            headers={"User-Agent": "PyFlyde Test"},
            params={"q": "test"},
        )

        self.assertEqual({"message": "Hello, World!"}, data_q.get_nowait())

        # Verify the mock was called with the expected arguments
        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        self.assertTrue("https://example.com/api?q=test" in str(args[0].full_url))
        self.assertEqual("GET", args[0].method)

        # Check that the User-Agent header was set
        user_agent = None
        for key, value in args[0].headers.items():
            if key.lower() == "user-agent":
                user_agent = value
                break
        self.assertEqual("PyFlyde Test", user_agent)

    @patch("urllib.request.urlopen")
    def test_http_html_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_response.read.return_value = (
            b"<!DOCTYPE html><html><body><h1>Test Page</h1></body></html>"
        )
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        data_q = Queue()

        node = Http(
            id="test_http",
            config={
                "method": InputConfig(type=InputType.STRING, value="GET"),
                "url": InputConfig(type=InputType.STRING, value="https://example.com"),
            },
        )
        node.outputs["data"].connect(data_q)

        node.process(url="https://example.com", method="GET")

        self.assertEqual(
            "<!DOCTYPE html><html><body><h1>Test Page</h1></body></html>",
            data_q.get_nowait(),
        )

        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        self.assertEqual("https://example.com", str(args[0].full_url))
        self.assertEqual("GET", args[0].method)

    @patch("urllib.request.urlopen")
    def test_http_binary_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/octet-stream"}
        binary_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"  # Start of a PNG file
        )
        mock_response.read.return_value = binary_data
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        data_q = Queue()

        node = Http(
            id="test_http",
            config={
                "method": InputConfig(type=InputType.STRING, value="GET"),
                "url": InputConfig(
                    type=InputType.STRING, value="https://example.com/image.png"
                ),
            },
        )
        node.outputs["data"].connect(data_q)

        node.process(url="https://example.com/image.png", method="GET")

        # Binary data should be returned as is
        self.assertEqual(binary_data, data_q.get_nowait())

        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        self.assertEqual("https://example.com/image.png", str(args[0].full_url))
        self.assertEqual("GET", args[0].method)

    @patch("urllib.request.urlopen")
    def test_http_non_utf8_encoding(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html; charset=ISO-8859-1"}
        # Latin-1 encoded text with special characters
        latin1_data = b"Espa\xf1ol Fran\xe7ais Portugu\xeas"
        mock_response.read.return_value = latin1_data
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        data_q = Queue()

        node = Http(
            id="test_http",
            config={
                "method": InputConfig(type=InputType.STRING, value="GET"),
                "url": InputConfig(
                    type=InputType.STRING, value="https://example.com/latin1.html"
                ),
            },
        )
        node.outputs["data"].connect(data_q)

        node.process(url="https://example.com/latin1.html", method="GET")

        # Should be properly decoded using ISO-8859-1 charset
        self.assertEqual("Español Français Português", data_q.get_nowait())

        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        self.assertEqual("https://example.com/latin1.html", str(args[0].full_url))
        self.assertEqual("GET", args[0].method)

    @patch("urllib.request.urlopen")
    def test_http_post(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.read.return_value = b'{"id": 1, "success": true}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        test_case = {
            "name": "POST request with data",
            "config": {
                "method": InputConfig(type=InputType.STRING, value="POST"),
                "url": InputConfig(
                    type=InputType.STRING, value="https://example.com/api/users"
                ),
                "headers": InputConfig(
                    type=InputType.JSON, value={"User-Agent": "PyFlyde Test"}
                ),
                "data": InputConfig(
                    type=InputType.JSON,
                    value={"name": "Test User", "email": "test@example.com"},
                ),
            },
        }

        data_q = Queue()

        node = Http(id="test_http", config=test_case["config"])
        node.outputs["data"].connect(data_q)

        node.process(
            url="https://example.com/api/users",
            method="POST",
            headers={"User-Agent": "PyFlyde Test"},
            data={"name": "Test User", "email": "test@example.com"},
        )

        self.assertEqual({"id": 1, "success": True}, data_q.get_nowait())

        # Verify the mock was called with the expected arguments
        mock_urlopen.assert_called_once()
        args, kwargs = mock_urlopen.call_args
        self.assertEqual("https://example.com/api/users", str(args[0].full_url))
        self.assertEqual("POST", args[0].method)

        # Check that the User-Agent header was set
        user_agent = None
        for key, value in args[0].headers.items():
            if key.lower() == "user-agent":
                user_agent = value
                break
        self.assertEqual("PyFlyde Test", user_agent)

        self.assertEqual(
            b'{"name": "Test User", "email": "test@example.com"}', kwargs["data"]
        )

    @patch("urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        # Create a mock headers object for HTTPError
        headers = client.HTTPMessage()
        headers.add_header("Content-Type", "text/plain")

        mock_urlopen.side_effect = error.HTTPError(
            url="https://example.com/api/error",
            code=404,
            msg="Not Found",
            hdrs=headers,
            fp=None,
        )

        test_case = {
            "name": "HTTP error handling",
            "config": {
                "method": InputConfig(type=InputType.STRING, value="GET"),
                "url": InputConfig(
                    type=InputType.STRING, value="https://example.com/api/error"
                ),
            },
        }

        data_q = Queue()

        node = Http(id="test_http", config=test_case["config"])
        node.outputs["data"].connect(data_q)

        with self.assertRaises(error.HTTPError) as context:
            node.process(url="https://example.com/api/error", method="GET")

        self.assertEqual(404, context.exception.code)
        self.assertEqual("Not Found", context.exception.msg)

        # Verify the mock was called
        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        self.assertEqual("https://example.com/api/error", str(args[0].full_url))

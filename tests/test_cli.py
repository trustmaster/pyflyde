import json
import os
import tempfile
import unittest
from unittest.mock import patch

from flyde.cli import (
    collect_components_from_directory,
    convert_class_name_to_display_name,
    gen_json,
    generate_node_json,
    is_stdlib_node,
)
from flyde.io import Input, Output
from flyde.node import Component


class TestCLIHelpers(unittest.TestCase):
    def test_convert_class_name_to_display_name(self):
        test_cases = [
            ("MyCustomNode", "My Custom Node"),
            ("HTTPClient", "HTTPClient"),  # Adjacent capitals stay together
            ("XMLParser", "XMLParser"),
            ("SimpleNode", "Simple Node"),
            ("Node", "Node"),  # Single word
            ("MyHTTPClient", "My HTTPClient"),
            ("CustomBob", "Custom Bob"),
            ("CustomAlice", "Custom Alice"),
        ]

        for class_name, expected in test_cases:
            with self.subTest(class_name=class_name):
                result = convert_class_name_to_display_name(class_name)
                self.assertEqual(result, expected)

    def test_is_stdlib_node(self):
        from flyde.node import SUPPORTED_MACROS

        # Test that all supported macros are detected as stdlib nodes
        for macro in SUPPORTED_MACROS:
            with self.subTest(node_name=macro):
                result = is_stdlib_node(macro)
                self.assertTrue(result)

        # Test that custom nodes are not detected as stdlib nodes
        custom_nodes = ["CustomNode", "MyComponent", "Echo", "Format"]
        for node_name in custom_nodes:
            with self.subTest(node_name=node_name):
                result = is_stdlib_node(node_name)
                self.assertFalse(result)


class TestCustomComponent(Component):
    """A test component for unit testing."""

    inputs = {
        "input1": Input(description="First test input"),
        "input2": Input(description="Second test input"),
    }
    outputs = {
        "output": Output(description="Test output"),
    }

    def process(self, input1, input2):
        return {"output": f"{input1}-{input2}"}


class CustomBob(Component):
    """A custom external node named Bob"""

    inputs = {
        "value": Input(description="Input value to process"),
    }
    outputs = {
        "result": Output(description="Processed result from external runtime"),
    }

    def process(self, value):
        return {"result": f"Bob processed: {value}"}


class InlineValue(Component):
    """This overrides the standard InlineValue node"""

    outputs = {
        "value": Output(description="The overridden value"),
    }

    def process(self):
        return {"value": "overridden"}


class TestGenerateNodeJson(unittest.TestCase):
    def test_generate_custom_node_json(self):
        result = generate_node_json("CustomBob", CustomBob, "test_components.py")

        expected = {
            "id": "CustomBob",
            "type": "code",
            "displayName": "Custom Bob",
            "description": "A custom external node named Bob",
            "icon": "fa-solid fa-user",
            "source": {"type": "custom", "data": "custom://test_components.py/CustomBob"},
            "editorNode": {
                "id": "CustomBob",
                "displayName": "Custom Bob",
                "description": "A custom external node named Bob",
                "icon": "fa-solid fa-user",
                "inputs": {"value": {"description": "Input value to process"}},
                "outputs": {"result": {"description": "Processed result from external runtime"}},
                "editorConfig": {"type": "structured"},
            },
            "config": {},
        }

        self.assertEqual(result, expected)

    def test_generate_stdlib_override_json(self):
        result = generate_node_json("InlineValue", InlineValue, "test_components.py")

        expected = {
            "id": "InlineValue",
            "type": "code",
            "displayName": "Overridden Inline Value",
            "description": "This overrides the standard InlineValue node",
            "source": {"type": "package", "data": "@flyde/nodes"},
            "editorNode": {
                "id": "InlineValue",
                "displayName": "Overridden Inline Value",
                "description": "This overrides the standard InlineValue node",
                "inputs": {},
                "outputs": {"value": {"description": "The overridden value"}},
                "editorConfig": {"type": "structured"},
            },
            "config": {},
        }

        self.assertEqual(result, expected)

    def test_generate_node_with_no_docstring(self):
        class NodeWithoutDoc(Component):
            inputs = {"inp": Input(description="Input")}
            outputs = {"out": Output(description="Output")}

        result = generate_node_json("NodeWithoutDoc", NodeWithoutDoc, "test.py")

        self.assertEqual(result["description"], "")
        self.assertEqual(result["editorNode"]["description"], "")

    def test_generate_node_with_no_inputs_outputs(self):
        class EmptyNode(Component):
            """An empty node"""

        result = generate_node_json("EmptyNode", EmptyNode, "test.py")

        self.assertEqual(result["editorNode"]["inputs"], {})
        self.assertEqual(result["editorNode"]["outputs"], {})


class TestCollectComponents(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_collect_components_from_directory(self):
        # Create test Python files
        test_component_py = '''
from flyde.io import Input, Output
from flyde.node import Component

class TestNode1(Component):
    """First test node"""
    inputs = {"inp": Input(description="Input")}
    outputs = {"out": Output(description="Output")}

class TestNode2(Component):
    """Second test node"""
    inputs = {"data": Input(description="Data input")}
    outputs = {"result": Output(description="Result output")}

# This should be ignored
class NotAComponent:
    pass
'''

        another_component_py = '''
from flyde.io import Input, Output
from flyde.node import Component

class AnotherNode(Component):
    """Another test node"""
    outputs = {"value": Output(description="Value output")}
'''

        # Write test files
        with open(os.path.join(self.temp_dir, "test_components.py"), "w") as f:
            f.write(test_component_py)

        with open(os.path.join(self.temp_dir, "another.py"), "w") as f:
            f.write(another_component_py)

        # Create __init__.py (should be ignored)
        with open(os.path.join(self.temp_dir, "__init__.py"), "w") as f:
            f.write("# This should be ignored")

        # Collect components
        components = collect_components_from_directory(self.temp_dir)

        # Should find 3 components
        self.assertEqual(len(components), 3)
        self.assertIn("TestNode1", components)
        self.assertIn("TestNode2", components)
        self.assertIn("AnotherNode", components)

        # Check that components are actually Component subclasses
        for name, component_info in components.items():
            self.assertTrue(issubclass(component_info["class"], Component))
            self.assertIn("file_path", component_info)

    def test_collect_components_invalid_syntax(self):
        # Create a file with invalid Python syntax
        invalid_py = """
This is not valid Python syntax!
class InvalidNode(Component:
    pass
"""

        with open(os.path.join(self.temp_dir, "invalid.py"), "w") as f:
            f.write(invalid_py)

        # Should handle the error gracefully
        components = collect_components_from_directory(self.temp_dir)
        self.assertEqual(len(components), 0)

    def test_collect_components_empty_directory(self):
        # Test with empty directory
        components = collect_components_from_directory(self.temp_dir)
        self.assertEqual(len(components), 0)


class TestGenJson(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_gen_json_with_mixed_components(self):
        # Create test files with both custom and stdlib override components
        components_py = '''
from flyde.io import Input, Output
from flyde.node import Component

class CustomBob(Component):
    """A custom external node named Bob"""
    inputs = {"value": Input(description="Input value to process")}
    outputs = {"result": Output(description="Processed result from external runtime")}

class CustomAlice(Component):
    """Another custom external node"""
    inputs = {
        "input1": Input(description="First input"),
        "input2": Input(description="Second input")
    }
    outputs = {"output": Output(description="Combined output")}

class InlineValue(Component):
    """This overrides the standard InlineValue node"""
    outputs = {"value": Output(description="The overridden value")}
'''

        with open(os.path.join(self.temp_dir, "components.py"), "w") as f:
            f.write(components_py)

        # Generate JSON
        gen_json(self.temp_dir)

        # Check that the file was created
        output_file = os.path.join(self.temp_dir, ".flyde-nodes.json")
        self.assertTrue(os.path.exists(output_file))

        # Load and verify the JSON content
        with open(output_file, "r") as f:
            data = json.load(f)

        # Check structure
        self.assertIn("nodes", data)
        self.assertIn("groups", data)

        # Check nodes
        nodes = data["nodes"]
        self.assertEqual(len(nodes), 3)
        self.assertIn("CustomBob", nodes)
        self.assertIn("CustomAlice", nodes)
        self.assertIn("InlineValue", nodes)

        # Check CustomBob
        bob = nodes["CustomBob"]
        self.assertEqual(bob["id"], "CustomBob")
        self.assertEqual(bob["displayName"], "Custom Bob")
        self.assertEqual(bob["source"]["type"], "custom")
        self.assertEqual(bob["source"]["data"], "custom://components.py/CustomBob")
        self.assertIn("icon", bob)

        # Check InlineValue (stdlib override)
        inline = nodes["InlineValue"]
        self.assertEqual(inline["id"], "InlineValue")
        self.assertEqual(inline["displayName"], "Overridden Inline Value")
        self.assertEqual(inline["source"]["type"], "package")
        self.assertEqual(inline["source"]["data"], "@flyde/nodes")
        self.assertNotIn("icon", inline)

        # Check groups
        groups = data["groups"]
        self.assertEqual(len(groups), 2)

        # Find groups by title
        custom_group = next(g for g in groups if g["title"] == "Custom Runtime Nodes")
        stdlib_group = next(g for g in groups if g["title"] == "Overridden Stdlib")

        self.assertCountEqual(custom_group["nodeIds"], ["CustomBob", "CustomAlice"])
        self.assertCountEqual(stdlib_group["nodeIds"], ["InlineValue"])

        # Check CustomAlice has correct path format
        alice = nodes["CustomAlice"]
        self.assertEqual(alice["source"]["type"], "custom")
        self.assertEqual(alice["source"]["data"], "custom://components.py/CustomAlice")

    def test_gen_json_empty_directory(self):
        # Test with directory containing no components
        empty_py = """
# This file has no Component subclasses
def some_function():
    pass

class NotAComponent:
    pass
"""

        with open(os.path.join(self.temp_dir, "empty.py"), "w") as f:
            f.write(empty_py)

        # Capture stdout to verify the message
        with patch("builtins.print") as mock_print:
            gen_json(self.temp_dir)
            mock_print.assert_any_call(f"No Component subclasses found in directory {self.temp_dir}")

        # Should not create the JSON file
        output_file = os.path.join(self.temp_dir, ".flyde-nodes.json")
        self.assertFalse(os.path.exists(output_file))

    def test_gen_json_only_custom_nodes(self):
        # Test with only custom nodes (no stdlib overrides)
        components_py = '''
from flyde.io import Input, Output
from flyde.node import Component

class CustomNode1(Component):
    """First custom node"""
    inputs = {"inp": Input(description="Input")}
    outputs = {"out": Output(description="Output")}

class CustomNode2(Component):
    """Second custom node"""
    outputs = {"result": Output(description="Result")}
'''

        with open(os.path.join(self.temp_dir, "components.py"), "w") as f:
            f.write(components_py)

        gen_json(self.temp_dir)

        output_file = os.path.join(self.temp_dir, ".flyde-nodes.json")
        with open(output_file, "r") as f:
            data = json.load(f)

        # Should have one group for custom nodes only
        groups = data["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["title"], "Custom Runtime Nodes")
        self.assertCountEqual(groups[0]["nodeIds"], ["CustomNode1", "CustomNode2"])

        # Check that custom nodes have correct path format
        for node_name in ["CustomNode1", "CustomNode2"]:
            node = data["nodes"][node_name]
            self.assertEqual(node["source"]["type"], "custom")
            self.assertEqual(node["source"]["data"], f"custom://components.py/{node_name}")

        # Ensure no stdlib overrides group exists
        for group in groups:
            self.assertNotEqual(group["title"], "Overridden Stdlib")

    def test_gen_json_only_stdlib_overrides(self):
        # Test with only stdlib override nodes
        components_py = '''
from flyde.io import Input, Output
from flyde.node import Component

class InlineValue(Component):
    """Override InlineValue"""
    outputs = {"value": Output(description="Value")}

class Conditional(Component):
    """Override Conditional"""
    inputs = {"condition": Input(description="Condition")}
    outputs = {"result": Output(description="Result")}
'''

        with open(os.path.join(self.temp_dir, "components.py"), "w") as f:
            f.write(components_py)

        gen_json(self.temp_dir)

        output_file = os.path.join(self.temp_dir, ".flyde-nodes.json")
        with open(output_file, "r") as f:
            data = json.load(f)

        # Should have one group for stdlib overrides only
        groups = data["groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["title"], "Overridden Stdlib")
        self.assertCountEqual(groups[0]["nodeIds"], ["InlineValue", "Conditional"])

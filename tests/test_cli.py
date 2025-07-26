import json
import os
import shutil
import tempfile
import unittest

from flyde.cli import (
    collect_components_from_directory,
    collect_flyde_nodes_from_directory,
    convert_class_name_to_display_name,
    gen_json,
    generate_flyde_node_json,
    generate_node_json,
    is_stdlib_node,
)
from flyde.io import Input, Output
from flyde.node import SUPPORTED_MACROS, Component


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
            "icon": "fa-brands fa-python",
            "source": {
                "type": "custom",
                "data": "custom://test_components.py/CustomBob",
            },
            "editorNode": {
                "id": "CustomBob",
                "displayName": "Custom Bob",
                "description": "A custom external node named Bob",
                "inputs": {"value": {"description": "Input value to process"}},
                "outputs": {"result": {"description": "Processed result from external runtime"}},
                "editorConfig": {"type": "structured"},
            },
            "config": {},
        }

        self.assertEqual(result, expected)

    def test_generate_stdlib_node_json(self):
        result = generate_node_json("InlineValue", InlineValue, "test_components.py")
        expected = "@flyde/nodes"
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


class TestCollectFlydeNodes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_collect_flyde_nodes_from_directory(self):
        # Use existing test files from the tests directory
        test_files_dir = os.path.join(os.path.dirname(__file__), "..")
        flyde_nodes = collect_flyde_nodes_from_directory(os.path.join(test_files_dir, "tests"))

        # Should find several .flyde nodes
        self.assertGreater(len(flyde_nodes), 0)
        self.assertIn("TestNestedFlow", flyde_nodes)
        self.assertIn("Repeat3Times", flyde_nodes)

        # Check TestNestedFlow structure (uses filename as ID)
        nested_flow = flyde_nodes["TestNestedFlow"]
        self.assertEqual(nested_flow["type"], "flyde")
        self.assertEqual(nested_flow["description"], "Repeats input 3xN times")
        self.assertIn("file_path", nested_flow)
        self.assertEqual(len(nested_flow["inputs"]), 2)
        self.assertEqual(len(nested_flow["outputs"]), 1)
        self.assertEqual(nested_flow["inputs"]["inp"]["mode"], "required")
        self.assertEqual(nested_flow["inputs"]["n"]["mode"], "required")

        # Check Repeat3Times structure
        repeat_flow = flyde_nodes["Repeat3Times"]
        self.assertEqual(repeat_flow["type"], "flyde")
        self.assertIn("For each input string", repeat_flow["description"])
        self.assertEqual(len(repeat_flow["inputs"]), 1)
        self.assertEqual(len(repeat_flow["outputs"]), 1)

    def test_collect_flyde_nodes_invalid_yaml(self):
        # Create a file with invalid YAML syntax
        invalid_flyde = """
This is not valid YAML syntax!
node:
  inputs:
    - invalid structure
"""

        with open(os.path.join(self.temp_dir, "invalid.flyde"), "w") as f:
            f.write(invalid_flyde)

        # Should handle the error gracefully
        flyde_nodes = collect_flyde_nodes_from_directory(self.temp_dir)
        self.assertEqual(len(flyde_nodes), 0)

    def test_collect_flyde_nodes_empty_directory(self):
        # Test with empty directory
        flyde_nodes = collect_flyde_nodes_from_directory(self.temp_dir)
        self.assertEqual(len(flyde_nodes), 0)

    def test_collect_flyde_nodes_uses_filename_as_id(self):
        # Test that node ID always comes from filename, not YAML id field
        test_flyde = """imports: {}
node:
  instances: []
  connections: []
  id: DummyExample
  inputs:
    inp:
      mode: required
  outputs:
    out:
      delayed: false
  inputsPosition: {}
  outputsPosition: {}
description: Test that uses filename for ID
"""

        with open(os.path.join(self.temp_dir, "ActualNodeName.flyde"), "w") as f:
            f.write(test_flyde)

        flyde_nodes = collect_flyde_nodes_from_directory(self.temp_dir)
        self.assertEqual(len(flyde_nodes), 1)
        # Should use filename, not the "DummyExample" from YAML
        self.assertIn("ActualNodeName", flyde_nodes)
        self.assertNotIn("DummyExample", flyde_nodes)

    def test_collect_flyde_nodes_description_priority(self):
        # Test that node.description takes priority over root description
        test_flyde_node_desc = """imports: {}
node:
  instances: []
  connections: []
  inputs:
    inp:
      mode: required
  outputs:
    out:
      delayed: false
  inputsPosition: {}
  outputsPosition: {}
  description: Node level description
description: Root level description
"""

        with open(os.path.join(self.temp_dir, "TestPriority.flyde"), "w") as f:
            f.write(test_flyde_node_desc)

        flyde_nodes = collect_flyde_nodes_from_directory(self.temp_dir)
        self.assertEqual(len(flyde_nodes), 1)
        self.assertIn("TestPriority", flyde_nodes)
        # Should prefer node.description over root description
        self.assertEqual(flyde_nodes["TestPriority"]["description"], "Node level description")


class TestGenerateFlydeNodeJson(unittest.TestCase):
    def test_generate_flyde_node_json(self):
        self.maxDiff = None
        flyde_info = {
            "file_path": "test_flows/TestFlow.flyde",
            "description": "A test flow for unit testing",
            "inputs": {"input1": {"mode": "required"}, "input2": {"mode": "optional"}},
            "outputs": {"output1": {}, "output2": {}},
            "type": "flyde",
        }

        result = generate_flyde_node_json("TestFlow", flyde_info)

        expected = {
            "id": "TestFlow",
            "type": "visual",
            "displayName": "Test Flow",
            "description": "A test flow for unit testing",
            "icon": "fa-diagram-project",
            "source": {"type": "file", "data": "test_flows/TestFlow.flyde"},
            "editorNode": {
                "id": "TestFlow",
                "displayName": "Test Flow",
                "description": "A test flow for unit testing",
                "inputs": {
                    "input1": {"description": "input1 input (required)"},
                    "input2": {"description": "input2 input"},
                },
                "outputs": {
                    "output1": {"description": "output1 output"},
                    "output2": {"description": "output2 output"},
                },
                "editorConfig": {"type": "structured"},
            },
            "config": {},
        }

        self.assertEqual(result, expected)

    def test_generate_flyde_node_with_no_inputs_outputs(self):
        flyde_info = {
            "file_path": "EmptyFlow.flyde",
            "description": "An empty flow",
            "inputs": {},
            "outputs": {},
            "type": "flyde",
        }

        result = generate_flyde_node_json("EmptyFlow", flyde_info)

        self.assertEqual(result["editorNode"]["inputs"], {})
        self.assertEqual(result["editorNode"]["outputs"], {})


class TestGenJson(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_gen_json_with_mixed_components(self):
        # Create test files with both custom and stdlib components, but do not override stdlib nodes
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
'''

        with open(os.path.join(self.temp_dir, "components.py"), "w") as f:
            f.write(components_py)

        # Generate JSON
        gen_json(self.temp_dir)

        # Check that the file was created
        output_file = os.path.join(self.temp_dir, "flyde-nodes.json")
        self.assertTrue(os.path.exists(output_file))

        # Load and verify the JSON content
        with open(output_file, "r") as f:
            data = json.load(f)

        # Check structure
        self.assertIn("nodes", data)
        self.assertIn("groups", data)

        # Check nodes
        nodes = data["nodes"]
        # Should have all custom nodes plus all stdlib nodes
        expected_nodes = set(["CustomBob", "CustomAlice"] + list(SUPPORTED_MACROS))
        self.assertEqual(set(nodes.keys()), expected_nodes)
        self.assertIn("CustomBob", nodes)
        self.assertIn("CustomAlice", nodes)
        for stdlib_node in SUPPORTED_MACROS:
            self.assertIn(stdlib_node, nodes)

        # Check CustomBob
        bob = nodes["CustomBob"]
        self.assertEqual(bob["id"], "CustomBob")
        self.assertEqual(bob["displayName"], "Custom Bob")
        self.assertEqual(bob["source"]["type"], "custom")
        self.assertEqual(bob["source"]["data"], "custom://components.py/CustomBob")
        self.assertIn("icon", bob)

        # Check groups
        groups = data["groups"]
        self.assertEqual(len(groups), 2)

        # Find groups by title
        custom_group = next((g for g in groups if g["title"] == "Your PyFlyde Nodes"), None)
        stdlib_group = next((g for g in groups if g["title"] == "PyFlyde Standard Nodes"), None)

        self.assertIsNotNone(custom_group)
        self.assertIsNotNone(stdlib_group)
        if custom_group is None or stdlib_group is None:
            return
        self.assertCountEqual(custom_group["nodeIds"], ["CustomBob", "CustomAlice"])
        self.assertCountEqual(stdlib_group["nodeIds"], list(SUPPORTED_MACROS))

    def test_gen_json_with_flyde_files(self):
        # Create test files with both .py components and copy an existing .flyde file
        components_py = '''
from flyde.io import Input, Output
from flyde.node import Component

class CustomNode(Component):
    """A custom Python node"""
    inputs = {"value": Input(description="Input value")}
    outputs = {"result": Output(description="Result value")}
'''

        with open(os.path.join(self.temp_dir, "components.py"), "w") as f:
            f.write(components_py)

        # Copy an existing .flyde file
        test_flyde_source = os.path.join(os.path.dirname(__file__), "..", "tests", "Repeat3Times.flyde")
        test_flyde_dest = os.path.join(self.temp_dir, "TestFlow.flyde")
        shutil.copy(test_flyde_source, test_flyde_dest)

        # Generate JSON
        gen_json(self.temp_dir)

        # Check that the file was created
        output_file = os.path.join(self.temp_dir, "flyde-nodes.json")
        self.assertTrue(os.path.exists(output_file))

        # Load and verify the JSON content
        with open(output_file, "r") as f:
            data = json.load(f)

        # Check structure
        self.assertIn("nodes", data)
        self.assertIn("groups", data)

        # Check nodes - should have both Python and .flyde nodes
        nodes = data["nodes"]
        expected_custom_nodes = set(["CustomNode", "TestFlow"] + list(SUPPORTED_MACROS))
        self.assertEqual(set(nodes.keys()), expected_custom_nodes)

        # Check CustomNode (Python)
        custom_node = nodes["CustomNode"]
        self.assertEqual(custom_node["type"], "code")
        self.assertEqual(custom_node["source"]["type"], "custom")

        # Check TestFlow (.flyde) - uses filename as ID
        test_flow = nodes["TestFlow"]
        self.assertEqual(test_flow["id"], "TestFlow")
        self.assertEqual(test_flow["type"], "visual")
        self.assertEqual(test_flow["displayName"], "Test Flow")
        self.assertEqual(test_flow["icon"], "fa-diagram-project")
        self.assertEqual(test_flow["source"]["type"], "file")
        self.assertEqual(test_flow["source"]["data"], "TestFlow.flyde")

        # Check groups
        groups = data["groups"]
        custom_group = next((g for g in groups if g["title"] == "Your PyFlyde Nodes"), None)
        self.assertIsNotNone(custom_group)
        if custom_group is not None:
            self.assertIn("CustomNode", custom_group["nodeIds"])
            self.assertIn("TestFlow", custom_group["nodeIds"])

    def test_gen_json_only_flyde_files(self):
        # Test with only .flyde files (no Python components) using existing files
        test_flyde_source_1 = os.path.join(os.path.dirname(__file__), "..", "tests", "Repeat3Times.flyde")
        test_flyde_source_2 = os.path.join(os.path.dirname(__file__), "..", "tests", "TestNestedFlow.flyde")

        shutil.copy(test_flyde_source_1, os.path.join(self.temp_dir, "Flow1.flyde"))
        shutil.copy(test_flyde_source_2, os.path.join(self.temp_dir, "Flow2.flyde"))

        gen_json(self.temp_dir)

        output_file = os.path.join(self.temp_dir, "flyde-nodes.json")
        with open(output_file, "r") as f:
            data = json.load(f)

        # Should have .flyde nodes and stdlib nodes
        nodes = data["nodes"]
        expected_nodes = set(["Flow1", "Flow2"] + list(SUPPORTED_MACROS))
        self.assertEqual(set(nodes.keys()), expected_nodes)

        # Check that .flyde nodes are in the custom group
        groups = data["groups"]
        custom_group = next((g for g in groups if g["title"] == "Your PyFlyde Nodes"), None)
        self.assertIsNotNone(custom_group)
        if custom_group is not None:
            self.assertIn("Flow1", custom_group["nodeIds"])
            self.assertIn("Flow2", custom_group["nodeIds"])

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

        # Generate JSON
        gen_json(self.temp_dir)

        # Should create the JSON file with only stdlib nodes if any exist
        output_file = os.path.join(self.temp_dir, "flyde-nodes.json")
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, "r") as f:
            data = json.load(f)
        self.assertIn("nodes", data)
        self.assertIn("groups", data)
        # At least one stdlib node should be present if stdlib is available
        stdlib_group = next((g for g in data["groups"] if g["title"] == "PyFlyde Standard Nodes"), None)
        self.assertIsNotNone(stdlib_group)
        if stdlib_group is None:
            return
        self.assertGreater(len(stdlib_group["nodeIds"]), 0)

    def test_gen_json_only_custom_nodes(self):
        # Test with only custom nodes (no stdlib nodes in this directory)
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

        output_file = os.path.join(self.temp_dir, "flyde-nodes.json")
        with open(output_file, "r") as f:
            data = json.load(f)

        # Should have at least the custom nodes group
        groups = data["groups"]
        custom_group = next((g for g in groups if g["title"] == "Your PyFlyde Nodes"), None)
        self.assertIsNotNone(custom_group)
        if custom_group is None:
            return
        self.assertCountEqual(custom_group["nodeIds"], ["CustomNode1", "CustomNode2"])

    def test_gen_json_only_stdlib_nodes(self):
        # Test with only stdlib nodes
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

        output_file = os.path.join(self.temp_dir, "flyde-nodes.json")
        with open(output_file, "r") as f:
            data = json.load(f)

        # Should have stdlib group
        groups = data["groups"]
        stdlib_group = next((g for g in groups if g["title"] == "PyFlyde Standard Nodes"), None)
        self.assertIsNotNone(stdlib_group)
        if stdlib_group is None:
            return
        self.assertCountEqual(stdlib_group["nodeIds"], list(SUPPORTED_MACROS))

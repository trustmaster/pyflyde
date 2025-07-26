import unittest
from queue import Queue

from flyde.flow import Flow
from flyde.io import EOF


class TestIsolatedFlow(unittest.TestCase):
    def test_flow(self):
        flow = Flow.from_file("tests/TestIsolatedFlow.flyde")
        flow.run()
        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())


class TestInOutFlow(unittest.TestCase):
    def test_flow(self):
        test_case = {
            "inputs": ["Hello", "World", "", EOF],
            "outputs": ["Hello", "World", "ERR: msg is empty", EOF],
        }
        flow = Flow.from_file("tests/TestInOutFlow.flyde")

        in_q = flow.node.inputs["inMsg"].queue
        out_q = Queue()
        flow.node.outputs["outMsg"].connect(out_q)

        flow.run()

        for inp, out in zip(test_case["inputs"], test_case["outputs"]):
            in_q.put(inp)
            self.assertEqual(out, out_q.get())

        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())


class TestNestedFlow(unittest.TestCase):
    def test_flow(self):
        test_case = {
            "inputs": {
                "inp": ["Hello", "World", "!", EOF],
                "n": [1, 2, EOF],
            },
            "outputs": [
                "HELLOHELLOHELLO",
                "WORLDWORLDWORLDWORLDWORLDWORLD",
                "!!!!!!",
                EOF,
            ],
        }
        flow = Flow.from_file("tests/TestNestedFlow.flyde")

        inp_q = flow.node.inputs["inp"].queue
        n_q = flow.node.inputs["n"].queue
        out_q = Queue()
        flow.node.outputs["out"].connect(out_q)

        flow.run()

        for i, inp in enumerate(test_case["inputs"]["inp"]):
            inp_q.put(inp)
            if i < len(test_case["inputs"]["n"]):
                n_q.put(test_case["inputs"]["n"][i])
            out = out_q.get()
            self.assertEqual(test_case["outputs"][i], out)

        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())


class TestFanInFlow(unittest.TestCase):
    def test_with_component(self):
        test_case = {
            "inputs": ["John", EOF],
            "outputs": ["John", "JOHN", "Hello, John!", EOF],
        }
        flow = Flow.from_file("tests/TestFanIn.flyde")

        in_q = flow.node.inputs["str"].queue
        out_q = Queue()
        flow.node.outputs["out"].connect(out_q)

        flow.run()

        for inp in test_case["inputs"]:
            in_q.put(inp)

        # Get all outputs until EOF
        output_list = []
        count = 0
        limit = len(test_case["outputs"])
        out = None
        while count < limit and out != EOF:
            out = out_q.get()
            output_list.append(out)
            count += 1

        # Compare expected and actual lists ignoring the order of elements
        self.assertCountEqual(test_case["outputs"], output_list)
        # EOF must be the last output
        self.assertEqual(EOF, output_list[-1])

        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())


class TestCustomLoadFlow(unittest.TestCase):
    def test_custom_component_loading(self):
        """Test loading components using custom:// source format."""
        test_case = {
            "inputs": ["hello", "world", EOF],
            "outputs": ["HELLO", "WORLD", EOF],
        }
        flow = Flow.from_file("tests/TestCustomLoad.flyde")

        in_q = flow.node.inputs["input"].queue
        out_q = Queue()
        flow.node.outputs["output"].connect(out_q)

        flow.run()

        for inp, expected_out in zip(test_case["inputs"], test_case["outputs"]):
            in_q.put(inp)
            if expected_out == EOF:
                actual_out = out_q.get()
                self.assertEqual(EOF, actual_out)
            else:
                actual_out = out_q.get()
                self.assertEqual(expected_out, actual_out)

        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())

    def test_custom_component_loading_edge_cases(self):
        """Test edge cases in custom component loading."""
        from flyde.flow import Flow
        from flyde.node import InstanceArgs, InstanceSource, InstanceSourceType

        flow = Flow({})

        # Test malformed custom path (no class name)
        args = InstanceArgs(
            id="test",
            display_name="Test",
            stopped=None,
            config={},
            source=InstanceSource(type=InstanceSourceType.CUSTOM, data="custom://tests/components.py/"),
        )
        with self.assertRaises(Exception):
            flow.create_component("Echo", args)

        # Test invalid module path
        args = InstanceArgs(
            id="test",
            display_name="Test",
            stopped=None,
            config={},
            source=InstanceSource(
                type=InstanceSourceType.CUSTOM,
                data="custom://tests/nonexistent.py/Echo",
            ),
        )
        with self.assertRaises(Exception):
            flow.create_component("Echo", args)

        # Test valid custom path
        args = InstanceArgs(
            id="test",
            display_name="Test",
            stopped=None,
            config={},
            source=InstanceSource(type=InstanceSourceType.CUSTOM, data="custom://tests/components.py/Echo"),
        )
        component = flow.create_component("Echo", args)
        self.assertIsNotNone(component)

    def test_with_graph(self):
        test_case = {
            "inputs": ["John", EOF],
            "outputs": [
                "JOHNJOHNJOHN",
                "JOHNJOHNJOHN",
                "HELLO, JOHN!HELLO, JOHN!HELLO, JOHN!",
                EOF,
            ],
        }
        flow = Flow.from_file("tests/TestFanInGraph.flyde")

        in_q = flow.node.inputs["str"].queue
        out_q = Queue()
        flow.node.outputs["out"].connect(out_q)

        flow.run()

        for inp in test_case["inputs"]:
            in_q.put(inp)

        # Get all outputs until EOF
        output_list = []
        count = 0
        limit = len(test_case["outputs"])
        out = None
        while count < limit and out != EOF:
            out = out_q.get()
            output_list.append(out)
            count += 1

        # Compare expected and actual lists ignoring the order of elements
        self.assertCountEqual(test_case["outputs"], output_list)
        # EOF must be the last output
        self.assertEqual(EOF, output_list[-1])

        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())

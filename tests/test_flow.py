import unittest
from flyde.io import EOF
from flyde.flow import FlydeFlow


class TestIsolatedFlow(unittest.TestCase):
    def test_flow(self):
        flow = FlydeFlow.from_file("tests/TestIsolatedFlow.flyde")
        flow.run()
        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())


class TestInOutFlow(unittest.TestCase):
    def test_flow(self):
        test_case = {
            "inputs": ["Hello", "World", EOF],
            "outputs": ["Hello", "World", EOF],
        }
        flow = FlydeFlow.from_file("tests/TestInOutFlow.flyde")

        inQ = flow.node.inputs["inMsg"].queue
        outQ = flow.node.outputs["outMsg"].queue

        flow.run()

        print("Running test case")
        for inp, out in zip(test_case["inputs"], test_case["outputs"]):
            inQ.put(inp)
            self.assertEqual(out, outQ.get())

        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())

import unittest
from flyde.flow import FlydeFlow


class TestFlow(unittest.TestCase):
    def test_flow(self):
        flow = FlydeFlow.from_file("tests/TestFlow.flyde")
        flow.run()
        flow.stopped.wait()
        self.assertTrue(flow.stopped.is_set())

from flyde.node import Component
from flyde.io import Input, Output, InputMode


class Print(Component):
    """Prints the input message to the console."""

    inputs = {
        'msg': Input(description='The message to print', type=str),
    }

    def process(self, msg: str):
        print(msg)


class Concat(Component):
    """Concatenates two strings."""

    inputs={
        'a': Input(description='The first string', type=str),
        'b': Input(description='The second string', type=str),
    }
    outputs={
        'out': Output(description='The concatenated string', type=str),
    }

    def process(self, a: str, b: str):
        out = a + b
        self.outputs['out'].send(out)

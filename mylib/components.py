from flyde.node import Component, Metadata
from flyde.io import Input, Output, InputMode


class Print(Component):
    meta: Metadata = Metadata(
        name='Print',
        display_name='Print',
        description='Prints the input message to the console',
        search_keywords=['print', 'console', 'output'],
        namespace='Print'
    )

    def __init__(self, **kwargs):
        super().__init__(
            inputs={
                'msg': Input(description='The message to print', type=str),
            },
            **kwargs
        )

    def process(self, msg: str):
        print(msg)


class Concat(Component):
    meta: Metadata = Metadata(
        name='Concat',
        display_name='Concat',
        description='Concatenates two strings',
        search_keywords=['concat', 'string', 'combine'],
        namespace='String'
    )

    def __init__(self, **kwargs):
        super().__init__(
            inputs={
                'a': Input(description='The first string', type=str),
                'b': Input(description='The second string', type=str),
            },
            outputs={
                'out': Output(description='The concatenated string', type=str),
            },
            **kwargs
        )

    def process(self, a: str, b: str):
        out = a + b
        self.outputs['out'].send(out)

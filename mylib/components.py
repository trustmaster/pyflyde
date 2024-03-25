from flyde.node import CodeNode, Metadata
from flyde.pins import InputPin, OutputPin

class Print(CodeNode):
    meta: Metadata = Metadata(
        name='Print',
        display_name='Print',
        description='Prints the input message to the console',
        search_keywords=['print', 'console', 'output'],
        namespace='Print'
    )
    inputs: dict[str, InputPin] = {
        'msg': InputPin(description='The message to print'),
    }

    def run(self, ins: dict[str, str], outs: dict[str, str]):
        print(ins['msg'])


class Concat(CodeNode):
    meta: Metadata = Metadata(
        name='Concat',
        display_name='Concat',
        description='Concatenates two strings',
        search_keywords=['concat', 'string', 'combine'],
        namespace='String'
    )
    inputs: dict[str, InputPin] = {
        'a': InputPin(description='The first string'),
        'b': InputPin(description='The second string'),
    }
    outputs: dict[str, OutputPin] = {
        'out': OutputPin(description='The concatenated string'),
    }

    def run(self, ins: dict[str, str], outs: dict[str, str]):
        outs['out'] = ins['a'] + ins['b']

from flyde.io import Input, InputMode, Output
from flyde.node import Component


class Echo(Component):
    """A simple component that echoes the input."""

    inputs = {"inp": Input(description="The input", type=str)}
    outputs = {"out": Output(description="The output", type=str)}

    def process(self, inp: str) -> dict[str, str]:
        return {"out": inp}


class Capitalize(Component):
    """A component that capitalizes the input."""

    inputs = {"inp": Input(description="The input", type=str)}
    outputs = {"out": Output(description="The output", type=str)}

    def process(self, inp: str) -> dict[str, str]:
        return {"out": inp.upper()}


class RepeatWordNTimes(Component):
    """A component that has both inputs and outputs and a sticky input."""

    inputs = {
        "word": Input(description="The input", type=str),
        "times": Input(
            description="The number of times to repeat the input",
            type=int,
            mode=InputMode.STICKY,
        ),
    }

    outputs = {"out": Output(description="The output", type=str)}

    def process(self, word: str, times: int) -> dict[str, str]:
        return {"out": word * times}

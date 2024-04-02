from typing import Any

from flyde.node import Component
from flyde.io import Input, Output, InputMode

class InlineValue(Component):
    """InlineValue sends a constant value to output."""

    outputs = {
        'value': Output(description='The constant value')
    }

    def __init__(self, value: Any, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def process(self):
        self.outputs['value'].send(self.value)
        # Inline value only runs once
        self.stop()

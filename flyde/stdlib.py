from typing import Any

from flyde.node import Component, Metadata
from flyde.io import Input, Output, InputMode

class InlineValue(Component):
    meta: Metadata = Metadata(
        name='InlineValue',
        display_name='Inline Value',
        description='Outputs a constant value',
        search_keywords=['constant', 'value', 'inline'],
        namespace='stdlib'
    )

    def __init__(self, value: Any, **kwargs):
        super().__init__(
            outputs={
                'value': Output(description='The constant value'),
            },
            **kwargs
        )
        self.value = value

    def process(self):
        self.outputs['value'].send(self.value)
        # Inline value only runs once
        self.stop()

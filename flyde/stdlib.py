from typing import Any

from flyde.node import Component
from flyde.io import Input, Output, InputMode


class InlineValue(Component):
    """InlineValue sends a constant value to output."""

    outputs = {"value": Output(description="The constant value")}

    def __init__(self, value: Any, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def process(self):
        self.send("value", self.value)
        # Inline value only runs once
        self.stop()


class GetAttribute(Component):
    """Get an attribute from an object or dictionary."""

    inputs = {
        "object": Input(description="The object or dictionary"),
        "attribute": Input(description="The attribute name", type=str),
    }
    outputs = {"value": Output(description="The attribute value")}

    def __init__(self, key: dict, **kwargs):
        super().__init__(**kwargs)
        self.value = None
        if "value" in key:
            self.value = key["value"]
        if "mode" in key:
            if key["mode"] == "static":
                self.inputs["attribute"]._input_mode = InputMode.STATIC
                self.inputs["attribute"].value = self.value
            else:
                self.inputs["attribute"]._input_mode = InputMode.STICKY
                if self.value is not None:
                    self.inputs["attribute"].value = self.value

    def process(self, object: Any, attribute: str):
        if isinstance(object, dict):
            value = object.get(attribute, None)
        elif hasattr(object, attribute):
            value = getattr(object, attribute)
        else:
            value = None
        self.send("value", value)

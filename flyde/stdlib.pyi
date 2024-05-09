from _typeshed import Incomplete as Incomplete
from flyde.node import Component as Component
from typing import Any

class InlineValue(Component):
    outputs: Incomplete
    value: Incomplete
    def __init__(self, value: Any, **kwargs) -> None: ...
    def process(self) -> None: ...

class GetAttribute(Component):
    inputs: Incomplete
    outputs: Incomplete
    value: Incomplete
    def __init__(self, key: dict, **kwargs) -> None: ...
    def process(self, object: Any, attribute: str): ...

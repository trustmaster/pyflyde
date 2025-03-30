from _typeshed import Incomplete
from enum import Enum
from flyde.io import Input as Input, InputMode as InputMode, Output as Output
from flyde.node import Component as Component
from typing import Any

class InlineValue(Component):
    """InlineValue sends a constant value to output."""
    outputs: Incomplete
    value: Incomplete
    def __init__(self, macro_data: dict, **kwargs) -> None: ...
    def process(self) -> None: ...
    def _is_inline_dict(self, value: Any) -> bool:
        """Check if a value is an inline Flyde value dict, which has `type` and `value` keys."""
    def _get_inline_value(self, value: Any) -> Any:
        """Get the value from an inline Flyde value output."""

class _ConditionType(Enum):
    """Condition type enumeration."""
    Equal = 'EQUAL'
    NotEqual = 'NOT_EQUAL'
    Contains = 'CONTAINS'
    NotContains = 'NOT_CONTAINS'
    RegexMatches = 'REGEX_MATCHES'
    Exists = 'EXISTS'
    NotExists = 'NOT_EXISTS'

class _ConditionalConfig:
    """Conditional configuration."""
    property_path: Incomplete
    condition_type: Incomplete
    condition_data: Incomplete
    left_operand: Incomplete
    right_operand: Incomplete
    def __init__(self, yml: dict) -> None: ...

class Conditional(Component):
    """Conditional component evaluates a condition against the input and sends the result to output."""
    inputs: Incomplete
    outputs: Incomplete
    _config: Incomplete
    def __init__(self, macro_data: dict, **kwargs) -> None: ...
    def _evaluate(self, left_operand: Any, right_operand: Any) -> bool: ...
    def process(self, leftOperand: Any, rightOperand: Any): ...

class GetAttribute(Component):
    """Get an attribute from an object or dictionary."""
    inputs: Incomplete
    outputs: Incomplete
    value: Incomplete
    def __init__(self, macro_data: dict, **kwargs) -> None: ...
    def process(self, object: Any, key: str): ...

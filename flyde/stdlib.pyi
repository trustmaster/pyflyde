from _typeshed import Incomplete
from dataclasses import dataclass
from enum import Enum
from flyde.io import Input as Input, InputConfig as InputConfig, InputMode as InputMode, InputType as InputType, Output as Output, Requiredness as Requiredness
from flyde.node import Component as Component
from typing import Any

class InlineValue(Component):
    """InlineValue sends a constant value to output."""
    outputs: Incomplete
    value: Incomplete
    def __init__(self, **kwargs) -> None: ...
    def process(self) -> None: ...

class _ConditionType(Enum):
    """Condition type enumeration."""
    Equal = 'EQUAL'
    NotEqual = 'NOT_EQUAL'
    Contains = 'CONTAINS'
    NotContains = 'NOT_CONTAINS'
    RegexMatches = 'REGEX_MATCHES'
    Exists = 'EXISTS'
    NotExists = 'NOT_EXISTS'

@dataclass
class _ConditionConfig:
    """Configuration etry for the condition type."""
    type: _ConditionType
    def __init__(self, type) -> None: ...

class _ConditionalConfig:
    """Conditional configuration."""
    condition_type: Incomplete
    left_operand: Incomplete
    right_operand: Incomplete
    def __init__(self, config: dict[str, InputConfig | _ConditionConfig]) -> None: ...

class Conditional(Component):
    """Conditional component evaluates a condition against the input and sends the result to output."""
    inputs: Incomplete
    outputs: Incomplete
    def parse_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Parse the raw config, handling the 'condition' special case."""
    _config: Incomplete
    def __init__(self, **kwargs) -> None: ...
    def _evaluate(self, left_operand: Any, right_operand: Any) -> bool: ...
    def process(self, leftOperand: Any, rightOperand: Any): ...

class GetAttribute(Component):
    """Get an attribute from an object or dictionary."""
    inputs: Incomplete
    outputs: Incomplete
    def __init__(self, **kwargs) -> None: ...
    def process(self, object: Any, key: str): ...

class Http(Component):
    """Http component makes HTTP requests with urllib."""
    inputs: Incomplete
    outputs: Incomplete
    def __init__(self, **kwargs) -> None: ...
    def process(self, url: str, method: str, headers: dict | None = None, params: dict | None = None, data: dict | None = None): ...

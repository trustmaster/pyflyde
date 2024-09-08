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

class _ConditionType(Enum):
    """Condition type enumeration."""
    Equal = 'EQUAL'
    NotEqual = 'NOT_EQUAL'
    GreaterThan = 'GREATER_THAN'
    GreaterThanOrEqual = 'GREATER_THAN_OR_EQUAL'
    LessThan = 'LESS_THAN'
    LessThanOrEqual = 'LESS_THAN_OR_EQUAL'
    Contains = 'CONTAINS'
    NotContains = 'NOT_CONTAINS'
    RegexMatches = 'REGEX_MATCHES'
    IsEmpty = 'IS_EMPTY'
    IsNotEmpty = 'IS_NOT_EMPTY'
    IsNull = 'IS_NULL'
    IsNotNull = 'IS_NOT_NULL'
    IsUndefined = 'IS_UNDEFINED'
    IsNotUndefined = 'IS_NOT_UNDEFINED'
    HasProperty = 'HAS_PROPERTY'
    LengthEqual = 'LENGTH_EQUAL'
    LengthNotEqual = 'LENGTH_NOT_EQUAL'
    LengthGreaterThan = 'LENGTH_GREATER_THAN'
    LengthLessThan = 'LENGTH_LESS_THAN'
    TypeEquals = 'TYPE_EQUALS'
    Expression = 'EXPRESSION'

class _ConditionalConfig:
    """Conditional configuration."""
    property_path: Incomplete
    condition_type: Incomplete
    condition_data: Incomplete
    compare_to_mode: Incomplete
    compare_to_value: Incomplete
    compare_to_type: Incomplete
    compare_to_property_path: str
    true_value_type: Incomplete
    true_value_expression: Incomplete
    false_value_type: Incomplete
    false_value_expression: Incomplete
    def __init__(self, yml: dict) -> None: ...

def _get_attribute_by_path(obj: Any, path: str) -> Any:
    """Gets nested attribute by property path."""

class Conditional(Component):
    """Conditional component evaluates a condition against the input and sends the result to output."""
    inputs: Incomplete
    outputs: Incomplete
    _config: Incomplete
    def __init__(self, macro_data: dict, **kwargs) -> None: ...
    def _evaluate(self, value: Any, compareTo: Any) -> bool: ...
    def process(self, value: Any, compareTo: Any): ...

class GetAttribute(Component):
    """Get an attribute from an object or dictionary."""
    inputs: Incomplete
    outputs: Incomplete
    value: Incomplete
    def __init__(self, macro_data: dict, **kwargs) -> None: ...
    def process(self, object: Any, attribute: str): ...

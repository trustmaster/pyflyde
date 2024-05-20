import re
from enum import Enum
from typing import Any

from flyde.node import Component
from flyde.io import Input, Output, InputMode


class InlineValue(Component):
    """InlineValue sends a constant value to output."""

    outputs = {"value": Output(description="The constant value")}

    def __init__(self, macro_data: dict, **kwargs):
        super().__init__(**kwargs)
        if "value" in macro_data:
            self.value = macro_data["value"]
        else:
            raise ValueError("Missing value in InlineValue configuration.")

    def process(self):
        self.send("value", self.value)
        # Inline value only runs once
        self.stop()


class _ConditionType(Enum):
    """Condition type enumeration."""
    Equal = "EQUAL"
    NotEqual = "NOT_EQUAL"
    GreaterThan = "GREATER_THAN"
    GreaterThanOrEqual = "GREATER_THAN_OR_EQUAL"
    LessThan = "LESS_THAN"
    LessThanOrEqual = "LESS_THAN_OR_EQUAL"
    Contains = "CONTAINS"
    NotContains = "NOT_CONTAINS"
    RegexMatches = "REGEX_MATCHES"
    IsEmpty = "IS_EMPTY"
    IsNotEmpty = "IS_NOT_EMPTY"
    IsNull = "IS_NULL"
    IsNotNull = "IS_NOT_NULL"
    IsUndefined = "IS_UNDEFINED"
    IsNotUndefined = "IS_NOT_UNDEFINED"
    HasProperty = "HAS_PROPERTY"
    LengthEqual = "LENGTH_EQUAL"
    LengthNotEqual = "LENGTH_NOT_EQUAL"
    LengthGreaterThan = "LENGTH_GREATER_THAN"
    LengthLessThan = "LENGTH_LESS_THAN"
    TypeEquals = "TYPE_EQUALS"
    Expression = "EXPRESSION"


class _ConditionalConfig:
    """Conditional configuration."""

    def __init__(self, yml: dict):
        self.property_path = yml.get("propertyPath", "")

        condition = yml.get("condition", {})
        condition_type = condition.get("type", "EQUAL")
        try:
            self.condition_type = _ConditionType(condition_type)
        except ValueError:
            raise ValueError(f"Unsupported condition type: {condition_type}")
        self.condition_data = condition.get("data", "")
        if self.condition_type == _ConditionType.Expression:
            raise NotImplementedError("Expression condition type is not implemented in PyFlyde.")

        compare_to = yml.get("compareTo", {})
        self.compare_to_mode = compare_to.get("mode", "static")
        if self.compare_to_mode == "static":
            self.compare_to_value = compare_to.get("value", None)
            self.compare_to_type = compare_to.get("type", "string")
            self.compare_to_property_path = ""
        else:
            self.compare_to_value = None
            self.compare_to_type = None
            self.compare_to_property_path = compare_to.get("propertyPath", "")

        true_value = yml.get("trueValue", {})
        self.true_value_type = true_value.get("type", "value")
        if self.true_value_type == "expression":
            self.true_value_expression = true_value.get("data", "")
            raise NotImplementedError("Expression value type is not implemented in PyFlyde.")
        else:
            self.true_value_expression = None

        false_value = yml.get("falseValue", {})
        self.false_value_type = false_value.get("type", "value")
        if self.false_value_type == "expression":
            self.false_value_expression = false_value.get("data", "")
            raise NotImplementedError("Expression value type is not implemented in PyFlyde.")
        else:
            self.false_value_expression = None


def _get_attribute_by_path(obj: Any, path: str) -> Any:
    """Gets nested attribute by property path."""
    for attr in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(attr, None)
        elif hasattr(obj, attr):
            obj = getattr(obj, attr)
        else:
            return None
    return obj


class Conditional(Component):
    """Conditional component evaluates a condition against the input and sends the result to output."""

    inputs = {
        "value": Input(description="Left operand of the comparison"),
        "compareTo": Input(description="Right operand of the comparison"),
    }
    outputs = {
        "true": Output(description="Output when the condition is true"),
        "false": Output(description="Output when the condition is false"),
    }

    def __init__(self, macro_data: dict, **kwargs):
        super().__init__(**kwargs)
        self._config = _ConditionalConfig(macro_data)
        if self._config.compare_to_mode == "static":
            self.inputs["compareTo"]._input_mode = InputMode.STATIC  # type: ignore
            self.inputs["compareTo"].value = self._config.compare_to_value

    def _evaluate(self, value: Any, compareTo: Any) -> bool:
        condition_type = self._config.condition_type
        if condition_type == _ConditionType.Equal:
            return value == compareTo
        elif condition_type == _ConditionType.NotEqual:
            return value != compareTo
        elif condition_type == _ConditionType.GreaterThan:
            return value > compareTo
        elif condition_type == _ConditionType.GreaterThanOrEqual:
            return value >= compareTo
        elif condition_type == _ConditionType.LessThan:
            return value < compareTo
        elif condition_type == _ConditionType.LessThanOrEqual:
            return value <= compareTo
        elif condition_type == _ConditionType.Contains:
            return compareTo in value
        elif condition_type == _ConditionType.NotContains:
            return compareTo not in value
        elif condition_type == _ConditionType.RegexMatches:
            m = re.match(compareTo, value)
            return m is not None
        elif condition_type == _ConditionType.IsEmpty:
            return value == ""
        elif condition_type == _ConditionType.IsNotEmpty:
            return value != ""
        elif condition_type == _ConditionType.IsNull:
            return value is None
        elif condition_type == _ConditionType.IsNotNull:
            return value is not None
        elif condition_type == _ConditionType.IsUndefined:
            return value is None
        elif condition_type == _ConditionType.IsNotUndefined:
            return value is not None
        elif condition_type == _ConditionType.HasProperty:
            if isinstance(value, dict):
                return compareTo in value
            return hasattr(value, compareTo)
        elif condition_type == _ConditionType.LengthEqual:
            return len(value) == compareTo
        elif condition_type == _ConditionType.LengthNotEqual:
            return len(value) != compareTo
        elif condition_type == _ConditionType.LengthGreaterThan:
            return len(value) > compareTo
        elif condition_type == _ConditionType.LengthLessThan:
            return len(value) < compareTo
        elif condition_type == _ConditionType.TypeEquals:
            if isinstance(compareTo, str):
                return type(value).__name__ == compareTo
            return type(value).__name__ == type(compareTo).__name__
        else:
            raise ValueError(f"Unsupported condition type: {condition_type}")

    def process(self, value: Any, compareTo: Any):
        left_operand = value
        right_operand = compareTo
        if self._config.property_path:
            left_operand = _get_attribute_by_path(value, self._config.property_path)

        if self._config.compare_to_property_path:
            right_operand = _get_attribute_by_path(compareTo, self._config.compare_to_property_path)

        result = self._evaluate(left_operand, right_operand)

        if result:
            if self._config.true_value_type == "compareTo":
                self.send("true", compareTo)
            else:
                self.send("true", value)
        else:
            if self._config.false_value_type == "compareTo":
                self.send("false", compareTo)
            else:
                self.send("false", value)


class GetAttribute(Component):
    """Get an attribute from an object or dictionary."""

    inputs = {
        "object": Input(description="The object or dictionary"),
        "attribute": Input(description="The attribute name", type=str),
    }
    outputs = {"value": Output(description="The attribute value")}

    def __init__(self, macro_data: dict, **kwargs):
        super().__init__(**kwargs)
        if "key" not in macro_data:
            raise ValueError("Missing 'key' in GetAttribute configuration.")
        key = macro_data["key"]
        self.value = None
        if "value" in key:
            self.value = key["value"]
        if "mode" in key:
            if key["mode"] == "static":
                self.inputs["attribute"]._input_mode = InputMode.STATIC  # type: ignore
                self.inputs["attribute"].value = self.value
            else:
                self.inputs["attribute"]._input_mode = InputMode.STICKY  # type: ignore
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

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
            value = macro_data["value"]
            self.value = self._get_inline_value(value) if self._is_inline_dict(value) else value
        else:
            raise ValueError("Missing value in InlineValue configuration.")

    def process(self):
        self.send("value", self.value)
        # Inline value only runs once
        self.stop()

    def _is_inline_dict(self, value: Any) -> bool:
        """Check if a value is an inline Flyde value dict, which has `type` and `value` keys."""
        supported_inline_types = ["dynamic", "string", "number", "boolean", "json", "select", "longtext"]
        return isinstance(value, dict) and "type" in value and value["type"] in supported_inline_types

    def _get_inline_value(self, value: Any) -> Any:
        """Get the value from an inline Flyde value output."""
        return value["value"]


class _ConditionType(Enum):
    """Condition type enumeration."""

    Equal = "EQUAL"
    NotEqual = "NOT_EQUAL"
    Contains = "CONTAINS"
    NotContains = "NOT_CONTAINS"
    RegexMatches = "REGEX_MATCHES"
    Exists = "EXISTS"
    NotExists = "NOT_EXISTS"


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

        left_operand = yml.get("leftOperand", {})
        self.left_operand = {
            "type": left_operand.get("type", "dynamic"),
            "value": left_operand.get("value", ""),
        }
        right_operand = yml.get("rightOperand", {})
        self.right_operand = {
            "type": right_operand.get("type", "dynamic"),
            "value": right_operand.get("value", ""),
        }


class Conditional(Component):
    """Conditional component evaluates a condition against the input and sends the result to output."""

    inputs = {
        "leftOperand": Input(description="Left operand of the condition"),
        "rightOperand": Input(description="Right operand of the condition"),
    }
    outputs = {
        "true": Output(description="Output when the condition is true"),
        "false": Output(description="Output when the condition is false"),
    }

    def __init__(self, macro_data: dict, **kwargs):
        super().__init__(**kwargs)
        self._config = _ConditionalConfig(macro_data)
        if self._config.left_operand["type"] != "dynamic":
            self.inputs["leftOperand"]._input_mode = InputMode.STATIC
            self.inputs["leftOperand"].value = self._config.left_operand["value"]
        if self._config.right_operand["type"] != "dynamic":
            self.inputs["rightOperand"]._input_mode = InputMode.STATIC
            self.inputs["rightOperand"].value = self._config.right_operand["value"]

    def _evaluate(self, left_operand: Any, right_operand: Any) -> bool:
        condition_type = self._config.condition_type
        if condition_type == _ConditionType.Equal:
            return left_operand == right_operand
        elif condition_type == _ConditionType.NotEqual:
            return left_operand != right_operand
        elif condition_type == _ConditionType.Contains:
            return right_operand in left_operand
        elif condition_type == _ConditionType.NotContains:
            return right_operand not in left_operand
        elif condition_type == _ConditionType.RegexMatches:
            m = re.match(right_operand, left_operand)
            return m is not None
        elif condition_type == _ConditionType.Exists:
            return left_operand is not None and left_operand != "" and left_operand != []
        elif condition_type == _ConditionType.NotExists:
            return left_operand is None or left_operand == "" or left_operand == []
        else:
            raise ValueError(f"Unsupported condition type: {condition_type}")

    def process(self, leftOperand: Any, rightOperand: Any):
        result = self._evaluate(leftOperand, rightOperand)

        if result:
            self.send("true", leftOperand)
        else:
            self.send("false", leftOperand)


class GetAttribute(Component):
    """Get an attribute from an object or dictionary."""

    inputs = {
        "object": Input(description="The object or dictionary"),
        "key": Input(description="The attribute name", type=str),
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
        if "type" in key:
            if key["type"] == "static":
                self.inputs["key"]._input_mode = InputMode.STATIC  # type: ignore
                self.inputs["key"].value = self.value
            else:
                self.inputs["key"]._input_mode = InputMode.STICKY  # type: ignore
                if self.value is not None:
                    self.inputs["key"].value = self.value

    def process(self, object: Any, key: str):
        keys = key.split(".")
        value = object
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, None)
            elif hasattr(value, k):
                value = getattr(value, k)
            else:
                value = None
                break
        self.send("value", value)

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Union

from flyde.io import Input, InputConfig, InputMode, InputType, Output
from flyde.node import Component


class InlineValue(Component):
    """InlineValue sends a constant value to output."""

    outputs = {"value": Output(description="The constant value")}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "value" in self._config:
            value = self._config["value"]
            self.value = value.value
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
    Contains = "CONTAINS"
    NotContains = "NOT_CONTAINS"
    RegexMatches = "REGEX_MATCHES"
    Exists = "EXISTS"
    NotExists = "NOT_EXISTS"


@dataclass
class _ConditionConfig:
    """Configuration etry for the condition type."""

    type: _ConditionType


class _ConditionalConfig:
    """Conditional configuration."""

    def __init__(self, config: dict[str, Union[InputConfig, _ConditionConfig]]):
        if "condition" not in config:
            raise ValueError("Missing 'condition' in Conditional configuration.")
        if not isinstance(config["condition"], _ConditionConfig):
            raise ValueError("Invalid 'condition' in Conditional configuration.")
        condition = config["condition"]
        self.condition_type = _ConditionType(condition.type)

        if "leftOperand" in config and isinstance(config["leftOperand"], InputConfig):
            self.left_operand: InputConfig = config["leftOperand"]

        if "rightOperand" in config and isinstance(config["rightOperand"], InputConfig):
            self.right_operand = config["rightOperand"]


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

    def parse_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Parse the raw config, handling the 'condition' special case."""
        result = super().parse_config(config)  # type: ignore

        # Handle the condition special case
        if "condition" in result and isinstance(result["condition"], dict) and "type" in result["condition"]:
            result["condition"] = _ConditionConfig(**result["condition"])

        return result

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._config = _ConditionalConfig(self._config)
        if hasattr(self._config, "left_operand") and self._config.left_operand.type != InputType.DYNAMIC:
            self.inputs["leftOperand"]._input_mode = InputMode.STATIC
            self.inputs["leftOperand"].value = self._config.left_operand.value
        if hasattr(self._config, "right_operand") and self._config.right_operand.type != InputType.DYNAMIC:
            self.inputs["rightOperand"]._input_mode = InputMode.STATIC
            self.inputs["rightOperand"].value = self._config.right_operand.value

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "key" not in self._config:
            raise ValueError("Missing 'key' in GetAttribute configuration.")
        key = self._config["key"]
        if not isinstance(key, InputConfig):
            raise ValueError("Invalid 'key' in GetAttribute configuration.")
        if key.type == InputType.DYNAMIC:
            self.inputs["key"]._input_mode = InputMode.STICKY  # type: ignore
            if key.value is not None:
                self.inputs["key"].value = key.value
        else:
            self.inputs["key"]._input_mode = InputMode.STATIC  # type: ignore
            self.inputs["key"].value = key.value

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

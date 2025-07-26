import inspect
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union
from urllib import error, parse, request

from flyde.io import Input, InputConfig, InputMode, InputType, Output, Requiredness
from flyde.node import Component


def list_nodes() -> list[str]:
    """Dynamically discover all Component classes defined in this module.

    Returns:
        list: List of class names that inherit from Component
    """
    current_module = inspect.getmodule(inspect.currentframe())
    component_classes = []
    if current_module is None:
        return component_classes

    for name, obj in inspect.getmembers(current_module):
        if (
            inspect.isclass(obj)
            and issubclass(obj, Component)
            and obj != Component
            and obj.__module__ == current_module.__name__
        ):
            component_classes.append(name)

    return sorted(component_classes)


class InlineValue(Component):
    """InlineValue sends a constant value to output."""

    icon = "pencil"
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

    icon = "circle-question"
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
        # Hack to parse a static config into conditional config
        self._config = _ConditionalConfig(self._config)  # type: ignore
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

    icon = "fa-magnifying-glass"
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


class Http(Component):
    """Http component makes HTTP requests with urllib."""

    icon = "globe"
    inputs = {
        "url": Input(description="URL to request", required=Requiredness.REQUIRED),
        "method": Input(description="HTTP method", type=str, required=Requiredness.REQUIRED),
        "headers": Input(description="HTTP headers", type=dict, required=Requiredness.OPTIONAL),
        "params": Input(description="URL parameters", type=dict, required=Requiredness.OPTIONAL),
        "data": Input(description="Request body", type=dict, required=Requiredness.OPTIONAL),
    }
    outputs = {
        "data": Output(description="Response data"),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if "method" in self._config and isinstance(self._config["method"], InputConfig):
            if self._config["method"].type == InputType.DYNAMIC:
                self.inputs["method"]._input_mode = InputMode.STICKY
            else:
                self.inputs["method"]._input_mode = InputMode.STATIC
                self.inputs["method"].value = self._config["method"].value
        else:
            self.inputs["method"]._input_mode = InputMode.STATIC
            self.inputs["method"].value = "GET"

        if "url" in self._config and isinstance(self._config["url"], InputConfig):
            if self._config["url"].type == InputType.DYNAMIC:
                self.inputs["url"]._input_mode = InputMode.QUEUE
            else:
                self.inputs["url"]._input_mode = InputMode.STATIC
                self.inputs["url"].value = self._config["url"].value

        if "headers" in self._config and isinstance(self._config["headers"], InputConfig):
            if self._config["headers"].type == InputType.DYNAMIC:
                self.inputs["headers"]._input_mode = InputMode.STICKY
            else:
                self.inputs["headers"]._input_mode = InputMode.STATIC
                self.inputs["headers"].value = self._config["headers"].value
        else:
            self.inputs["headers"]._input_mode = InputMode.STATIC
            self.inputs["headers"].value = {}

        if "params" in self._config and isinstance(self._config["params"], InputConfig):
            if self._config["params"].type == InputType.DYNAMIC:
                self.inputs["params"]._input_mode = InputMode.STICKY
            else:
                self.inputs["params"]._input_mode = InputMode.STATIC
                self.inputs["params"].value = self._config["params"].value
        else:
            self.inputs["params"]._input_mode = InputMode.STATIC
            self.inputs["params"].value = {}

        if "data" in self._config and isinstance(self._config["data"], InputConfig):
            if self._config["data"].type == InputType.DYNAMIC:
                self.inputs["data"]._input_mode = InputMode.STICKY
            else:
                self.inputs["data"]._input_mode = InputMode.STATIC
                self.inputs["data"].value = self._config["data"].value
        else:
            self.inputs["data"]._input_mode = InputMode.STATIC
            self.inputs["data"].value = {}

    def process(
        self,
        url: str,
        method: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ):
        try:
            if params:
                url_parts = list(parse.urlparse(url))
                query = dict(parse.parse_qsl(url_parts[4]))
                query.update(params)
                url_parts[4] = parse.urlencode(query)
                url = parse.urlunparse(url_parts)

            req = request.Request(url)
            req.method = method

            if headers:
                for key, value in headers.items():
                    req.add_header(key, value)

            data_bytes = None
            if data and method != "GET":
                data_bytes = json.dumps(data).encode("utf-8")
                req.add_header("Content-Type", "application/json")
                req.add_header("Content-Length", str(len(data_bytes)))

            with request.urlopen(req, data=data_bytes) as response:
                content_type = response.headers.get("Content-Type", "")
                response_data = response.read()

                # Handle text-based responses
                if (
                    "text/" in content_type
                    or "json" in content_type
                    or "xml" in content_type
                    or "application/javascript" in content_type
                ):
                    # Extract charset from content-type header if present
                    charset = "utf-8"  # Default charset
                    if "charset=" in content_type:
                        charset_part = content_type.split("charset=")[1]
                        if ";" in charset_part:
                            charset = charset_part.split(";")[0].strip()
                        else:
                            charset = charset_part.strip()

                    try:
                        response_data = response_data.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        # Fallback to utf-8 if specified charset fails
                        response_data = response_data.decode("utf-8", errors="replace")

                    # Try to parse JSON if the content type indicates JSON
                    if "json" in content_type:
                        try:
                            response_data = json.loads(response_data)
                        except json.JSONDecodeError:
                            pass
                # Binary data remains as bytes

                self.send("data", response_data)
        except error.HTTPError as e:
            raise e
        except error.URLError as e:
            raise e
        except Exception as e:
            raise e

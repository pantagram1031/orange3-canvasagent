from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


class PlanValidationError(ValueError):
    """Raised when a model response is not a valid canvas plan."""


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PlanValidationError(f"Action field '{key}' must be a non-empty string")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise PlanValidationError(f"Action field '{key}' must be a string when provided")
    return value


def _position(data: dict[str, Any], key: str, *, required: bool = False) -> tuple[float, ...] | None:
    value = data.get(key)
    if value is None:
        if required:
            raise PlanValidationError(f"Action field '{key}' is required")
        return None
    if not isinstance(value, (list, tuple)) or len(value) not in (2, 4):
        raise PlanValidationError(f"Action field '{key}' must be a 2- or 4-number list")
    try:
        return tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise PlanValidationError(f"Action field '{key}' must contain numbers") from exc


@dataclass(frozen=True)
class CanvasAction:
    type: str
    node_id: str | None = None
    qualified_name: str | None = None
    title: str | None = None
    position: tuple[float, ...] | None = None
    source_node_id: str | None = None
    sink_node_id: str | None = None
    source_channel: str | None = None
    sink_channel: str | None = None
    text: str | None = None
    bounds: tuple[float, ...] | None = None

    SUPPORTED_TYPES: ClassVar[set[str]] = {
        "add_widget",
        "connect",
        "rename_node",
        "move_node",
        "annotate",
    }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanvasAction":
        if not isinstance(data, dict):
            raise PlanValidationError("Each action must be an object")
        action_type = _require_str(data, "type")
        if action_type not in cls.SUPPORTED_TYPES:
            raise PlanValidationError(f"Unsupported action type: {action_type}")

        if action_type == "add_widget":
            return cls(
                type=action_type,
                node_id=_require_str(data, "node_id"),
                qualified_name=_require_str(data, "qualified_name"),
                title=_optional_str(data, "title"),
                position=_position(data, "position"),
            )
        if action_type == "connect":
            return cls(
                type=action_type,
                source_node_id=_require_str(data, "source_node_id"),
                sink_node_id=_require_str(data, "sink_node_id"),
                source_channel=_optional_str(data, "source_channel"),
                sink_channel=_optional_str(data, "sink_channel"),
            )
        if action_type == "rename_node":
            return cls(
                type=action_type,
                node_id=_require_str(data, "node_id"),
                title=_require_str(data, "title"),
            )
        if action_type == "move_node":
            return cls(
                type=action_type,
                node_id=_require_str(data, "node_id"),
                position=_position(data, "position", required=True),
            )
        return cls(
            type=action_type,
            text=_require_str(data, "text"),
            bounds=_position(data, "bounds", required=True),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in self.__dict__.items()
            if value is not None
        }


@dataclass(frozen=True)
class CanvasPlan:
    summary: str
    actions: list[CanvasAction]
    warnings: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanvasPlan":
        if not isinstance(data, dict):
            raise PlanValidationError("Canvas plan must be a JSON object")
        summary = data.get("summary")
        if not isinstance(summary, str):
            raise PlanValidationError("Canvas plan field 'summary' must be a string")
        raw_actions = data.get("actions")
        if not isinstance(raw_actions, list):
            raise PlanValidationError("Canvas plan field 'actions' must be a list")
        raw_warnings = data.get("warnings", [])
        if not isinstance(raw_warnings, list) or not all(
            isinstance(item, str) for item in raw_warnings
        ):
            raise PlanValidationError("Canvas plan field 'warnings' must be a list of strings")
        return cls(
            summary=summary,
            actions=[CanvasAction.from_dict(item) for item in raw_actions],
            warnings=list(raw_warnings),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "actions": [action.to_dict() for action in self.actions],
            "warnings": self.warnings,
        }


CANVAS_PLAN_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "actions", "warnings"],
    "properties": {
        "summary": {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "actions": {
            "type": "array",
            "items": {
                "oneOf": [
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["type", "node_id", "qualified_name"],
                        "properties": {
                            "type": {"const": "add_widget"},
                            "node_id": {"type": "string"},
                            "qualified_name": {"type": "string"},
                            "title": {"type": "string"},
                            "position": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {"type": "number"},
                            },
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["type", "source_node_id", "sink_node_id"],
                        "properties": {
                            "type": {"const": "connect"},
                            "source_node_id": {"type": "string"},
                            "sink_node_id": {"type": "string"},
                            "source_channel": {"type": "string"},
                            "sink_channel": {"type": "string"},
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["type", "node_id", "title"],
                        "properties": {
                            "type": {"const": "rename_node"},
                            "node_id": {"type": "string"},
                            "title": {"type": "string"},
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["type", "node_id", "position"],
                        "properties": {
                            "type": {"const": "move_node"},
                            "node_id": {"type": "string"},
                            "position": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 2,
                                "items": {"type": "number"},
                            },
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["type", "text", "bounds"],
                        "properties": {
                            "type": {"const": "annotate"},
                            "text": {"type": "string"},
                            "bounds": {
                                "type": "array",
                                "minItems": 4,
                                "maxItems": 4,
                                "items": {"type": "number"},
                            },
                        },
                    },
                ]
            },
        },
    },
}


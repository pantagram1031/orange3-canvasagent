from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Callable

from .schema import CanvasAction, CanvasPlan


class CanvasExecutionError(RuntimeError):
    """Raised when a structured canvas action cannot be applied."""


@dataclass(frozen=True)
class CanvasApplyResult:
    messages: list[str]


@dataclass
class _SimpleLink:
    source_node: object
    source_channel: object
    sink_node: object
    sink_channel: object


class CanvasActionExecutor:
    def __init__(
        self,
        scheme,
        *,
        resolve_widget_description: Callable[[str], object],
        node_ids: dict[str, object] | None = None,
    ):
        self.scheme = scheme
        self.resolve_widget_description = resolve_widget_description
        self.node_ids = dict(node_ids or {})
        self._index_existing_nodes()

    def apply(self, plan: CanvasPlan) -> CanvasApplyResult:
        messages: list[str] = []
        for action in plan.actions:
            message = self._apply_action(action)
            if message:
                messages.append(message)
        return CanvasApplyResult(messages=messages)

    def _index_existing_nodes(self) -> None:
        for index, node in enumerate(getattr(self.scheme, "nodes", [])):
            self.node_ids.setdefault(f"node_{index}", node)

    def _apply_action(self, action: CanvasAction) -> str:
        if action.type == "add_widget":
            return self._add_widget(action)
        if action.type == "connect":
            return self._connect(action)
        if action.type == "rename_node":
            return self._rename_node(action)
        if action.type == "move_node":
            return self._move_node(action)
        if action.type == "annotate":
            return self._annotate(action)
        raise CanvasExecutionError(f"Unsupported action type: {action.type}")

    def _add_widget(self, action: CanvasAction) -> str:
        description = self._resolve(action.qualified_name)
        position = action.position or self._next_position()
        title = action.title or getattr(description, "name", action.qualified_name)
        if hasattr(self.scheme, "new_node"):
            node = self.scheme.new_node(description, title=title, position=position)
        else:
            node = self._create_scheme_node(description, title, position)
            self.scheme.add_node(node)
        self.node_ids[action.node_id] = node
        return f"Added {title}"

    def _connect(self, action: CanvasAction) -> str:
        source_node = self._node(action.source_node_id, "source")
        sink_node = self._node(action.sink_node_id, "sink")
        source_channel, sink_channel = self._channels(source_node, sink_node, action)
        link = self._create_link(source_node, source_channel, sink_node, sink_channel)
        if hasattr(self.scheme, "add_link"):
            self.scheme.add_link(link)
        elif hasattr(self.scheme, "new_link"):
            self.scheme.new_link(source_node, source_channel, sink_node, sink_channel)
        else:
            raise CanvasExecutionError("Scheme does not support adding links")
        return f"Connected {action.source_node_id} to {action.sink_node_id}"

    def _rename_node(self, action: CanvasAction) -> str:
        node = self._node(action.node_id, "target")
        if hasattr(node, "set_title"):
            node.set_title(action.title)
        else:
            node.title = action.title
        return f"Renamed {action.node_id} to {action.title}"

    def _move_node(self, action: CanvasAction) -> str:
        node = self._node(action.node_id, "target")
        position = tuple(action.position)
        if hasattr(node, "set_position"):
            node.set_position(position)
        else:
            node.position = position
        return f"Moved {action.node_id}"

    def _annotate(self, action: CanvasAction) -> str:
        annotation = self._create_annotation(action.text, action.bounds)
        if hasattr(self.scheme, "add_annotation"):
            self.scheme.add_annotation(annotation)
        else:
            raise CanvasExecutionError("Scheme does not support annotations")
        return "Added annotation"

    def _resolve(self, qualified_name: str):
        try:
            return self.resolve_widget_description(qualified_name)
        except Exception as exc:
            raise CanvasExecutionError(f"Unknown widget: {qualified_name}") from exc

    def _node(self, node_id: str, role: str):
        try:
            return self.node_ids[node_id]
        except KeyError as exc:
            raise CanvasExecutionError(f"Unknown {role} node: {node_id}") from exc

    def _channels(self, source_node, sink_node, action: CanvasAction):
        if action.source_channel or action.sink_channel:
            source = self._find_channel(source_node.description.outputs, action.source_channel, "source")
            sink = self._find_channel(sink_node.description.inputs, action.sink_channel, "sink")
            return source, sink
        proposals = self.scheme.propose_links(source_node, sink_node)
        if not proposals:
            raise CanvasExecutionError("No compatible channels found for connection")
        source_channel, sink_channel, _weight = proposals[0]
        return source_channel, sink_channel

    def _find_channel(self, channels, name: str | None, role: str):
        if name is None:
            if len(channels) == 1:
                return channels[0]
            raise CanvasExecutionError(f"{role.capitalize()} channel name is required")
        for channel in channels:
            if getattr(channel, "name", None) == name:
                return channel
        raise CanvasExecutionError(f"Unknown {role} channel: {name}")

    def _create_scheme_node(self, description, title, position):
        try:
            from orangecanvas.scheme.node import SchemeNode

            return SchemeNode(description, title=title, position=position)
        except Exception:
            return SimpleNamespace(description=description, title=title, position=position)

    def _create_link(self, source_node, source_channel, sink_node, sink_channel):
        try:
            from orangecanvas.scheme.link import SchemeLink

            return SchemeLink(source_node, source_channel, sink_node, sink_channel)
        except Exception:
            return _SimpleLink(source_node, source_channel, sink_node, sink_channel)

    def _create_annotation(self, text, bounds):
        try:
            from orangecanvas.scheme.annotations import SchemeTextAnnotation

            return SchemeTextAnnotation(rect=tuple(bounds), text=text)
        except Exception:
            return SimpleNamespace(text=text, rect=tuple(bounds))

    def _next_position(self) -> tuple[float, float]:
        count = len(getattr(self.scheme, "nodes", []))
        return (float(50 + count * 160), 50.0)


def describe_canvas_state(scheme) -> dict:
    nodes = []
    for index, node in enumerate(getattr(scheme, "nodes", [])):
        description = getattr(node, "description", None)
        nodes.append(
            {
                "id": f"node_{index}",
                "title": getattr(node, "title", ""),
                "qualified_name": getattr(description, "qualified_name", ""),
                "position": list(getattr(node, "position", (0, 0)) or (0, 0)),
                "outputs": [getattr(channel, "name", "") for channel in getattr(description, "outputs", [])],
                "inputs": [getattr(channel, "name", "") for channel in getattr(description, "inputs", [])],
            }
        )
    links = []
    for link in getattr(scheme, "links", []):
        links.append(
            {
                "source": getattr(getattr(link, "source_node", None), "title", ""),
                "source_channel": getattr(getattr(link, "source_channel", None), "name", ""),
                "sink": getattr(getattr(link, "sink_node", None), "title", ""),
                "sink_channel": getattr(getattr(link, "sink_channel", None), "name", ""),
            }
        )
    return {"nodes": nodes, "links": links}


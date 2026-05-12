from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace


class FakeChannel:
    def __init__(self, name: str):
        self.name = name


class FakeDescription:
    def __init__(self, name: str, qualified_name: str, outputs=None, inputs=None):
        self.name = name
        self.qualified_name = qualified_name
        self.outputs = outputs or []
        self.inputs = inputs or []
        self.project_name = "tests"
        self.version = "1"


class FakeNode:
    def __init__(self, description: FakeDescription, title=None, position=None):
        self.description = description
        self.title = title or description.name
        self.position = position or (0.0, 0.0)

    def set_title(self, title: str):
        self.title = title

    def set_position(self, position):
        self.position = tuple(position)


class FakeLink:
    def __init__(self, source_node, source_channel, sink_node, sink_channel):
        self.source_node = source_node
        self.source_channel = source_channel
        self.sink_node = sink_node
        self.sink_channel = sink_channel


class FakeAnnotation:
    def __init__(self, text, rect):
        self.text = text
        self.rect = tuple(rect)


class FakeScheme:
    def __init__(self):
        self.nodes = []
        self.links = []
        self.annotations = []
        self.loaded_snapshot = None

    def new_node(self, description, title=None, position=None):
        node = FakeNode(description, title=title, position=position)
        self.nodes.append(node)
        return node

    def add_link(self, link):
        self.links.append(link)

    def propose_links(self, source_node, sink_node):
        if not source_node.description.outputs or not sink_node.description.inputs:
            return []
        return [(source_node.description.outputs[0], sink_node.description.inputs[0], 1)]

    def add_annotation(self, annotation):
        self.annotations.append(annotation)

    def save_to(self, stream, pretty=True, pickle_fallback=False):
        titles = ",".join(node.title for node in self.nodes)
        stream.write(titles.encode("utf-8"))

    def load_from(self, stream):
        self.loaded_snapshot = stream.read()


def fake_resolver():
    output = FakeChannel("Data")
    input_ = FakeChannel("Data")
    descriptions = {
        "Orange.widgets.data.owfile.OWFile": FakeDescription(
            "File", "Orange.widgets.data.owfile.OWFile", outputs=[output]
        ),
        "Orange.widgets.data.owtable.OWDataTable": FakeDescription(
            "Data Table", "Orange.widgets.data.owtable.OWDataTable", inputs=[input_]
        ),
    }
    return descriptions.__getitem__


class CompletedProcess:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


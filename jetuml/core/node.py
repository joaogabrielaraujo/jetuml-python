"""
Node hierarchy for JetUML.
"""

from __future__ import annotations
import math
import uuid
from abc import abstractmethod
from typing import Any, Dict, List, Optional
from .element import DiagramElement
from .geometry import Point, Rectangle


class Node(DiagramElement):
    """Abstract base class for diagram nodes."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 100.0,
        height: float = 60.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(element_id)
        self.bounds = Rectangle(x, y, width, height)
        self.parent_id: Optional[str] = None

    @property
    def x(self) -> float:
        return self.bounds.x

    @x.setter
    def x(self, val: float) -> None:
        self.bounds.x = val

    @property
    def y(self) -> float:
        return self.bounds.y

    @y.setter
    def y(self, val: float) -> None:
        self.bounds.y = val

    @property
    def width(self) -> float:
        return self.bounds.width

    @width.setter
    def width(self, val: float) -> None:
        self.bounds.width = val

    @property
    def height(self) -> float:
        return self.bounds.height

    @height.setter
    def height(self, val: float) -> None:
        self.bounds.height = val

    @property
    def center(self) -> Point:
        return self.bounds.center

    def contains(self, p: Point) -> bool:
        return self.bounds.contains(p)

    def connection_point(self, target: Point) -> Point:
        return self.bounds.connection_point(target)

    def translate(self, dx: float, dy: float) -> None:
        self.bounds.x += dx
        self.bounds.y += dy

    @abstractmethod
    def clone(self) -> Node:
        pass


class ClassNode(Node):
    """UML Class node with name, attributes, and methods compartments."""

    def __init__(
        self,
        name: str = "Class",
        attributes: str = "",
        methods: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 120.0,
        height: float = 80.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self._name = name
        self._attributes = attributes
        self._methods = methods
        self._update_bounds()
        if width > self.width:
            self.width = width
        if height > self.height:
            self.height = height

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val
        self._update_bounds()

    @property
    def attributes(self) -> str:
        return self._attributes

    @attributes.setter
    def attributes(self, val: str) -> None:
        self._attributes = val
        self._update_bounds()

    @property
    def methods(self) -> str:
        return self._methods

    @methods.setter
    def methods(self, val: str) -> None:
        self._methods = val
        self._update_bounds()

    def _update_bounds(self) -> None:
        attr_lines = len(self._attributes.splitlines()) if self._attributes else 0
        method_lines = len(self._methods.splitlines()) if self._methods else 0
        attr_h = max(1, attr_lines) * 18.0 + 8.0
        method_h = max(1, method_lines) * 18.0 + 8.0
        min_height = 28.0 + attr_h + method_h
        self.height = max(80.0, float(min_height))

        all_text = [self._name] + self._attributes.splitlines() + self._methods.splitlines()
        max_len = max([len(t) for t in all_text], default=6)
        min_width = max(120.0, max_len * 8.5 + 24.0)
        self.width = max(120.0, float(min_width))

    def clone(self) -> ClassNode:
        c = ClassNode(
            self.name,
            self.attributes,
            self.methods,
            self.x,
            self.y,
            self.width,
            self.height,
        )
        c.parent_id = self.parent_id
        return c

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ClassNode",
            "id": self.id,
            "name": self.name,
            "attributes": self.attributes,
            "methods": self.methods,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClassNode:
        node = cls(
            name=data.get("name", "Class"),
            attributes=data.get("attributes", ""),
            methods=data.get("methods", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 120.0),
            height=data.get("height", 80.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class InterfaceNode(Node):
    """UML Interface node with «interface» stereotype, name, and methods."""

    def __init__(
        self,
        name: str = "Interface",
        methods: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 120.0,
        height: float = 70.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self._name = name
        self._methods = methods
        self._update_bounds()
        if width > self.width:
            self.width = width
        if height > self.height:
            self.height = height

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val
        self._update_bounds()

    @property
    def methods(self) -> str:
        return self._methods

    @methods.setter
    def methods(self, val: str) -> None:
        self._methods = val
        self._update_bounds()

    def _update_bounds(self) -> None:
        method_lines = len(self._methods.splitlines()) if self._methods else 0
        method_h = max(1, method_lines) * 18.0 + 8.0
        min_height = 42.0 + method_h
        self.height = max(70.0, float(min_height))

        all_text = ["«interface»", self._name] + self._methods.splitlines()
        max_len = max([len(t) for t in all_text], default=9)
        min_width = max(120.0, max_len * 8.5 + 24.0)
        self.width = max(120.0, float(min_width))

    def clone(self) -> InterfaceNode:
        node = InterfaceNode(self.name, self.methods, self.x, self.y, self.width, self.height)
        node.parent_id = self.parent_id
        return node

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "InterfaceNode",
            "id": self.id,
            "name": self.name,
            "methods": self.methods,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InterfaceNode:
        node = cls(
            name=data.get("name", "Interface"),
            methods=data.get("methods", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 120.0),
            height=data.get("height", 70.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class PackageNode(Node):
    """UML Package node with name and children."""

    def __init__(
        self,
        name: str = "Package",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 200.0,
        height: float = 140.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self.name = name
        self.child_ids: List[str] = []

    def clone(self) -> PackageNode:
        p = PackageNode(self.name, self.x, self.y, self.width, self.height)
        p.parent_id = self.parent_id
        p.child_ids = list(self.child_ids)
        return p

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PackageNode",
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
            "child_ids": list(self.child_ids),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PackageNode:
        node = cls(
            name=data.get("name", "Package"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 200.0),
            height=data.get("height", 140.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        node.child_ids = list(data.get("child_ids", []))
        return node


class PackageDescriptionNode(Node):
    """Package Description node with name and content."""

    def __init__(
        self,
        name: str = "Package Description",
        content: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 140.0,
        height: float = 90.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self.name = name
        self.content = content

    def clone(self) -> PackageDescriptionNode:
        n = PackageDescriptionNode(self.name, self.content, self.x, self.y, self.width, self.height)
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PackageDescriptionNode",
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PackageDescriptionNode:
        node = cls(
            name=data.get("name", "Package Description"),
            content=data.get("content", ""),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 140.0),
            height=data.get("height", 90.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class NoteNode(Node):
    """UML Note node with folded corner."""

    def __init__(
        self,
        text: str = "Note",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 110.0,
        height: float = 65.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self._text = text
        self._update_bounds()
        if width > self.width:
            self.width = width
        if height > self.height:
            self.height = height

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self._text = val
        self._update_bounds()

    def _update_bounds(self) -> None:
        lines = self._text.splitlines() if self._text else ["Note"]
        min_height = max(55.0, len(lines) * 18.0 + 20)
        max_len = max([len(line) for line in lines], default=4)
        min_width = max(90.0, max_len * 8.0 + 25)
        self.width = max(90.0, min_width)
        self.height = max(55.0, min_height)

    def clone(self) -> NoteNode:
        n = NoteNode(self.text, self.x, self.y, self.width, self.height)
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "NoteNode",
            "id": self.id,
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NoteNode:
        node = cls(
            text=data.get("text", "Note"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 110.0),
            height=data.get("height", 65.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class PointNode(Node):
    """Synthetic point node for anchoring note connectors to arbitrary diagram positions."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, 6.0, 6.0, element_id)

    def connection_point(self, target: Point) -> Point:
        return Point(self.x + 3.0, self.y + 3.0)

    def clone(self) -> PointNode:
        return PointNode(self.x, self.y)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "PointNode",
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PointNode:
        node = cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class ActorNode(Node):
    """UML Use Case Actor stick figure."""

    def __init__(
        self,
        name: str = "Actor",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 60.0,
        height: float = 80.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self.name = name

    def clone(self) -> ActorNode:
        n = ActorNode(self.name, self.x, self.y, self.width, self.height)
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ActorNode",
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ActorNode:
        node = cls(
            name=data.get("name", "Actor"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 60.0),
            height=data.get("height", 80.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class UseCaseNode(Node):
    """UML Use Case ellipse node."""

    def __init__(
        self,
        name: str = "Use Case",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 120.0,
        height: float = 60.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self.name = name

    def connection_point(self, target: Point) -> Point:
        # Ellipse boundary intersection
        c = self.center
        dx = target.x - c.x
        dy = target.y - c.y
        if dx == 0 and dy == 0:
            return c
        a = self.width / 2.0
        b = self.height / 2.0
        # (x/a)^2 + (y/b)^2 = 1 => t = 1 / sqrt((dx/a)^2 + (dy/b)^2)
        factor = math.hypot(dx / a, dy / b)
        if factor == 0:
            return c
        t = 1.0 / factor
        return Point(c.x + dx * t, c.y + dy * t)

    def clone(self) -> UseCaseNode:
        n = UseCaseNode(self.name, self.x, self.y, self.width, self.height)
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "UseCaseNode",
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UseCaseNode:
        node = cls(
            name=data.get("name", "Use Case"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 120.0),
            height=data.get("height", 60.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class StateNode(Node):
    """UML State rounded rectangle."""

    def __init__(
        self,
        name: str = "State",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 100.0,
        height: float = 50.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self.name = name

    def clone(self) -> StateNode:
        n = StateNode(self.name, self.x, self.y, self.width, self.height)
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "StateNode",
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StateNode:
        node = cls(
            name=data.get("name", "State"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 100.0),
            height=data.get("height", 50.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class InitialStateNode(Node):
    """UML Initial State black circle."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, 24.0, 24.0, element_id)

    def connection_point(self, target: Point) -> Point:
        c = self.center
        dx = target.x - c.x
        dy = target.y - c.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return c
        r = 12.0
        return Point(c.x + (dx / dist) * r, c.y + (dy / dist) * r)

    def clone(self) -> InitialStateNode:
        n = InitialStateNode(self.x, self.y)
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "InitialStateNode",
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InitialStateNode:
        node = cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class FinalStateNode(Node):
    """UML Final State bullseye circle."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, 26.0, 26.0, element_id)

    def connection_point(self, target: Point) -> Point:
        c = self.center
        dx = target.x - c.x
        dy = target.y - c.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return c
        r = 13.0
        return Point(c.x + (dx / dist) * r, c.y + (dy / dist) * r)

    def clone(self) -> FinalStateNode:
        n = FinalStateNode(self.x, self.y)
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "FinalStateNode",
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FinalStateNode:
        node = cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class ObjectNode(Node):
    """UML Object node with underlined name and field rows."""

    def __init__(
        self,
        name: str = "object:Type",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 140.0,
        height: float = 70.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self.name = name
        self.field_ids: List[str] = []

    def clone(self) -> ObjectNode:
        n = ObjectNode(self.name, self.x, self.y, self.width, self.height)
        n.parent_id = self.parent_id
        n.field_ids = list(self.field_ids)
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ObjectNode",
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
            "field_ids": list(self.field_ids),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ObjectNode:
        node = cls(
            name=data.get("name", "object:Type"),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 140.0),
            height=data.get("height", 70.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        node.field_ids = list(data.get("field_ids", []))
        return node


class FieldNode(Node):
    """Field node belonging to an ObjectNode with Name and Value compartments."""

    def __init__(
        self,
        name: str = "field",
        value: str = "",
        parent_object_id: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 120.0,
        height: float = 24.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self.name = name
        self.value = value
        self.parent_id = parent_object_id

    @property
    def parent_object_id(self) -> str:
        return self.parent_id or ""

    @parent_object_id.setter
    def parent_object_id(self, val: str) -> None:
        self.parent_id = val

    @property
    def value_bounds(self) -> Rectangle:
        """The bounding box for the Value compartment (right half of the field)."""
        half_w = self.width / 2.0
        return Rectangle(self.x + half_w, self.y, half_w, self.height)

    def value_connection_point(self) -> Point:
        """Connection origin point for reference edges starting at the value part."""
        return Point(self.x + self.width * 0.75, self.y + self.height / 2.0)

    def clone(self) -> FieldNode:
        n = FieldNode(
            self.name,
            self.value,
            self.parent_object_id,
            self.x,
            self.y,
            self.width,
            self.height,
        )
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "FieldNode",
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "parent_object_id": self.parent_object_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FieldNode:
        node = cls(
            name=data.get("name", "field"),
            value=data.get("value", ""),
            parent_object_id=data.get("parent_object_id", data.get("parent_id", "")),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 120.0),
            height=data.get("height", 24.0),
            element_id=data.get("id"),
        )
        return node


class ImplicitParameterNode(Node):
    """UML Sequence diagram Implicit Parameter (actor or object box with lifeline)."""

    def __init__(
        self,
        name: str = "param:Type",
        x: float = 0.0,
        y: float = 20.0,
        width: float = 90.0,
        height: float = 40.0,
        lifeline_length: float = 400.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, element_id)
        self.name = name
        self.lifeline_length = lifeline_length

    @property
    def lifeline_x(self) -> float:
        return self.x + self.width / 2.0

    @property
    def lifeline_top_y(self) -> float:
        return self.y + self.height

    @property
    def lifeline_bottom_y(self) -> float:
        return self.y + self.height + self.lifeline_length

    def contains(self, p: Point) -> bool:
        # Check header box
        if self.bounds.contains(p):
            return True
        # Check lifeline proximity (within 10px horizontally)
        if abs(p.x - self.lifeline_x) <= 10.0 and self.lifeline_top_y <= p.y <= self.lifeline_bottom_y:
            return True
        return False

    def clone(self) -> ImplicitParameterNode:
        n = ImplicitParameterNode(
            self.name,
            self.x,
            self.y,
            self.width,
            self.height,
            self.lifeline_length,
        )
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ImplicitParameterNode",
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "lifeline_length": self.lifeline_length,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImplicitParameterNode:
        node = cls(
            name=data.get("name", "param:Type"),
            x=data.get("x", 0.0),
            y=data.get("y", 20.0),
            width=data.get("width", 90.0),
            height=data.get("height", 40.0),
            lifeline_length=data.get("lifeline_length", 400.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


class CallNode(Node):
    """Sequence diagram activation box."""

    def __init__(
        self,
        implicit_parameter_id: str = "",
        y_top: float = 80.0,
        y_bottom: float = 140.0,
        open_bottom: bool = False,
        caller_id: Optional[str] = None,
        x: float = 0.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y_top, 16.0, max(20.0, y_bottom - y_top), element_id)
        self.implicit_parameter_id = implicit_parameter_id
        self.open_bottom = open_bottom
        self.caller_id = caller_id

    @property
    def y_top(self) -> float:
        return self.y

    @y_top.setter
    def y_top(self, val: float) -> None:
        h = max(20.0, self.bottom - val)
        self.y = val
        self.height = h

    @property
    def y_bottom(self) -> float:
        return self.bottom

    @y_bottom.setter
    def y_bottom(self, val: float) -> None:
        self.height = max(20.0, val - self.y)

    def clone(self) -> CallNode:
        n = CallNode(
            self.implicit_parameter_id,
            self.y,
            self.bottom,
            self.open_bottom,
            self.caller_id,
            self.x,
        )
        n.parent_id = self.parent_id
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "CallNode",
            "id": self.id,
            "implicit_parameter_id": self.implicit_parameter_id,
            "y_top": self.y,
            "y_bottom": self.bottom,
            "open_bottom": self.open_bottom,
            "caller_id": self.caller_id,
            "x": self.x,
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CallNode:
        node = cls(
            implicit_parameter_id=data.get("implicit_parameter_id", ""),
            y_top=data.get("y_top", 80.0),
            y_bottom=data.get("y_bottom", 140.0),
            open_bottom=data.get("open_bottom", False),
            caller_id=data.get("caller_id"),
            x=data.get("x", 0.0),
            element_id=data.get("id"),
        )
        node.parent_id = data.get("parent_id")
        return node


NODE_TYPE_MAP = {
    "ClassNode": ClassNode,
    "InterfaceNode": InterfaceNode,
    "PackageNode": PackageNode,
    "PackageDescriptionNode": PackageDescriptionNode,
    "NoteNode": NoteNode,
    "PointNode": PointNode,
    "ActorNode": ActorNode,
    "UseCaseNode": UseCaseNode,
    "StateNode": StateNode,
    "InitialStateNode": InitialStateNode,
    "FinalStateNode": FinalStateNode,
    "ObjectNode": ObjectNode,
    "FieldNode": FieldNode,
    "ImplicitParameterNode": ImplicitParameterNode,
    "CallNode": CallNode,
}

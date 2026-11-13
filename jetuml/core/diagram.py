"""
Diagram aggregate and management for JetUML.
"""

from __future__ import annotations
import copy
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from .element import DiagramElement
from .geometry import Point, Rectangle
from .node import (
    Node,
    ClassNode,
    InterfaceNode,
    PackageNode,
    PackageDescriptionNode,
    NoteNode,
    PointNode,
    ActorNode,
    UseCaseNode,
    StateNode,
    InitialStateNode,
    FinalStateNode,
    ObjectNode,
    FieldNode,
    ImplicitParameterNode,
    CallNode,
    NODE_TYPE_MAP,
)
from .edge import (
    Edge,
    ClassRelationshipEdge,
    NoteEdge,
    ReferenceEdge,
    CollaborationEdge,
    TransitionEdge,
    UseCaseRelationshipEdge,
    CallEdge,
    ReturnEdge,
    EDGE_TYPE_MAP,
)
from .validation import DiagramValidator, ValidationResult


class DiagramType(str, Enum):
    CLASS = "Class"
    SEQUENCE = "Sequence"
    STATE = "State"
    OBJECT = "Object"
    USE_CASE = "Use Case"


class Diagram:
    """Core domain model representing a UML diagram."""

    def __init__(
        self,
        diagram_type: DiagramType = DiagramType.CLASS,
        title: str = "Untitled",
        width: float = 1200.0,
        height: float = 800.0,
    ) -> None:
        self.diagram_type = diagram_type
        self.title = title
        self.width = width
        self.height = height
        self.file_path: Optional[str] = None
        self.is_modified: bool = False

        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._change_listeners: List[Callable[[], None]] = []

    @property
    def nodes(self) -> List[Node]:
        return list(self._nodes.values())

    @property
    def edges(self) -> List[Edge]:
        return list(self._edges.values())

    @property
    def elements(self) -> List[DiagramElement]:
        return list(self._nodes.values()) + list(self._edges.values())

    @property
    def selected_elements(self) -> List[DiagramElement]:
        return [elem for elem in self.elements if elem.selected]

    def add_change_listener(self, listener: Callable[[], None]) -> None:
        self._change_listeners.append(listener)

    def remove_change_listener(self, listener: Callable[[], None]) -> None:
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def notify_change(self) -> None:
        self.is_modified = True
        for listener in self._change_listeners:
            listener()

    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def get_edge_by_id(self, edge_id: str) -> Optional[Edge]:
        return self._edges.get(edge_id)

    def add_node(self, node: Node, parent: Optional[Node] = None) -> ValidationResult:
        res = DiagramValidator.validate_node_creation(self, node, parent)
        if not res.is_valid:
            return res

        self._nodes[node.id] = node
        if parent:
            node.parent_id = parent.id
            if isinstance(parent, PackageNode):
                if node.id not in parent.child_ids:
                    parent.child_ids.append(node.id)
            elif isinstance(parent, ObjectNode):
                if node.id not in parent.field_ids:
                    parent.field_ids.append(node.id)

        self.notify_change()
        return ValidationResult.ok()

    def remove_node(self, node_id: str) -> None:
        node = self._nodes.pop(node_id, None)
        if not node:
            return

        # If node has parent, unregister from parent
        if node.parent_id:
            parent = self._nodes.get(node.parent_id)
            if isinstance(parent, PackageNode) and node_id in parent.child_ids:
                parent.child_ids.remove(node_id)
            elif isinstance(parent, ObjectNode) and node_id in parent.field_ids:
                parent.field_ids.remove(node_id)

        # If node has children (e.g. Package or Object), remove children recursively
        if isinstance(node, PackageNode):
            for child_id in list(node.child_ids):
                self.remove_node(child_id)
        elif isinstance(node, ObjectNode):
            for child_id in list(node.field_ids):
                self.remove_node(child_id)

        # Remove connected edges
        connected_edges = [
            e.id
            for e in self.edges
            if e.start_node_id == node_id or e.end_node_id == node_id
        ]
        for eid in connected_edges:
            self.remove_edge(eid)

        self.notify_change()

    def add_edge(self, edge: Edge) -> ValidationResult:
        start_node = self.get_node_by_id(edge.start_node_id)
        end_node = self.get_node_by_id(edge.end_node_id)

        if not start_node or not end_node:
            return ValidationResult.error("Edge must connect existing nodes.")

        res = DiagramValidator.validate_edge_creation(self, edge, start_node, end_node)
        if not res.is_valid:
            return res

        # Automatic curvature offset calculation for multiple edges (RF17, RF19)
        existing_between = [
            e
            for e in self.edges
            if (
                (e.start_node_id == edge.start_node_id and e.end_node_id == edge.end_node_id)
                or (e.start_node_id == edge.end_node_id and e.end_node_id == edge.start_node_id)
            )
        ]
        if existing_between:
            edge.curvature_offset = 25.0 * (len(existing_between) % 2 * 2 - 1)

        self._edges[edge.id] = edge
        self.notify_change()
        return ValidationResult.ok()

    def remove_edge(self, edge_id: str) -> None:
        if edge_id in self._edges:
            del self._edges[edge_id]
            self.notify_change()

    def find_node_at(self, p: Point) -> Optional[Node]:
        """Finds topmost node at given point, checking children first."""
        # Check field nodes first
        for node in reversed(self.nodes):
            if isinstance(node, FieldNode) and node.contains(p):
                return node
        # Check regular nodes (non-packages first, then packages)
        for node in reversed(self.nodes):
            if not isinstance(node, PackageNode) and node.contains(p):
                return node
        for node in reversed(self.nodes):
            if isinstance(node, PackageNode) and node.contains(p):
                return node
        return None

    def find_edge_at(self, p: Point, tolerance: float = 6.0) -> Optional[Edge]:
        """Hit test for edges within tolerance distance."""
        for edge in reversed(self.edges):
            start_node = self.get_node_by_id(edge.start_node_id)
            end_node = self.get_node_by_id(edge.end_node_id)
            if not start_node or not end_node:
                continue
            if edge.is_self_edge:
                # Approximate self-edge bounds
                sb = start_node.bounds
                loop_box = Rectangle(sb.right - 10, sb.y - 30, 40, 40)
                if loop_box.contains(p):
                    return edge
            else:
                p1 = start_node.connection_point(end_node.center)
                p2 = end_node.connection_point(start_node.center)
                # Distance from point to line segment
                dist = self._dist_point_to_segment(p, p1, p2)
                if dist <= tolerance:
                    return edge
        return None

    def _dist_point_to_segment(self, p: Point, v: Point, w: Point) -> float:
        import math
        l2 = (v.x - w.x) ** 2 + (v.y - w.y) ** 2
        if l2 == 0:
            return p.distance_to(v)
        t = max(0.0, min(1.0, ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2))
        proj = Point(v.x + t * (w.x - v.x), v.y + t * (w.y - v.y))
        return p.distance_to(proj)

    def select_all(self) -> None:
        for elem in self.elements:
            elem.selected = True

    def clear_selection(self) -> None:
        for elem in self.elements:
            elem.selected = False

    def select(self, elem: DiagramElement) -> None:
        elem.selected = True

    def deselect(self, elem: DiagramElement) -> None:
        elem.selected = False

    def content_bounds(self) -> Rectangle:
        """Calculates bounding box enclosing all nodes and edges (RF05)."""
        if not self._nodes:
            return Rectangle(0, 0, 400, 300)

        min_x = min(node.bounds.x for node in self._nodes.values())
        min_y = min(node.bounds.y for node in self._nodes.values())
        max_x = max(node.bounds.right for node in self._nodes.values())
        max_y = max(node.bounds.bottom for node in self._nodes.values())

        # Give a 20px margin around content
        margin = 20.0
        return Rectangle(
            max(0.0, min_x - margin),
            max(0.0, min_y - margin),
            (max_x - min_x) + margin * 2,
            (max_y - min_y) + margin * 2,
        )

    def duplicate(self) -> Diagram:
        """Creates a deep copy of diagram in a new tab (RF03)."""
        new_d = Diagram(
            diagram_type=self.diagram_type,
            title=f"Copy of {self.title}",
            width=self.width,
            height=self.height,
        )
        # Map old node IDs to new nodes
        id_map: Dict[str, str] = {}
        for node in self.nodes:
            c = node.clone()
            id_map[node.id] = c.id
            new_d._nodes[c.id] = c

        # Fix parent/child IDs in cloned nodes
        for node in new_d.nodes:
            if node.parent_id and node.parent_id in id_map:
                node.parent_id = id_map[node.parent_id]
            if isinstance(node, PackageNode):
                node.child_ids = [id_map[cid] for cid in node.child_ids if cid in id_map]
            elif isinstance(node, ObjectNode):
                node.field_ids = [id_map[cid] for cid in node.field_ids if cid in id_map]

        # Clone edges
        for edge in self.edges:
            if edge.start_node_id in id_map and edge.end_node_id in id_map:
                ce = edge.clone()
                ce.start_node_id = id_map[edge.start_node_id]
                ce.end_node_id = id_map[edge.end_node_id]
                new_d._edges[ce.id] = ce

        return new_d

    def to_dict(self) -> Dict[str, Any]:
        """JSON serializable representation conforming to open format (RNF02)."""
        return {
            "version": "1.0",
            "diagram_type": self.diagram_type.value,
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Diagram:
        dtype_str = data.get("diagram_type", "Class")
        dtype = DiagramType(dtype_str)
        diag = cls(
            diagram_type=dtype,
            title=data.get("title", "Untitled"),
            width=float(data.get("width", 1200.0)),
            height=float(data.get("height", 800.0)),
        )

        # Deserialize nodes
        for nd in data.get("nodes", []):
            ntype = nd.get("type")
            node_cls = NODE_TYPE_MAP.get(ntype)
            if node_cls:
                node = node_cls.from_dict(nd)
                diag._nodes[node.id] = node

        # Deserialize edges
        for ed in data.get("edges", []):
            etype = ed.get("type")
            edge_cls = EDGE_TYPE_MAP.get(etype)
            if edge_cls:
                edge = edge_cls.from_dict(ed)
                diag._edges[edge.id] = edge

        diag.is_modified = False
        return diag

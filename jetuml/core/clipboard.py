"""
Clipboard management for Cut, Copy, and Paste operations (RF34).
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from .element import DiagramElement
from .geometry import Point
from .node import (
    Node,
    ClassNode,
    InterfaceNode,
    PackageNode,
    PackageDescriptionNode,
    NoteNode,
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
from .diagram import DiagramType
from .commands import AddNodeCommand, AddEdgeCommand, CompoundCommand

if TYPE_CHECKING:
    from .diagram import Diagram


COMPATIBLE_TYPES = {
    DiagramType.CLASS: {
        "ClassNode",
        "InterfaceNode",
        "PackageNode",
        "PackageDescriptionNode",
        "NoteNode",
        "PointNode",
        "ClassRelationshipEdge",
        "NoteEdge",
    },
    DiagramType.STATE: {
        "StateNode",
        "InitialStateNode",
        "FinalStateNode",
        "NoteNode",
        "PointNode",
        "TransitionEdge",
        "NoteEdge",
    },
    DiagramType.OBJECT: {
        "ObjectNode",
        "FieldNode",
        "NoteNode",
        "PointNode",
        "ReferenceEdge",
        "CollaborationEdge",
        "NoteEdge",
    },
    DiagramType.USE_CASE: {
        "ActorNode",
        "UseCaseNode",
        "NoteNode",
        "PointNode",
        "UseCaseRelationshipEdge",
        "NoteEdge",
    },
    DiagramType.SEQUENCE: set(),  # Sequence pasting is explicitly disallowed
}


class ClipboardManager:
    """Singleton/shared clipboard for diagram elements."""

    _instance: Optional[ClipboardManager] = None

    def __init__(self) -> None:
        self._buffer_nodes: List[Dict[str, Any]] = []
        self._buffer_edges: List[Dict[str, Any]] = []
        self.source_diagram_type: Optional[DiagramType] = None

    @classmethod
    def get_instance(cls) -> ClipboardManager:
        if cls._instance is None:
            cls._instance = ClipboardManager()
        return cls._instance

    def copy(self, diagram: Diagram) -> int:
        """Copies selected elements to clipboard buffer."""
        self._buffer_nodes.clear()
        self._buffer_edges.clear()
        self.source_diagram_type = diagram.diagram_type

        selected_nodes = [e for e in diagram.selected_elements if isinstance(e, Node)]
        selected_node_ids = {n.id for n in selected_nodes}

        # If a package or object is copied, also copy all its children
        for node in list(selected_nodes):
            if isinstance(node, PackageNode):
                for cid in node.child_ids:
                    cn = diagram.get_node_by_id(cid)
                    if cn and cn not in selected_nodes:
                        selected_nodes.append(cn)
                        selected_node_ids.add(cn.id)
            elif isinstance(node, ObjectNode):
                for cid in node.field_ids:
                    cn = diagram.get_node_by_id(cid)
                    if cn and cn not in selected_nodes:
                        selected_nodes.append(cn)
                        selected_node_ids.add(cn.id)

        for n in selected_nodes:
            self._buffer_nodes.append(n.to_dict())

        # Copy edges between selected nodes
        for e in diagram.edges:
            if e.start_node_id in selected_node_ids and e.end_node_id in selected_node_ids:
                self._buffer_edges.append(e.to_dict())

        return len(self._buffer_nodes) + len(self._buffer_edges)

    def can_paste_into(self, target_diagram: Diagram) -> Tuple[bool, Optional[str]]:
        if not self._buffer_nodes and not self._buffer_edges:
            return False, "Clipboard is empty."

        if target_diagram.diagram_type == DiagramType.SEQUENCE:
            return False, "Paste is not allowed in Sequence Diagrams to preserve control flow validity."

        allowed = COMPATIBLE_TYPES.get(target_diagram.diagram_type, set())
        for nd in self._buffer_nodes:
            if nd.get("type") not in allowed:
                return False, f"Element '{nd.get('type')}' is incompatible with {target_diagram.diagram_type.value} Diagram."

        for ed in self._buffer_edges:
            if ed.get("type") not in allowed:
                return False, f"Edge '{ed.get('type')}' is incompatible with {target_diagram.diagram_type.value} Diagram."

        return True, None

    def paste(self, target_diagram: Diagram, offset: float = 20.0) -> Tuple[bool, Optional[str], Optional[CompoundCommand]]:
        can_paste, err = self.can_paste_into(target_diagram)
        if not can_paste:
            return False, err, None

        id_map: Dict[str, str] = {}
        new_nodes: List[Node] = []
        commands = []

        # Instantiate new nodes
        for nd in self._buffer_nodes:
            cls = NODE_TYPE_MAP.get(nd.get("type"))
            if not cls:
                continue
            new_node = cls.from_dict(nd)
            old_id = new_node.id
            new_node.id = cls.from_dict({"id": None}).id  # fresh UUID
            new_node.translate(offset, offset)
            id_map[old_id] = new_node.id
            new_nodes.append(new_node)

        # Fix hierarchy relationships in new nodes
        for node in new_nodes:
            if node.parent_id and node.parent_id in id_map:
                node.parent_id = id_map[node.parent_id]
            if isinstance(node, PackageNode):
                node.child_ids = [id_map[cid] for cid in node.child_ids if cid in id_map]
            elif isinstance(node, ObjectNode):
                node.field_ids = [id_map[cid] for cid in node.field_ids if cid in id_map]

            parent = target_diagram.get_node_by_id(node.parent_id) if node.parent_id else None
            commands.append(AddNodeCommand(target_diagram, node, parent))

        # Instantiate new edges
        for ed in self._buffer_edges:
            cls = EDGE_TYPE_MAP.get(ed.get("type"))
            if not cls:
                continue
            old_start = ed.get("start_node_id")
            old_end = ed.get("end_node_id")
            if old_start in id_map and old_end in id_map:
                new_edge = cls.from_dict(ed)
                new_edge.id = cls.from_dict({"id": None}).id
                new_edge.start_node_id = id_map[old_start]
                new_edge.end_node_id = id_map[old_end]
                commands.append(AddEdgeCommand(target_diagram, new_edge))

        compound = CompoundCommand(commands)
        target_diagram.clear_selection()
        for node in new_nodes:
            node.selected = True

        return True, None, compound

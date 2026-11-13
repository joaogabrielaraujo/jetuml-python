"""
Command pattern implementation for Undo/Redo (RF21).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from .element import DiagramElement
from .geometry import Point

if TYPE_CHECKING:
    from .diagram import Diagram
    from .node import Node
    from .edge import Edge


class Command(ABC):
    """Abstract command interface."""

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

    def redo(self) -> None:
        self.execute()


class CommandStack:
    """Manages undo and redo stacks for a diagram."""

    def __init__(self, diagram: Diagram) -> None:
        self.diagram = diagram
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []

    def execute(self, cmd: Command) -> None:
        cmd.execute()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.redo()
        self._undo_stack.append(cmd)
        return True

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()


class AddNodeCommand(Command):
    """Command to add a node to the diagram."""

    def __init__(self, diagram: Diagram, node: Node, parent: Optional[Node] = None) -> None:
        self.diagram = diagram
        self.node = node
        self.parent = parent

    def execute(self) -> None:
        self.diagram.add_node(self.node, self.parent)

    def undo(self) -> None:
        self.diagram.remove_node(self.node.id)


class AddEdgeCommand(Command):
    """Command to add an edge to the diagram."""

    def __init__(self, diagram: Diagram, edge: Edge) -> None:
        self.diagram = diagram
        self.edge = edge

    def execute(self) -> None:
        self.diagram.add_edge(self.edge)

    def undo(self) -> None:
        self.diagram.remove_edge(self.edge.id)


class RemoveElementsCommand(Command):
    """Command to remove one or more diagram elements."""

    def __init__(self, diagram: Diagram, elements: List[DiagramElement]) -> None:
        self.diagram = diagram
        self.elements = list(elements)
        # Store full serialized snapshot of elements and connected edges for undo
        self._saved_nodes: List[Dict[str, Any]] = []
        self._saved_edges: List[Dict[str, Any]] = []

    def execute(self) -> None:
        from .node import Node
        from .edge import Edge

        self._saved_nodes.clear()
        self._saved_edges.clear()

        node_ids = {e.id for e in self.elements if isinstance(e, Node)}
        edge_ids = {e.id for e in self.elements if isinstance(e, Edge)}

        # Also collect all connected edges that will be removed implicitly
        for edge in self.diagram.edges:
            if edge.start_node_id in node_ids or edge.end_node_id in node_ids:
                edge_ids.add(edge.id)

        for nid in node_ids:
            node = self.diagram.get_node_by_id(nid)
            if node:
                self._saved_nodes.append(node.to_dict())

        for eid in edge_ids:
            edge = self.diagram.get_edge_by_id(eid)
            if edge:
                self._saved_edges.append(edge.to_dict())

        # Now remove them from diagram
        for eid in edge_ids:
            self.diagram.remove_edge(eid)
        for nid in node_ids:
            self.diagram.remove_node(nid)

    def undo(self) -> None:
        from .node import NODE_TYPE_MAP
        from .edge import EDGE_TYPE_MAP

        # Re-add saved nodes
        for nd in self._saved_nodes:
            cls = NODE_TYPE_MAP.get(nd.get("type"))
            if cls:
                node = cls.from_dict(nd)
                self.diagram._nodes[node.id] = node

        # Re-add saved edges
        for ed in self._saved_edges:
            cls = EDGE_TYPE_MAP.get(ed.get("type"))
            if cls:
                edge = cls.from_dict(ed)
                self.diagram._edges[edge.id] = edge

        self.diagram.notify_change()


class MoveElementsCommand(Command):
    """Command to move nodes by a delta."""

    def __init__(self, diagram: Diagram, node_ids: List[str], dx: float, dy: float) -> None:
        self.diagram = diagram
        self.node_ids = list(node_ids)
        self.dx = dx
        self.dy = dy

    def execute(self) -> None:
        for nid in self.node_ids:
            node = self.diagram.get_node_by_id(nid)
            if node:
                node.translate(self.dx, self.dy)
        self.diagram.notify_change()

    def undo(self) -> None:
        for nid in self.node_ids:
            node = self.diagram.get_node_by_id(nid)
            if node:
                node.translate(-self.dx, -self.dy)
        self.diagram.notify_change()


class EditPropertiesCommand(Command):
    """Command to update element properties."""

    def __init__(
        self,
        diagram: Diagram,
        element: DiagramElement,
        old_props: Dict[str, Any],
        new_props: Dict[str, Any],
    ) -> None:
        self.diagram = diagram
        self.element = element
        self.old_props = old_props
        self.new_props = new_props

    def _apply(self, props: Dict[str, Any]) -> None:
        for key, val in props.items():
            if hasattr(self.element, key):
                setattr(self.element, key, val)
        # Update bounds if node
        if hasattr(self.element, "_update_bounds"):
            getattr(self.element, "_update_bounds")()
        self.diagram.notify_change()

    def execute(self) -> None:
        self._apply(self.new_props)

    def undo(self) -> None:
        self._apply(self.old_props)


class CompoundCommand(Command):
    """Batches multiple commands into a single undo/redo unit."""

    def __init__(self, commands: List[Command]) -> None:
        self.commands = list(commands)

    def execute(self) -> None:
        for cmd in self.commands:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self.commands):
            cmd.undo()

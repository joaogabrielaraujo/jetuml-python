"""
Validation engine and rules for JetUML diagrams.
Enforces RF18, RF19, RF25, RF30.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from .diagram import Diagram
    from .node import Node
    from .edge import Edge


@dataclass
class ValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    silent_failure: bool = False

    @classmethod
    def ok(cls) -> ValidationResult:
        return cls(is_valid=True)

    @classmethod
    def error(cls, message: str) -> ValidationResult:
        return cls(is_valid=False, error_message=message, silent_failure=False)

    @classmethod
    def silent(cls) -> ValidationResult:
        return cls(is_valid=False, error_message=None, silent_failure=True)


class DiagramValidator:
    """Validator containing rules for all diagram types."""

    @staticmethod
    def validate_edge_creation(
        diagram: Diagram,
        edge: Edge,
        start_node: Node,
        end_node: Node,
    ) -> ValidationResult:
        from .diagram import DiagramType
        from .node import (
            ClassNode,
            InterfaceNode,
            PackageNode,
            ActorNode,
            UseCaseNode,
            StateNode,
            InitialStateNode,
            FinalStateNode,
            ObjectNode,
            FieldNode,
            ImplicitParameterNode,
            CallNode,
            NoteNode,
            PointNode,
        )
        from .edge import (
            ClassRelationshipEdge,
            NoteEdge,
            ReferenceEdge,
            CollaborationEdge,
            TransitionEdge,
            UseCaseRelationshipEdge,
            CallEdge,
            ReturnEdge,
        )

        dtype = diagram.diagram_type

        # Note edges can connect Note to anything or Note to Point
        if isinstance(edge, NoteEdge):
            if not (isinstance(start_node, NoteNode) or isinstance(end_node, NoteNode)):
                return ValidationResult.error("Note connector must attach to a Note node.")
            return ValidationResult.ok()

        # -------------------------------------------------------------
        # CLASS DIAGRAM VALIDATIONS (RF18, RF19)
        # -------------------------------------------------------------
        if dtype == DiagramType.CLASS:
            if not isinstance(edge, ClassRelationshipEdge):
                return ValidationResult.error("Invalid edge type for Class Diagram.")

            # Self-edge checks (RF19)
            if start_node.id == end_node.id:
                if edge.relationship_type in ("Inheritance", "Dependency"):
                    return ValidationResult.error(
                        f"Self-{edge.relationship_type.lower()} is not allowed in Class Diagrams."
                    )

            # Node compatibility
            # Realization: source class/interface -> target interface
            # Inheritance: class -> class or interface -> interface
            if edge.relationship_type == "Realization":
                if not (isinstance(end_node, InterfaceNode) or isinstance(end_node, ClassNode)):
                    return ValidationResult.error("Realization target must be an Interface or Class.")

            # RF18: No more than 1 edge of same type between same two nodes
            existing_same_type = [
                e
                for e in diagram.edges
                if isinstance(e, ClassRelationshipEdge)
                and e.relationship_type == edge.relationship_type
                and (
                    (e.start_node_id == start_node.id and e.end_node_id == end_node.id)
                    or (e.start_node_id == end_node.id and e.end_node_id == start_node.id)
                )
            ]
            if existing_same_type:
                return ValidationResult.error(
                    f"An edge of type '{edge.relationship_type}' already exists between these nodes."
                )

            # RF18: Direct cycles (vai-e-volta) with Inheritance, Dependency, Aggregation, Association
            if start_node.id != end_node.id:
                if edge.relationship_type in ("Inheritance", "Dependency", "Aggregation", "Association"):
                    reverse_cycle = [
                        e
                        for e in diagram.edges
                        if isinstance(e, ClassRelationshipEdge)
                        and e.relationship_type == edge.relationship_type
                        and e.start_node_id == end_node.id
                        and e.end_node_id == start_node.id
                    ]
                    if reverse_cycle:
                        return ValidationResult.error(
                            f"Direct cycle not allowed for '{edge.relationship_type}'."
                        )

            # RF18: Cannot combine Association and Aggregation simultaneously between same two classes
            is_assoc = edge.relationship_type == "Association"
            is_aggreg = edge.relationship_type in ("Aggregation", "Composition")
            if is_assoc or is_aggreg:
                for e in diagram.edges:
                    if isinstance(e, ClassRelationshipEdge) and (
                        (e.start_node_id == start_node.id and e.end_node_id == end_node.id)
                        or (e.start_node_id == end_node.id and e.end_node_id == start_node.id)
                    ):
                        if is_assoc and e.relationship_type in ("Aggregation", "Composition"):
                            return ValidationResult.error(
                                "Cannot combine Association and Aggregation/Composition between the same classes."
                            )
                        if is_aggreg and e.relationship_type == "Association":
                            return ValidationResult.error(
                                "Cannot combine Association and Aggregation/Composition between the same classes."
                            )

            return ValidationResult.ok()

        # -------------------------------------------------------------
        # OBJECT DIAGRAM VALIDATIONS (RF18, RF19, RF25, RF26)
        # -------------------------------------------------------------
        elif dtype == DiagramType.OBJECT:
            if isinstance(edge, ReferenceEdge):
                # Must start at FieldNode and end at ObjectNode
                if not isinstance(start_node, FieldNode):
                    return ValidationResult.error("Reference edge must start at a Field's value.")
                if not isinstance(end_node, ObjectNode):
                    return ValidationResult.error("Reference edge must target an Object node.")
                return ValidationResult.ok()

            elif isinstance(edge, CollaborationEdge):
                if not (isinstance(start_node, ObjectNode) and isinstance(end_node, ObjectNode)):
                    return ValidationResult.error("Collaboration edge must connect two Object nodes.")

                # RF19: Block self-collaboration for Objects
                if start_node.id == end_node.id:
                    return ValidationResult.error("Self-collaboration is not allowed for Objects.")

                # RF18: No more than 1 edge of same type between same two nodes
                existing = [
                    e
                    for e in diagram.edges
                    if isinstance(e, CollaborationEdge)
                    and e.start_node_id == start_node.id
                    and e.end_node_id == end_node.id
                ]
                if existing:
                    return ValidationResult.error("A collaboration edge already exists in this direction.")

                # RF18: Collaboration cycle between two Objects (A->B and B->A)
                reverse_collab = [
                    e
                    for e in diagram.edges
                    if isinstance(e, CollaborationEdge)
                    and e.start_node_id == end_node.id
                    and e.end_node_id == start_node.id
                ]
                if reverse_collab:
                    return ValidationResult.error(
                        "Collaboration cycles between two Objects are not allowed."
                    )

                return ValidationResult.ok()

            return ValidationResult.error("Invalid edge for Object Diagram.")

        # -------------------------------------------------------------
        # STATE DIAGRAM VALIDATIONS (RF18, RF19)
        # -------------------------------------------------------------
        elif dtype == DiagramType.STATE:
            if not isinstance(edge, TransitionEdge):
                return ValidationResult.error("Invalid edge for State Diagram.")

            # RF19: Transitions starting from Final State or ending at Initial State are rejected
            if isinstance(start_node, FinalStateNode):
                return ValidationResult.error("Cannot create transitions starting from a Final State.")
            if isinstance(end_node, InitialStateNode):
                return ValidationResult.error("Cannot create transitions ending at an Initial State.")

            # Self-transitions
            if start_node.id == end_node.id:
                if isinstance(start_node, (InitialStateNode, FinalStateNode)):
                    return ValidationResult.error("Initial and Final states cannot have self-transitions.")

                self_transitions = [
                    e
                    for e in diagram.edges
                    if isinstance(e, TransitionEdge)
                    and e.start_node_id == start_node.id
                    and e.end_node_id == start_node.id
                ]
                if len(self_transitions) >= 2:
                    return ValidationResult.error("A state can have at most two self-transitions.")
                return ValidationResult.ok()

            # Between two different nodes: up to 2 transitions in each direction (RF19)
            directional_transitions = [
                e
                for e in diagram.edges
                if isinstance(e, TransitionEdge)
                and e.start_node_id == start_node.id
                and e.end_node_id == end_node.id
            ]
            if len(directional_transitions) >= 2:
                return ValidationResult.error(
                    "At most two transitions are allowed in the same direction between two states."
                )

            return ValidationResult.ok()

        # -------------------------------------------------------------
        # USE CASE DIAGRAM VALIDATIONS (RF18, RF19)
        # -------------------------------------------------------------
        elif dtype == DiagramType.USE_CASE:
            if not isinstance(edge, UseCaseRelationshipEdge):
                return ValidationResult.error("Invalid edge for Use Case Diagram.")

            # RF19: Block self-association, self-inheritance, self-dependency for Actors / Use Cases
            if start_node.id == end_node.id:
                return ValidationResult.error(
                    f"Self-{edge.relationship_type.lower()} is not allowed for Actors or Use Cases."
                )

            # RF18: No more than 1 edge of same type between same two nodes
            existing = [
                e
                for e in diagram.edges
                if isinstance(e, UseCaseRelationshipEdge)
                and e.relationship_type == edge.relationship_type
                and (
                    (e.start_node_id == start_node.id and e.end_node_id == end_node.id)
                    or (e.start_node_id == end_node.id and e.end_node_id == start_node.id)
                )
            ]
            if existing:
                return ValidationResult.error(
                    f"An edge of type '{edge.relationship_type}' already exists between these elements."
                )

            return ValidationResult.ok()

        # -------------------------------------------------------------
        # SEQUENCE DIAGRAM VALIDATIONS (RF30)
        # -------------------------------------------------------------
        elif dtype == DiagramType.SEQUENCE:
            if not (isinstance(edge, CallEdge) or isinstance(edge, ReturnEdge)):
                return ValidationResult.error("Invalid edge for Sequence Diagram.")

            # RF30: Connecting Call or Return edges to elements that are not CallNodes (activation boxes)
            # Exception: Constructor call (RF29) can target an ImplicitParameterNode
            is_valid_start = isinstance(start_node, CallNode)
            is_valid_end = isinstance(end_node, CallNode) or (
                isinstance(edge, CallEdge) and edge.is_create and isinstance(end_node, ImplicitParameterNode)
            )

            if not is_valid_start or not is_valid_end:
                return ValidationResult.error(
                    "Call and Return edges must connect to activation boxes (CallNodes)."
                )

            # RF30: Same activation box receiving calls from multiple different callers simultaneously
            if isinstance(edge, CallEdge) and isinstance(end_node, CallNode):
                # Check existing incoming call edges
                existing_callers = [
                    e.start_node_id
                    for e in diagram.edges
                    if isinstance(e, CallEdge) and e.end_node_id == end_node.id
                ]
                if existing_callers and start_node.id not in existing_callers:
                    return ValidationResult.error(
                        "An activation box cannot receive calls from multiple different callers."
                    )

            # RF30: Flow control jump / arbitrary points fails silently without notification
            # If calling backward in time (y-coordinate less than current activation start)
            if isinstance(edge, CallEdge) and isinstance(start_node, CallNode) and isinstance(end_node, CallNode):
                if end_node.y < start_node.y:
                    return ValidationResult.silent()

            return ValidationResult.ok()

        return ValidationResult.ok()

    @staticmethod
    def validate_node_creation(
        diagram: Diagram,
        node: Node,
        parent: Optional[Node] = None,
    ) -> ValidationResult:
        from .node import FieldNode, CallNode

        # RF25: FieldNode cannot exist as loose root node in diagram: must belong to an object
        if isinstance(node, FieldNode):
            if not parent or parent.__class__.__name__ != "ObjectNode":
                return ValidationResult.error(
                    "FieldNode cannot exist as a loose root node: it must belong to an Object."
                )

        # RF30: No more than one orphan root call block (without caller) in same sequence diagram
        if isinstance(node, CallNode) and node.caller_id is None:
            from .node import CallNode as CNode
            root_calls = [
                n
                for n in diagram.nodes
                if isinstance(n, CNode) and n.caller_id is None and n.id != node.id
            ]
            if len(root_calls) >= 1:
                return ValidationResult.error(
                    "Only one root orphan call block is allowed in a Sequence Diagram."
                )

        return ValidationResult.ok()

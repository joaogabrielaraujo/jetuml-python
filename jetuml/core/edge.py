"""
Edge hierarchy and routing for JetUML.
"""

from __future__ import annotations
import math
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from .element import DiagramElement
from .geometry import Point, Rectangle


class Edge(DiagramElement):
    """Abstract base class for all edges connecting nodes."""

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        middle_label: str = "",
        start_label: str = "",
        end_label: str = "",
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(element_id)
        self.start_node_id = start_node_id
        self.end_node_id = end_node_id
        self.middle_label = middle_label
        self.start_label = start_label
        self.end_label = end_label
        self.curvature_offset: float = 0.0

    @property
    def is_self_edge(self) -> bool:
        return self.start_node_id == self.end_node_id and bool(self.start_node_id)

    @abstractmethod
    def clone(self) -> Edge:
        pass


class ClassRelationshipEdge(Edge):
    """
    Edges for Class Diagrams:
    Dependency, Inheritance, Realization, Association, Aggregation, Composition.
    """

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        relationship_type: str = "Association",
        directionality: str = "Unspecified",
        middle_label: str = "",
        start_label: str = "",
        end_label: str = "",
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(start_node_id, end_node_id, middle_label, start_label, end_label, element_id)
        self.relationship_type = relationship_type
        self.directionality = directionality  # Unspecified, Unidirectional, Bidirectional

    @property
    def generalization_type(self) -> str:
        if self.relationship_type == "Realization":
            return "Implementation"
        return "Inheritance"

    @generalization_type.setter
    def generalization_type(self, val: str) -> None:
        if val == "Implementation":
            self.relationship_type = "Realization"
        else:
            self.relationship_type = "Inheritance"

    @property
    def aggregation_type(self) -> str:
        return self.relationship_type

    @aggregation_type.setter
    def aggregation_type(self, val: str) -> None:
        if val in ("Aggregation", "Composition"):
            self.relationship_type = val

    def clone(self) -> ClassRelationshipEdge:
        e = ClassRelationshipEdge(
            self.start_node_id,
            self.end_node_id,
            self.relationship_type,
            self.directionality,
            self.middle_label,
            self.start_label,
            self.end_label,
        )
        e.curvature_offset = self.curvature_offset
        return e

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ClassRelationshipEdge",
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "relationship_type": self.relationship_type,
            "directionality": self.directionality,
            "middle_label": self.middle_label,
            "start_label": self.start_label,
            "end_label": self.end_label,
            "curvature_offset": self.curvature_offset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClassRelationshipEdge:
        e = cls(
            start_node_id=data.get("start_node_id", ""),
            end_node_id=data.get("end_node_id", ""),
            relationship_type=data.get("relationship_type", "Association"),
            directionality=data.get("directionality", "Unspecified"),
            middle_label=data.get("middle_label", ""),
            start_label=data.get("start_label", ""),
            end_label=data.get("end_label", ""),
            element_id=data.get("id"),
        )
        e.curvature_offset = data.get("curvature_offset", 0.0)
        return e


class NoteEdge(Edge):
    """Dashed line connecting a NoteNode to any element or diagram anchor point."""

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(start_node_id, end_node_id, "", "", "", element_id)

    def clone(self) -> NoteEdge:
        return NoteEdge(self.start_node_id, self.end_node_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "NoteEdge",
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NoteEdge:
        return cls(
            start_node_id=data.get("start_node_id", ""),
            end_node_id=data.get("end_node_id", ""),
            element_id=data.get("id"),
        )


class ReferenceEdge(Edge):
    """Reference from a Field's value compartment to an ObjectNode."""

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(start_node_id, end_node_id, "", "", "", element_id)

    def clone(self) -> ReferenceEdge:
        return ReferenceEdge(self.start_node_id, self.end_node_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ReferenceEdge",
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReferenceEdge:
        return cls(
            start_node_id=data.get("start_node_id", ""),
            end_node_id=data.get("end_node_id", ""),
            element_id=data.get("id"),
        )


class CollaborationEdge(Edge):
    """Collaboration edge between two ObjectNodes."""

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        middle_label: str = "",
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(start_node_id, end_node_id, middle_label, "", "", element_id)

    def clone(self) -> CollaborationEdge:
        e = CollaborationEdge(self.start_node_id, self.end_node_id, self.middle_label)
        e.curvature_offset = self.curvature_offset
        return e

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "CollaborationEdge",
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "middle_label": self.middle_label,
            "curvature_offset": self.curvature_offset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CollaborationEdge:
        e = cls(
            start_node_id=data.get("start_node_id", ""),
            end_node_id=data.get("end_node_id", ""),
            middle_label=data.get("middle_label", ""),
            element_id=data.get("id"),
        )
        e.curvature_offset = data.get("curvature_offset", 0.0)
        return e


class TransitionEdge(Edge):
    """State transition between State nodes."""

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        middle_label: str = "",
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(start_node_id, end_node_id, middle_label, "", "", element_id)

    def clone(self) -> TransitionEdge:
        e = TransitionEdge(self.start_node_id, self.end_node_id, self.middle_label)
        e.curvature_offset = self.curvature_offset
        return e

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "TransitionEdge",
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "middle_label": self.middle_label,
            "curvature_offset": self.curvature_offset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TransitionEdge:
        e = cls(
            start_node_id=data.get("start_node_id", ""),
            end_node_id=data.get("end_node_id", ""),
            middle_label=data.get("middle_label", ""),
            element_id=data.get("id"),
        )
        e.curvature_offset = data.get("curvature_offset", 0.0)
        return e


class UseCaseRelationshipEdge(Edge):
    """
    Edges for Use Case Diagrams:
    Association, Include, Extend, Generalization.
    """

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        relationship_type: str = "Association",
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(start_node_id, end_node_id, "", "", "", element_id)
        self.relationship_type = relationship_type

    @property
    def dependency_type(self) -> str:
        if self.relationship_type == "Include":
            return "Include"
        elif self.relationship_type == "Extend":
            return "Extend"
        return "None"

    @dependency_type.setter
    def dependency_type(self, val: str) -> None:
        if val in ("Include", "Extend"):
            self.relationship_type = val
        else:
            self.relationship_type = "Association"

    def clone(self) -> UseCaseRelationshipEdge:
        e = UseCaseRelationshipEdge(
            self.start_node_id,
            self.end_node_id,
            self.relationship_type,
        )
        e.middle_label = self.middle_label
        e.curvature_offset = self.curvature_offset
        return e

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "UseCaseRelationshipEdge",
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "relationship_type": self.relationship_type,
            "middle_label": self.middle_label,
            "curvature_offset": self.curvature_offset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UseCaseRelationshipEdge:
        e = cls(
            start_node_id=data.get("start_node_id", ""),
            end_node_id=data.get("end_node_id", ""),
            relationship_type=data.get("relationship_type", "Association"),
            element_id=data.get("id"),
        )
        e.middle_label = data.get("middle_label", "")
        e.curvature_offset = data.get("curvature_offset", 0.0)
        return e


class CallEdge(Edge):
    """Synchronous or asynchronous call in a sequence diagram."""

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        middle_label: str = "",
        is_create: bool = False,
        y: float = 100.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(start_node_id, end_node_id, middle_label, "", "", element_id)
        self.is_create = is_create
        self.y = y

    def clone(self) -> CallEdge:
        e = CallEdge(
            self.start_node_id,
            self.end_node_id,
            self.middle_label,
            self.is_create,
            self.y,
        )
        return e

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "CallEdge",
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "middle_label": self.middle_label,
            "is_create": self.is_create,
            "y": self.y,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CallEdge:
        return cls(
            start_node_id=data.get("start_node_id", ""),
            end_node_id=data.get("end_node_id", ""),
            middle_label=data.get("middle_label", ""),
            is_create=data.get("is_create", False),
            y=data.get("y", 100.0),
            element_id=data.get("id"),
        )


class ReturnEdge(Edge):
    """Return signal in a sequence diagram."""

    def __init__(
        self,
        start_node_id: str = "",
        end_node_id: str = "",
        middle_label: str = "",
        y: float = 120.0,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(start_node_id, end_node_id, middle_label, "", "", element_id)
        self.y = y

    def clone(self) -> ReturnEdge:
        return ReturnEdge(self.start_node_id, self.end_node_id, self.middle_label, self.y)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ReturnEdge",
            "id": self.id,
            "start_node_id": self.start_node_id,
            "end_node_id": self.end_node_id,
            "middle_label": self.middle_label,
            "y": self.y,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReturnEdge:
        return cls(
            start_node_id=data.get("start_node_id", ""),
            end_node_id=data.get("end_node_id", ""),
            middle_label=data.get("middle_label", ""),
            y=data.get("y", 120.0),
            element_id=data.get("id"),
        )


EDGE_TYPE_MAP = {
    "ClassRelationshipEdge": ClassRelationshipEdge,
    "NoteEdge": NoteEdge,
    "ReferenceEdge": ReferenceEdge,
    "CollaborationEdge": CollaborationEdge,
    "TransitionEdge": TransitionEdge,
    "UseCaseRelationshipEdge": UseCaseRelationshipEdge,
    "CallEdge": CallEdge,
    "ReturnEdge": ReturnEdge,
}

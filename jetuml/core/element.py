"""
DiagramElement base class for JetUML.
"""

from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict


class DiagramElement(ABC):
    """Abstract base class for all elements in a diagram (nodes and edges)."""

    def __init__(self, element_id: str | None = None) -> None:
        self.id: str = element_id if element_id else str(uuid.uuid4())
        self.selected: bool = False

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize element to a dictionary."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> DiagramElement:
        """Deserialize element from a dictionary."""
        pass

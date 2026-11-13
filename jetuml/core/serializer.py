"""JSON serialization and deserialization for JetUML diagrams (RF02, RNF02)."""

from __future__ import annotations
import json
from typing import Any, Dict
from .diagram import Diagram


class DiagramSerializer:
    @staticmethod
    def to_json(diagram: Diagram, indent: int = 2) -> str:
        data = diagram.to_dict()
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def from_json(json_str: str) -> Diagram:
        data = json.loads(json_str)
        return Diagram.from_dict(data)

    @staticmethod
    def save_to_file(diagram: Diagram, file_path: str) -> None:
        json_content = DiagramSerializer.to_json(diagram)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        diagram.file_path = file_path
        diagram.is_modified = False

    @staticmethod
    def load_from_file(file_path: str) -> Diagram:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        diag = DiagramSerializer.from_json(content)
        diag.file_path = file_path
        diag.is_modified = False
        return diag

"""Diagram-specific toolbars with precise order (RF07) and shortcuts (RF08)."""

from __future__ import annotations
import tkinter as tk
from typing import Callable, Dict
from ..core.diagram import DiagramType

TOOLBAR_CONFIGS = {
    DiagramType.CLASS: [
        ("Select", "Selection tool"),
        ("Class", "UML Class box"),
        ("Interface", "UML Interface box"),
        ("Package", "Package container"),
        ("Package Description", "Package description note"),
        ("Note", "UML Note box"),
        ("Dependency", "Dependency dashed arrow"),
        ("Inheritance", "Generalization triangle arrow"),
        ("Realization", "Implementation dashed triangle"),
        ("Association", "Solid association line"),
        ("Aggregation", "Hollow diamond aggregation"),
        ("Composition", "Filled diamond composition"),
        ("Note Connector", "Note connection dashed line"),
        ("To Clipboard", "Copy diagram image to clipboard"),
    ],
    DiagramType.SEQUENCE: [
        ("Select", "Selection tool"),
        ("Implicit Parameter", "Object/Lifeline container"),
        ("Note", "UML Note box"),
        ("Call", "Method call invocation"),
        ("Return", "Return message"),
        ("Note Connector", "Note connection dashed line"),
        ("To Clipboard", "Copy diagram image to clipboard"),
    ],
    DiagramType.STATE: [
        ("Select", "Selection tool"),
        ("State", "Rounded state box"),
        ("Initial State", "Initial state filled circle"),
        ("Final State", "Final state bullseye circle"),
        ("Note", "UML Note box"),
        ("Transition", "State transition arrow"),
        ("Note Connector", "Note connection dashed line"),
        ("To Clipboard", "Copy diagram image to clipboard"),
    ],
    DiagramType.OBJECT: [
        ("Select", "Selection tool"),
        ("Object", "Object instance box"),
        ("Field", "Field attribute row"),
        ("Note", "UML Note box"),
        ("Reference", "Pointer reference arrow"),
        ("Collaboration", "Collaboration message arrow"),
        ("Note Connector", "Note connection dashed line"),
        ("To Clipboard", "Copy diagram image to clipboard"),
    ],
    DiagramType.USE_CASE: [
        ("Select", "Selection tool"),
        ("Actor", "Actor stick figure"),
        ("Use Case", "Use case ellipse"),
        ("Note", "UML Note box"),
        ("Association", "Actor-UseCase communication line"),
        ("Include", "«include» relationship"),
        ("Extend", "«extend» relationship"),
        ("Generalization", "Generalization hierarchy"),
        ("Note Connector", "Note connection dashed line"),
        ("To Clipboard", "Copy diagram image to clipboard"),
    ],
}


class DiagramToolbar(tk.Frame):
    def __init__(self, parent: tk.Widget, diagram_type: DiagramType, on_tool_selected: Callable[[str], None]) -> None:
        super().__init__(parent, relief=tk.RAISED, borderwidth=1)
        self.diagram_type = diagram_type
        self.on_tool_selected = on_tool_selected
        self.active_tool: str = "Select"
        self.show_tool_hints: bool = True
        self.buttons: Dict[str, tk.Button] = {}
        self._build_tools()

    def _build_tools(self) -> None:
        tools = TOOLBAR_CONFIGS.get(self.diagram_type, [])
        shortcuts = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "A", "B", "C", "D"]

        for i, (tool_name, desc) in enumerate(tools):
            key = shortcuts[i] if i < len(shortcuts) else ""
            label_text = f"[{key}] {tool_name}" if self.show_tool_hints else key
            btn = tk.Button(
                self,
                text=label_text,
                relief=tk.SUNKEN if tool_name == self.active_tool else tk.RAISED,
                anchor="w",
                padx=6,
                pady=4,
                command=lambda t=tool_name: self.set_active_tool(t),
            )
            btn.pack(fill=tk.X, padx=2, pady=1)
            self.buttons[tool_name] = btn

    def set_active_tool(self, tool_name: str) -> None:
        self.active_tool = tool_name
        for t_name, btn in self.buttons.items():
            btn.config(relief=tk.SUNKEN if t_name == tool_name else tk.RAISED)
        self.on_tool_selected(tool_name)

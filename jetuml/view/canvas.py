"""Interactive Diagram Canvas (RF11-RF17, RF32-RF37)."""

from __future__ import annotations
import math
import tkinter as tk
from typing import Callable, Optional, Any, Dict
from ..core.geometry import Point, Rectangle
from ..core.diagram import Diagram, DiagramType
from ..core.node import (
    Node, ClassNode, InterfaceNode, PackageNode, PackageDescriptionNode,
    NoteNode, ActorNode, UseCaseNode, StateNode, InitialStateNode,
    FinalStateNode, ObjectNode, FieldNode, ImplicitParameterNode,
    CallNode, PointNode,
)
from ..core.edge import (
    Edge, ClassRelationshipEdge, NoteEdge, ReferenceEdge, CollaborationEdge,
    TransitionEdge, UseCaseRelationshipEdge, CallEdge, ReturnEdge,
)
from ..core.commands import (
    CommandStack, AddNodeCommand, AddEdgeCommand, MoveElementsCommand,
    RemoveElementsCommand,
)
from .theme import ThemeManager


NODE_TOOL_FACTORIES = {
    "Class": lambda p: ClassNode("Class", x=p.x, y=p.y),
    "Interface": lambda p: InterfaceNode("Interface", x=p.x, y=p.y),
    "Package": lambda p: PackageNode("Package", x=p.x, y=p.y),
    "Package Description": lambda p: PackageDescriptionNode("Package Description", x=p.x, y=p.y),
    "Note": lambda p: NoteNode("Note", x=p.x, y=p.y),
    "Actor": lambda p: ActorNode("Actor", x=p.x, y=p.y),
    "Use Case": lambda p: UseCaseNode("Use Case", x=p.x, y=p.y),
    "State": lambda p: StateNode("State", x=p.x, y=p.y),
    "Initial State": lambda p: InitialStateNode(x=p.x, y=p.y),
    "Final State": lambda p: FinalStateNode(x=p.x, y=p.y),
    "Object": lambda p: ObjectNode("object:Type", x=p.x, y=p.y),
    "Implicit Parameter": lambda p: ImplicitParameterNode("param:Type", x=p.x, y=p.y),
    "Call": lambda p: CallNode(x=p.x, y_top=p.y, y_bottom=p.y + 60.0),
}

EDGE_TOOL_FACTORIES = {
    "Association": lambda s, e: ClassRelationshipEdge(s, e, relationship_type="Association"),
    "Inheritance": lambda s, e: ClassRelationshipEdge(s, e, relationship_type="Inheritance"),
    "Realization": lambda s, e: ClassRelationshipEdge(s, e, relationship_type="Realization"),
    "Dependency": lambda s, e: ClassRelationshipEdge(s, e, relationship_type="Dependency"),
    "Aggregation": lambda s, e: ClassRelationshipEdge(s, e, relationship_type="Aggregation"),
    "Composition": lambda s, e: ClassRelationshipEdge(s, e, relationship_type="Composition"),
    "Transition": lambda s, e: TransitionEdge(s, e),
    "Note Connector": lambda s, e: NoteEdge(s, e),
    "Reference": lambda s, e: ReferenceEdge(s, e),
    "Collaboration": lambda s, e: CollaborationEdge(s, e),
    "Call": lambda s, e: CallEdge(s, e),
    "Return": lambda s, e: ReturnEdge(s, e),
    "Include": lambda s, e: UseCaseRelationshipEdge(s, e, relationship_type="Include"),
    "Extend": lambda s, e: UseCaseRelationshipEdge(s, e, relationship_type="Extend"),
    "Generalization": lambda s, e: UseCaseRelationshipEdge(s, e, relationship_type="Generalization"),
}


class DiagramCanvas(tk.Canvas):
    def __init__(
        self,
        parent: tk.Widget,
        diagram: Diagram,
        command_stack: CommandStack,
        on_notify: Callable[[str, bool], None],
        on_auto_edit: Callable[[Any], None],
    ) -> None:
        super().__init__(parent, bg="#ffffff", highlightthickness=0)
        self.diagram = diagram
        self.command_stack = command_stack
        self.on_notify = on_notify
        self.on_auto_edit = on_auto_edit

        self.zoom_level: int = 0
        self.zoom_factors = {-2: 0.64, -1: 0.80, 0: 1.0, 1: 1.25, 2: 1.56}
        self.show_grid: bool = True
        self.grid_spacing: float = 20.0
        self.active_tool: str = "Select"

        self.drag_start: Optional[Point] = None
        self.rubber_band_start: Optional[Point] = None
        self.is_lasso: bool = False

        self.diagram.add_change_listener(self.redraw)

        self.bind("<Button-1>", self.on_mouse_down)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.bind("<Button-3>", self.on_right_click)
        self.bind("<Double-Button-1>", self.on_double_click)

    @property
    def scale(self) -> float:
        return self.zoom_factors[self.zoom_level]

    def snap(self, val: float) -> float:
        return round(val / self.grid_spacing) * self.grid_spacing

    def redraw(self) -> None:
        self.delete("all")
        theme = ThemeManager.get_current()
        self.config(bg=theme.canvas_bg)

        if self.show_grid:
            sc = self.scale * self.grid_spacing
            w = int(self.diagram.width * self.scale)
            h = int(self.diagram.height * self.scale)
            for x in range(0, w, int(sc)):
                self.create_line(x, 0, x, h, fill=theme.grid_color)
            for y in range(0, h, int(sc)):
                self.create_line(0, y, w, y, fill=theme.grid_color)

        for edge in self.diagram.edges:
            self._draw_edge(edge, theme)

        for node in self.diagram.nodes:
            self._draw_node(node, theme)

    def _draw_node(self, node: Node, theme: Any) -> None:
        if isinstance(node, ClassNode):
            self._draw_class_node(node, theme)
        elif isinstance(node, InterfaceNode):
            self._draw_interface_node(node, theme)
        elif isinstance(node, PackageNode):
            self._draw_package_node(node, theme)
        elif isinstance(node, PackageDescriptionNode):
            self._draw_package_desc_node(node, theme)
        elif isinstance(node, NoteNode):
            self._draw_note_node(node, theme)
        elif isinstance(node, ActorNode):
            self._draw_actor_node(node, theme)
        elif isinstance(node, UseCaseNode):
            self._draw_use_case_node(node, theme)
        elif isinstance(node, StateNode):
            self._draw_state_node(node, theme)
        elif isinstance(node, InitialStateNode):
            self._draw_initial_state_node(node, theme)
        elif isinstance(node, FinalStateNode):
            self._draw_final_state_node(node, theme)
        elif isinstance(node, ObjectNode):
            self._draw_object_node(node, theme)
        elif isinstance(node, FieldNode):
            self._draw_field_node(node, theme)
        elif isinstance(node, ImplicitParameterNode):
            self._draw_implicit_parameter_node(node, theme)
        elif isinstance(node, CallNode):
            self._draw_call_node(node, theme)
        else:
            x, y, w, h = node.x * self.scale, node.y * self.scale, node.width * self.scale, node.height * self.scale
            self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke)
            if hasattr(node, "name"):
                self.create_text(x + w / 2, y + h / 2, text=getattr(node, "name"), fill=theme.text_color)

        if node.selected:
            x, y, w, h = node.x * self.scale, node.y * self.scale, node.width * self.scale, node.height * self.scale
            self.create_rectangle(x - 2, y - 2, x + w + 2, y + h + 2, outline=theme.selection_color, width=2)

    def _draw_class_node(self, node: ClassNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc

        self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)

        header_h = 28.0 * sc
        self.create_text(
            x + w / 2, y + header_h / 2,
            text=node.name,
            font=("Segoe UI", max(8, int(10 * sc)), "bold"),
            fill=theme.text_color,
        )
        self.create_line(x, y + header_h, x + w, y + header_h, fill=theme.node_stroke)

        attr_lines = node.attributes.splitlines() if node.attributes else []
        attr_h = max(1, len(attr_lines)) * 18.0 * sc + 8.0 * sc
        curr_y = y + header_h + 4.0 * sc
        line_spacing = 18.0 * sc
        font_regular = ("Segoe UI", max(8, int(9.5 * sc)))

        for line in attr_lines:
            self.create_text(
                x + 8.0 * sc, curr_y + 8.0 * sc,
                anchor="w",
                text=line,
                font=font_regular,
                fill=theme.text_color,
            )
            curr_y += line_spacing

        divider_2 = y + header_h + attr_h
        self.create_line(x, divider_2, x + w, divider_2, fill=theme.node_stroke)

        method_lines = node.methods.splitlines() if node.methods else []
        curr_y = divider_2 + 4.0 * sc
        for line in method_lines:
            self.create_text(
                x + 8.0 * sc, curr_y + 8.0 * sc,
                anchor="w",
                text=line,
                font=font_regular,
                fill=theme.text_color,
            )
            curr_y += line_spacing

    def _draw_interface_node(self, node: InterfaceNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc

        self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)

        self.create_text(
            x + w / 2, y + 10.0 * sc,
            text="«interface»",
            font=("Segoe UI", max(7, int(8.5 * sc)), "italic"),
            fill=theme.text_color,
        )
        self.create_text(
            x + w / 2, y + 24.0 * sc,
            text=node.name,
            font=("Segoe UI", max(8, int(10 * sc)), "bold"),
            fill=theme.text_color,
        )
        header_h = 36.0 * sc
        self.create_line(x, y + header_h, x + w, y + header_h, fill=theme.node_stroke)

        method_lines = node.methods.splitlines() if node.methods else []
        curr_y = y + header_h + 4.0 * sc
        line_spacing = 18.0 * sc
        font_regular = ("Segoe UI", max(8, int(9.5 * sc)))

        for line in method_lines:
            self.create_text(
                x + 8.0 * sc, curr_y + 8.0 * sc,
                anchor="w",
                text=line,
                font=font_regular,
                fill=theme.text_color,
            )
            curr_y += line_spacing

    def _draw_package_node(self, node: PackageNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc
        tab_w = min(w * 0.45, 75.0 * sc)
        tab_h = 22.0 * sc

        self.create_rectangle(x, y, x + tab_w, y + tab_h, fill=theme.panel_bg, outline=theme.node_stroke)
        self.create_rectangle(x, y + tab_h, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke)
        self.create_text(x + 6.0 * sc, y + 11.0 * sc, anchor="w", text=node.name, font=("Segoe UI", max(8, int(9 * sc)), "bold"), fill=theme.text_color)

    def _draw_package_desc_node(self, node: PackageDescriptionNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc

        self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke)
        self.create_text(x + w / 2, y + 14.0 * sc, text=node.name, font=("Segoe UI", max(8, int(9.5 * sc)), "bold"), fill=theme.text_color)
        self.create_line(x, y + 26.0 * sc, x + w, y + 26.0 * sc, fill=theme.node_stroke)
        if node.content:
            self.create_text(x + 6.0 * sc, y + 32.0 * sc, anchor="nw", text=node.content, font=("Segoe UI", max(8, int(9 * sc))), fill=theme.text_color)

    def _draw_note_node(self, node: NoteNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc
        fold = 12.0 * sc

        bg_col = "#fff9d6" if not ThemeManager.is_dark() else "#3b3a32"
        fold_col = "#f0e68c" if not ThemeManager.is_dark() else "#4f4e43"
        self.create_polygon([x, y, x + w - fold, y, x + w, y + fold, x + w, y + h, x, y + h], fill=bg_col, outline=theme.node_stroke)
        self.create_polygon([x + w - fold, y, x + w - fold, y + fold, x + w, y + fold], fill=fold_col, outline=theme.node_stroke)

        lines = node.text.splitlines() if node.text else ["Note"]
        curr_y = y + 8.0 * sc
        for line in lines:
            self.create_text(x + 8.0 * sc, curr_y, anchor="nw", text=line, font=("Segoe UI", max(8, int(9 * sc))), fill=theme.text_color)
            curr_y += 16.0 * sc

    def _draw_actor_node(self, node: ActorNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc
        cx = x + w / 2

        r = 12.0 * sc
        self.create_oval(cx - r, y, cx + r, y + 2 * r, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)
        neck_y = y + 2 * r
        crotch_y = neck_y + 24.0 * sc
        self.create_line(cx, neck_y, cx, crotch_y, fill=theme.node_stroke, width=1.5)
        arm_y = neck_y + 10.0 * sc
        self.create_line(cx - 18.0 * sc, arm_y, cx + 18.0 * sc, arm_y, fill=theme.node_stroke, width=1.5)
        leg_bottom_y = crotch_y + 22.0 * sc
        self.create_line(cx, crotch_y, cx - 14.0 * sc, leg_bottom_y, fill=theme.node_stroke, width=1.5)
        self.create_line(cx, crotch_y, cx + 14.0 * sc, leg_bottom_y, fill=theme.node_stroke, width=1.5)
        self.create_text(cx, leg_bottom_y + 12.0 * sc, text=node.name, font=("Segoe UI", max(8, int(9.5 * sc))), fill=theme.text_color)

    def _draw_use_case_node(self, node: UseCaseNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc
        self.create_oval(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)
        self.create_text(x + w / 2, y + h / 2, text=node.name, font=("Segoe UI", max(8, int(9.5 * sc))), fill=theme.text_color)

    def _draw_state_node(self, node: StateNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc
        self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)
        self.create_text(x + w / 2, y + h / 2, text=node.name, font=("Segoe UI", max(8, int(9.5 * sc))), fill=theme.text_color)

    def _draw_initial_state_node(self, node: InitialStateNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc
        fill_col = "#000000" if not ThemeManager.is_dark() else "#ffffff"
        self.create_oval(x, y, x + w, y + h, fill=fill_col, outline=theme.node_stroke)

    def _draw_final_state_node(self, node: FinalStateNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc
        fill_col = "#000000" if not ThemeManager.is_dark() else "#ffffff"
        self.create_oval(x, y, x + w, y + h, outline=theme.node_stroke, width=1.5)
        self.create_oval(x + 4 * sc, y + 4 * sc, x + w - 4 * sc, y + h - 4 * sc, fill=fill_col, outline=fill_col)

    def _draw_object_node(self, node: ObjectNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc

        self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)
        self.create_text(x + w / 2, y + 16.0 * sc, text=node.name, font=("Segoe UI", max(8, int(9.5 * sc)), "underline", "bold"), fill=theme.text_color)
        self.create_line(x, y + 28.0 * sc, x + w, y + 28.0 * sc, fill=theme.node_stroke)

    def _draw_field_node(self, node: FieldNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc

        self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke)
        mid_x = x + w / 2
        self.create_line(mid_x, y, mid_x, y + h, fill=theme.node_stroke)
        self.create_text(x + 4 * sc, y + h / 2, anchor="w", text=node.name, font=("Segoe UI", max(7, int(8.5 * sc))), fill=theme.text_color)
        self.create_text(mid_x + 4 * sc, y + h / 2, anchor="w", text=node.value, font=("Segoe UI", max(7, int(8.5 * sc))), fill=theme.text_color)

    def _draw_implicit_parameter_node(self, node: ImplicitParameterNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc

        self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)
        self.create_text(x + w / 2, y + h / 2, text=node.name, font=("Segoe UI", max(8, int(9.5 * sc))), fill=theme.text_color)

        lx = node.lifeline_x * sc
        ly1 = node.lifeline_top_y * sc
        ly2 = node.lifeline_bottom_y * sc
        self.create_line(lx, ly1, lx, ly2, fill=theme.node_stroke, dash=(4, 4), width=1.5)

    def _draw_call_node(self, node: CallNode, theme: Any) -> None:
        sc = self.scale
        x = node.x * sc
        y = node.y * sc
        w = node.width * sc
        h = node.height * sc
        self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)

    def _draw_edge(self, edge: Edge, theme: Any) -> None:
        s = self.diagram.get_node_by_id(edge.start_node_id)
        e = self.diagram.get_node_by_id(edge.end_node_id)
        if not s or not e:
            return

        p1 = s.connection_point(e.center)
        p2 = e.connection_point(s.center)
        x1, y1 = p1.x * self.scale, p1.y * self.scale
        x2, y2 = p2.x * self.scale, p2.y * self.scale
        sc = self.scale

        is_dashed = isinstance(edge, (NoteEdge, ReturnEdge)) or (
            isinstance(edge, ClassRelationshipEdge) and edge.relationship_type in ("Realization", "Dependency")
        ) or (
            isinstance(edge, UseCaseRelationshipEdge) and edge.relationship_type in ("Include", "Extend")
        )
        dash = (5, 4) if is_dashed else None

        self.create_line(x1, y1, x2, y2, fill=theme.node_stroke, width=1.5, dash=dash)

        if edge.middle_label:
            mx = (x1 + x2) / 2.0
            my = (y1 + y2) / 2.0 - 10.0 * sc
            self.create_text(mx, my, text=edge.middle_label, font=("Segoe UI", max(8, int(9 * sc))), fill=theme.text_color)
        if edge.start_label:
            sx = x1 + (x2 - x1) * 0.15
            sy = y1 + (y2 - y1) * 0.15 - 8.0 * sc
            self.create_text(sx, sy, text=edge.start_label, font=("Segoe UI", max(7, int(8.5 * sc))), fill=theme.text_color)
        if edge.end_label:
            ex = x2 - (x2 - x1) * 0.15
            ey = y2 - (y2 - y1) * 0.15 - 8.0 * sc
            self.create_text(ex, ey, text=edge.end_label, font=("Segoe UI", max(7, int(8.5 * sc))), fill=theme.text_color)

        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist > 1e-4:
            ux = dx / dist
            uy = dy / dist
            perp_x = -uy
            perp_y = ux

            if isinstance(edge, ClassRelationshipEdge):
                if edge.relationship_type in ("Inheritance", "Realization"):
                    size = 12.0 * sc
                    base_x = x2 - ux * size
                    base_y = y2 - uy * size
                    w_half = 6.0 * sc
                    p_left = (base_x + perp_x * w_half, base_y + perp_y * w_half)
                    p_right = (base_x - perp_x * w_half, base_y - perp_y * w_half)
                    self.create_polygon([x2, y2, p_left[0], p_left[1], p_right[0], p_right[1]], fill=theme.canvas_bg, outline=theme.node_stroke, width=1.5)
                elif edge.relationship_type in ("Aggregation", "Composition"):
                    size = 14.0 * sc
                    tip_x = x1 + ux * size
                    tip_y = y1 + uy * size
                    mid_x = x1 + ux * (size / 2.0)
                    mid_y = y1 + uy * (size / 2.0)
                    w_half = 5.0 * sc
                    p_left = (mid_x + perp_x * w_half, mid_y + perp_y * w_half)
                    p_right = (mid_x - perp_x * w_half, mid_y - perp_y * w_half)
                    fill_col = theme.node_stroke if edge.relationship_type == "Composition" else theme.canvas_bg
                    self.create_polygon([x1, y1, p_left[0], p_left[1], tip_x, tip_y, p_right[0], p_right[1]], fill=fill_col, outline=theme.node_stroke, width=1.5)
                elif edge.relationship_type == "Dependency" or edge.directionality != "Unspecified":
                    size = 10.0 * sc
                    w_half = 5.0 * sc
                    base_x = x2 - ux * size
                    base_y = y2 - uy * size
                    self.create_line(base_x + perp_x * w_half, base_y + perp_y * w_half, x2, y2, fill=theme.node_stroke, width=1.5)
                    self.create_line(base_x - perp_x * w_half, base_y - perp_y * w_half, x2, y2, fill=theme.node_stroke, width=1.5)
            elif isinstance(edge, (ReferenceEdge, CollaborationEdge, TransitionEdge, CallEdge)):
                size = 10.0 * sc
                w_half = 5.0 * sc
                base_x = x2 - ux * size
                base_y = y2 - uy * size
                self.create_line(base_x + perp_x * w_half, base_y + perp_y * w_half, x2, y2, fill=theme.node_stroke, width=1.5)
                self.create_line(base_x - perp_x * w_half, base_y - perp_y * w_half, x2, y2, fill=theme.node_stroke, width=1.5)
            elif isinstance(edge, UseCaseRelationshipEdge):
                if edge.relationship_type == "Generalization":
                    size = 12.0 * sc
                    base_x = x2 - ux * size
                    base_y = y2 - uy * size
                    w_half = 6.0 * sc
                    p_left = (base_x + perp_x * w_half, base_y + perp_y * w_half)
                    p_right = (base_x - perp_x * w_half, base_y - perp_y * w_half)
                    self.create_polygon([x2, y2, p_left[0], p_left[1], p_right[0], p_right[1]], fill=theme.canvas_bg, outline=theme.node_stroke, width=1.5)
                elif edge.relationship_type in ("Include", "Extend"):
                    size = 10.0 * sc
                    w_half = 5.0 * sc
                    base_x = x2 - ux * size
                    base_y = y2 - uy * size
                    self.create_line(base_x + perp_x * w_half, base_y + perp_y * w_half, x2, y2, fill=theme.node_stroke, width=1.5)
                    self.create_line(base_x - perp_x * w_half, base_y - perp_y * w_half, x2, y2, fill=theme.node_stroke, width=1.5)

    def on_mouse_down(self, event: tk.Event) -> None:
        p = Point(event.x / self.scale, event.y / self.scale)
        p_snapped = Point(self.snap(p.x), self.snap(p.y))

        if self.active_tool in NODE_TOOL_FACTORIES:
            node = NODE_TOOL_FACTORIES[self.active_tool](p_snapped)
            self.command_stack.execute(AddNodeCommand(self.diagram, node))
            self.on_auto_edit(node)
        elif self.active_tool == "Field":
            hit_obj = self.diagram.find_node_at(p)
            if hit_obj and isinstance(hit_obj, ObjectNode):
                field_y = hit_obj.y + 30.0 + len(hit_obj.field_ids) * 24.0
                f = FieldNode("field", "value", parent_object_id=hit_obj.id, x=hit_obj.x, y=field_y, width=hit_obj.width)
                self.command_stack.execute(AddNodeCommand(self.diagram, f, parent=hit_obj))
                self.on_auto_edit(f)
            else:
                self.on_notify("Field must be added onto an Object.", False)
        elif self.active_tool == "Select":
            hit_node = self.diagram.find_node_at(p)
            if hit_node:
                if not (event.state & 0x0004):
                    self.diagram.clear_selection()
                hit_node.selected = not hit_node.selected
                self.drag_start = p
            else:
                if not (event.state & 0x0004):
                    self.diagram.clear_selection()
                self.is_lasso = True
                self.drag_start = p
        else:
            self.rubber_band_start = p

        self.redraw()

    def on_mouse_drag(self, event: tk.Event) -> None:
        p = Point(event.x / self.scale, event.y / self.scale)
        if self.active_tool == "Select" and self.drag_start and not self.is_lasso:
            dx = self.snap(p.x - self.drag_start.x)
            dy = self.snap(p.y - self.drag_start.y)
            if dx != 0 or dy != 0:
                selected_ids = [n.id for n in self.diagram.selected_elements if hasattr(n, "id")]
                self.command_stack.execute(MoveElementsCommand(self.diagram, selected_ids, dx, dy))
                self.drag_start = p
        elif self.rubber_band_start:
            self.redraw()
            theme = ThemeManager.get_current()
            self.create_line(
                self.rubber_band_start.x * self.scale,
                self.rubber_band_start.y * self.scale,
                event.x,
                event.y,
                fill=theme.rubberband_color,
                dash=(4, 4),
            )

    def on_mouse_up(self, event: tk.Event) -> None:
        p = Point(event.x / self.scale, event.y / self.scale)
        if self.rubber_band_start:
            start_node = self.diagram.find_node_at(self.rubber_band_start)
            end_node = self.diagram.find_node_at(p)
            if start_node and end_node:
                factory = EDGE_TOOL_FACTORIES.get(self.active_tool)
                if factory:
                    edge = factory(start_node.id, end_node.id)
                    res = self.diagram.add_edge(edge)
                    if not res.is_valid and not res.silent_failure:
                        self.on_notify(res.error_message or "Invalid connection.", False)

            self.rubber_band_start = None
            self.redraw()
        self.drag_start = None
        self.is_lasso = False

    def on_double_click(self, event: tk.Event) -> None:
        p = Point(event.x / self.scale, event.y / self.scale)
        node = self.diagram.find_node_at(p)
        if node:
            self.on_auto_edit(node)

    def on_right_click(self, event: tk.Event) -> None:
        menu = tk.Menu(self, tearoff=0)
        from .toolbar import TOOLBAR_CONFIGS
        for name, _ in TOOLBAR_CONFIGS.get(self.diagram.diagram_type, []):
            menu.add_command(label=name, command=lambda t=name: self.set_tool(t))
        menu.tk_popup(event.x_root, event.y_root)

    def set_tool(self, tool_name: str) -> None:
        self.active_tool = tool_name


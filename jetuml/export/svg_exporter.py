"""Pure Python SVG Exporter for JetUML (RF04)."""

from __future__ import annotations
import html
from typing import TYPE_CHECKING
from ..core.geometry import Rectangle, Point
from ..core.node import (
    ClassNode, InterfaceNode, PackageNode, PackageDescriptionNode,
    NoteNode, ActorNode, UseCaseNode, StateNode, InitialStateNode,
    FinalStateNode, ObjectNode, FieldNode, ImplicitParameterNode, CallNode,
)
from ..core.edge import (
    ClassRelationshipEdge, NoteEdge, ReferenceEdge, CollaborationEdge,
    TransitionEdge, UseCaseRelationshipEdge, CallEdge, ReturnEdge,
)

if TYPE_CHECKING:
    from ..core.diagram import Diagram


class SvgExporter:
    @staticmethod
    def export(diagram: Diagram) -> str:
        bounds = diagram.content_bounds()
        w = max(400.0, bounds.width + 40.0)
        h = max(300.0, bounds.height + 40.0)

        svg = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{bounds.x-20} {bounds.y-20} {w} {h}">',
            '  <defs>',
            '    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">',
            '      <path d="M0,0 L0,6 L9,3 z" fill="#000" />',
            '    </marker>',
            '    <marker id="openArrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">',
            '      <path d="M0,0 L9,5 L0,10" fill="none" stroke="#000" stroke-width="1.5" />',
            '    </marker>',
            '    <marker id="triangle" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto">',
            '      <path d="M0,0 L12,6 L0,12 z" fill="#fff" stroke="#000" stroke-width="1.2" />',
            '    </marker>',
            '    <marker id="diamond" markerWidth="14" markerHeight="10" refX="13" refY="5" orient="auto">',
            '      <path d="M0,5 L7,0 L14,5 L7,10 z" fill="#fff" stroke="#000" stroke-width="1.2" />',
            '    </marker>',
            '    <marker id="filledDiamond" markerWidth="14" markerHeight="10" refX="13" refY="5" orient="auto">',
            '      <path d="M0,5 L7,0 L14,5 L7,10 z" fill="#000" />',
            '    </marker>',
            '  </defs>',
            '  <style>',
            '    text { font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; }',
            '    .kw { font-size: 11px; fill: #555; }',
            '    .label { font-size: 12px; fill: #222; }',
            '  </style>',
            f'  <rect x="{bounds.x-20}" y="{bounds.y-20}" width="{w}" height="{h}" fill="#ffffff" />',
        ]

        for edge in diagram.edges:
            start_node = diagram.get_node_by_id(edge.start_node_id)
            end_node = diagram.get_node_by_id(edge.end_node_id)
            if not start_node or not end_node:
                continue

            p1 = start_node.connection_point(end_node.center)
            p2 = end_node.connection_point(start_node.center)

            stroke_dash = 'stroke-dasharray="5,4"' if isinstance(edge, (NoteEdge, ReturnEdge)) or (
                isinstance(edge, ClassRelationshipEdge) and edge.relationship_type in ("Realization", "Dependency")
            ) or (
                isinstance(edge, UseCaseRelationshipEdge) and edge.relationship_type in ("Include", "Extend")
            ) else ""

            marker = ""
            if isinstance(edge, ClassRelationshipEdge):
                if edge.relationship_type in ("Inheritance", "Realization"):
                    marker = 'marker-end="url(#triangle)"'
                elif edge.relationship_type == "Aggregation":
                    marker = 'marker-start="url(#diamond)"'
                elif edge.relationship_type == "Composition":
                    marker = 'marker-start="url(#filledDiamond)"'
                elif edge.relationship_type == "Dependency" or edge.directionality != "Unspecified":
                    marker = 'marker-end="url(#openArrow)"'
            elif isinstance(edge, UseCaseRelationshipEdge):
                if edge.relationship_type == "Generalization":
                    marker = 'marker-end="url(#triangle)"'
                elif edge.relationship_type in ("Include", "Extend"):
                    marker = 'marker-end="url(#openArrow)"'
            elif isinstance(edge, (ReferenceEdge, CollaborationEdge, TransitionEdge, CallEdge)):
                marker = 'marker-end="url(#arrow)"'

            svg.append(f'  <line x1="{p1.x}" y1="{p1.y}" x2="{p2.x}" y2="{p2.y}" stroke="#000" stroke-width="1.3" {stroke_dash} {marker} />')

            if edge.middle_label:
                mx = (p1.x + p2.x) / 2.0
                my = (p1.y + p2.y) / 2.0 - 6.0
                svg.append(f'  <text x="{mx}" y="{my}" text-anchor="middle" class="label">{html.escape(edge.middle_label)}</text>')

        for node in diagram.nodes:
            if isinstance(node, ClassNode):
                svg.append(f'  <rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" fill="#fdfdfd" stroke="#000" stroke-width="1.2" />')
                svg.append(f'  <text x="{node.x + node.width/2}" y="{node.y + 20}" font-weight="bold" text-anchor="middle">{html.escape(node.name)}</text>')
                svg.append(f'  <line x1="{node.x}" y1="{node.y + 28}" x2="{node.x + node.width}" y2="{node.y + 28}" stroke="#000" />')
                ay = node.y + 44
                for attr in node.attributes.splitlines():
                    svg.append(f'  <text x="{node.x + 8}" y="{ay}">{html.escape(attr)}</text>')
                    ay += 16
                mid_y = ay + 4
                svg.append(f'  <line x1="{node.x}" y1="{mid_y}" x2="{node.x + node.width}" y2="{mid_y}" stroke="#000" />')
                my = mid_y + 16
                for meth in node.methods.splitlines():
                    svg.append(f'  <text x="{node.x + 8}" y="{my}">{html.escape(meth)}</text>')
                    my += 16
            elif isinstance(node, NoteNode):
                x, y, w, h = node.x, node.y, node.width, node.height
                svg.append(f'  <polygon points="{x},{y} {x+w-12},{y} {x+w},{y+12} {x+w},{y+h} {x},{y+h}" fill="#fff9d6" stroke="#000" stroke-width="1.2" />')
                svg.append(f'  <polyline points="{x+w-12},{y} {x+w-12},{y+12} {x+w},{y+12}" fill="#f0e68c" stroke="#000" />')
                ty = y + 20
                for line in node.text.splitlines():
                    svg.append(f'  <text x="{x + 8}" y="{ty}">{html.escape(line)}</text>')
                    ty += 16
            elif isinstance(node, UseCaseNode):
                cx, cy = node.x + node.width / 2, node.y + node.height / 2
                rx, ry = node.width / 2, node.height / 2
                svg.append(f'  <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#ffffff" stroke="#000" stroke-width="1.3" />')
                svg.append(f'  <text x="{cx}" y="{cy + 5}" text-anchor="middle">{html.escape(node.name)}</text>')
            elif isinstance(node, ActorNode):
                cx = node.x + node.width / 2
                svg.append(f'  <circle cx="{cx}" cy="{node.y + 15}" r="12" fill="#fff" stroke="#000" stroke-width="1.4" />')
                svg.append(f'  <line x1="{cx}" y1="{node.y + 27}" x2="{cx}" y2="{node.y + 55}" stroke="#000" stroke-width="1.4" />')
                svg.append(f'  <line x1="{cx - 20}" y1="{node.y + 38}" x2="{cx + 20}" y2="{node.y + 38}" stroke="#000" stroke-width="1.4" />')
                svg.append(f'  <line x1="{cx}" y1="{node.y + 55}" x2="{cx - 15}" y2="{node.y + 80}" stroke="#000" stroke-width="1.4" />')
                svg.append(f'  <line x1="{cx}" y1="{node.y + 55}" x2="{cx + 15}" y2="{node.y + 80}" stroke="#000" stroke-width="1.4" />')
                svg.append(f'  <text x="{cx}" y="{node.y + 96}" text-anchor="middle">{html.escape(node.name)}</text>')
            elif isinstance(node, StateNode):
                svg.append(f'  <rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" rx="12" ry="12" fill="#ffffff" stroke="#000" stroke-width="1.3" />')
                svg.append(f'  <text x="{node.x + node.width/2}" y="{node.y + node.height/2 + 5}" text-anchor="middle">{html.escape(node.name)}</text>')
            elif isinstance(node, InitialStateNode):
                cx, cy = node.x + 12, node.y + 12
                svg.append(f'  <circle cx="{cx}" cy="{cy}" r="11" fill="#000" />')
            elif isinstance(node, FinalStateNode):
                cx, cy = node.x + 13, node.y + 13
                svg.append(f'  <circle cx="{cx}" cy="{cy}" r="12" fill="#fff" stroke="#000" stroke-width="1.4" />')
                svg.append(f'  <circle cx="{cx}" cy="{cy}" r="7" fill="#000" />')
            elif isinstance(node, ImplicitParameterNode):
                svg.append(f'  <rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" fill="#fff" stroke="#000" stroke-width="1.2" />')
                svg.append(f'  <text x="{node.x + node.width/2}" y="{node.y + 24}" text-anchor="middle">{html.escape(node.name)}</text>')
                lx = node.lifeline_x
                svg.append(f'  <line x1="{lx}" y1="{node.lifeline_top_y}" x2="{lx}" y2="{node.lifeline_bottom_y}" stroke="#000" stroke-width="1.2" stroke-dasharray="4,4" />')
            elif isinstance(node, CallNode):
                svg.append(f'  <rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" fill="#ffffff" stroke="#000" stroke-width="1.2" />')
            elif isinstance(node, ObjectNode):
                svg.append(f'  <rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" fill="#ffffff" stroke="#000" stroke-width="1.2" />')
                svg.append(f'  <text x="{node.x + node.width/2}" y="{node.y + 20}" text-decoration="underline" text-anchor="middle">{html.escape(node.name)}</text>')
                svg.append(f'  <line x1="{node.x}" y1="{node.y + 28}" x2="{node.x + node.width}" y2="{node.y + 28}" stroke="#000" />')
            elif isinstance(node, FieldNode):
                svg.append(f'  <rect x="{node.x}" y="{node.y}" width="{node.width}" height="{node.height}" fill="#f9f9f9" stroke="#999" />')
                svg.append(f'  <text x="{node.x + 6}" y="{node.y + 16}">{html.escape(node.name)}</text>')
                svg.append(f'  <text x="{node.x + node.width/2 + 6}" y="{node.y + 16}">{html.escape(node.value)}</text>')

        svg.append('</svg>')
        return "\n".join(svg)

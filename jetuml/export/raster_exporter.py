"""Raster export (PNG and JPEG) using Pillow (RF04)."""

from __future__ import annotations
from typing import TYPE_CHECKING
from PIL import Image, ImageDraw, ImageFont
from ..core.node import ClassNode, InterfaceNode, NoteNode

if TYPE_CHECKING:
    from ..core.diagram import Diagram


class RasterExporter:
    @staticmethod
    def render_to_image(diagram: Diagram) -> Image.Image:
        bounds = diagram.content_bounds()
        w = int(max(400, bounds.width + 40))
        h = int(max(300, bounds.height + 40))

        img = Image.new("RGB", (w, h), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 13)
            font_bold = ImageFont.truetype("arialbd.ttf", 13)
        except Exception:
            font = ImageFont.load_default()
            font_bold = font

        ox = bounds.x - 20
        oy = bounds.y - 20

        for edge in diagram.edges:
            s = diagram.get_node_by_id(edge.start_node_id)
            e = diagram.get_node_by_id(edge.end_node_id)
            if not s or not e:
                continue
            p1 = s.connection_point(e.center)
            p2 = e.connection_point(s.center)
            draw.line([(p1.x - ox, p1.y - oy), (p2.x - ox, p2.y - oy)], fill=(0, 0, 0), width=2)
            if edge.middle_label:
                mx = (p1.x + p2.x) / 2.0 - ox
                my = (p1.y + p2.y) / 2.0 - oy - 14
                draw.text((mx, my), edge.middle_label, fill=(0, 0, 0), font=font)

        for node in diagram.nodes:
            x = node.x - ox
            y = node.y - oy
            w_n = node.width
            h_n = node.height
            if isinstance(node, ClassNode):
                draw.rectangle([x, y, x + w_n, y + h_n], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
                draw.text((x + 10, y + 6), node.name, fill=(0, 0, 0), font=font_bold)
                header_y = y + 26
                draw.line([(x, header_y), (x + w_n, header_y)], fill=(0, 0, 0), width=1)
                curr_y = header_y + 4
                attr_lines = node.attributes.splitlines() if node.attributes else []
                for attr in attr_lines:
                    draw.text((x + 8, curr_y), attr, fill=(0, 0, 0), font=font)
                    curr_y += 16
                div_y = header_y + max(1, len(attr_lines)) * 16 + 6
                draw.line([(x, div_y), (x + w_n, div_y)], fill=(0, 0, 0), width=1)
                curr_y = div_y + 4
                for meth in (node.methods.splitlines() if node.methods else []):
                    draw.text((x + 8, curr_y), meth, fill=(0, 0, 0), font=font)
                    curr_y += 16
            elif isinstance(node, InterfaceNode):
                draw.rectangle([x, y, x + w_n, y + h_n], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
                draw.text((x + 10, y + 4), "«interface»", fill=(80, 80, 80), font=font)
                draw.text((x + 10, y + 18), node.name, fill=(0, 0, 0), font=font_bold)
                header_y = y + 36
                draw.line([(x, header_y), (x + w_n, header_y)], fill=(0, 0, 0), width=1)
                curr_y = header_y + 4
                for meth in (node.methods.splitlines() if node.methods else []):
                    draw.text((x + 8, curr_y), meth, fill=(0, 0, 0), font=font)
                    curr_y += 16
            elif isinstance(node, NoteNode):
                draw.rectangle([x, y, x + w_n, y + h_n], fill=(255, 253, 220), outline=(0, 0, 0), width=2)
                curr_y = y + 6
                for line in (node.text.splitlines() if node.text else ["Note"]):
                    draw.text((x + 8, curr_y), line, fill=(0, 0, 0), font=font)
                    curr_y += 16
            else:
                draw.rectangle([x, y, x + w_n, y + h_n], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
                if hasattr(node, "name"):
                    draw.text((x + 10, y + 8), getattr(node, "name"), fill=(0, 0, 0), font=font_bold)
                elif hasattr(node, "text"):
                    draw.text((x + 8, y + 8), getattr(node, "text"), fill=(0, 0, 0), font=font)

        return img

    @staticmethod
    def export_to_file(diagram: Diagram, file_path: str, format_name: str = "PNG") -> None:
        img = RasterExporter.render_to_image(diagram)
        img.save(file_path, format=format_name.upper())

import unittest
from jetuml.core.diagram import Diagram, DiagramType
from jetuml.core.node import ClassNode, InterfaceNode, NoteNode
from jetuml.core.commands import CommandStack, EditPropertiesCommand
from jetuml.export.raster_exporter import RasterExporter
from jetuml.export.svg_exporter import SvgExporter


class TestClassNodeProperties(unittest.TestCase):
    def test_class_node_auto_bounds_update(self):
        c = ClassNode("User")
        initial_h = c.height
        initial_w = c.width

        # Add multiple attributes and methods
        c.attributes = "- id: int\n- name: str\n- email: str\n- role: str"
        c.methods = "+ get_id(): int\n+ set_name(name: str): void\n+ authenticate(token: str): bool"

        self.assertGreater(c.height, initial_h)
        self.assertGreater(c.width, initial_w)

    def test_edit_properties_command_undo_redo(self):
        d = Diagram(DiagramType.CLASS)
        stack = CommandStack(d)
        c = ClassNode("Order")
        d.add_node(c)

        old_props = {"name": c.name, "attributes": c.attributes, "methods": c.methods}
        new_props = {
            "name": "OrderService",
            "attributes": "- total: float\n- status: str",
            "methods": "+ calculate_tax(): float",
        }

        cmd = EditPropertiesCommand(d, c, old_props, new_props)
        stack.execute(cmd)

        self.assertEqual(c.name, "OrderService")
        self.assertEqual(c.attributes, "- total: float\n- status: str")
        self.assertEqual(c.methods, "+ calculate_tax(): float")

        # Test Undo
        self.assertTrue(stack.undo())
        self.assertEqual(c.name, "Order")
        self.assertEqual(c.attributes, "")
        self.assertEqual(c.methods, "")

        # Test Redo
        self.assertTrue(stack.redo())
        self.assertEqual(c.name, "OrderService")
        self.assertEqual(c.attributes, "- total: float\n- status: str")
        self.assertEqual(c.methods, "+ calculate_tax(): float")

    def test_interface_node_bounds(self):
        iface = InterfaceNode("Repository")
        h1 = iface.height
        iface.methods = "+ find_by_id(id: int): Any\n+ save(entity: Any): void\n+ delete(id: int): void"
        self.assertGreater(iface.height, h1)

    def test_svg_and_raster_export_with_attributes_and_methods(self):
        d = Diagram(DiagramType.CLASS)
        c = ClassNode("User", attributes="- email: str", methods="+ login(): bool")
        d.add_node(c)

        svg = SvgExporter.export(d)
        self.assertIn("User", svg)
        self.assertIn("- email: str", svg)
        self.assertIn("+ login(): bool", svg)

        img = RasterExporter.render_to_image(d)
        self.assertIsNotNone(img)
        self.assertGreater(img.width, 100)
        self.assertGreater(img.height, 100)


    def test_load_example_class_diagram(self):
        from jetuml.core.serializer import DiagramSerializer
        import os
        example_path = os.path.join(os.path.dirname(__file__), "..", "examples", "class_diagram.json")
        if os.path.exists(example_path):
            diag = DiagramSerializer.load_from_file(example_path)
            self.assertEqual(len(diag.nodes), 1)
            node = diag.nodes[0]
            self.assertIsInstance(node, ClassNode)
            self.assertEqual(node.name, "User")
            self.assertIn("email", node.attributes)
            self.assertIn("login", node.methods)


if __name__ == "__main__":
    unittest.main()


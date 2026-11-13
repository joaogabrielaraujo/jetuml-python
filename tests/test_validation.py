import unittest
from jetuml.core.diagram import Diagram, DiagramType
from jetuml.core.node import ClassNode, FieldNode, ObjectNode, StateNode, InitialStateNode, FinalStateNode, CallNode, ImplicitParameterNode
from jetuml.core.edge import ClassRelationshipEdge, TransitionEdge, CallEdge

class TestValidation(unittest.TestCase):
    def test_class_prevent_duplicate_edge(self):
        d = Diagram(DiagramType.CLASS)
        c1 = ClassNode("A")
        c2 = ClassNode("B")
        d.add_node(c1)
        d.add_node(c2)
        e1 = ClassRelationshipEdge(c1.id, c2.id, "Association")
        self.assertTrue(d.add_edge(e1).is_valid)
        e2 = ClassRelationshipEdge(c1.id, c2.id, "Association")
        self.assertFalse(d.add_edge(e2).is_valid)

    def test_class_prevent_direct_cycles(self):
        d = Diagram(DiagramType.CLASS)
        c1 = ClassNode("A")
        c2 = ClassNode("B")
        d.add_node(c1)
        d.add_node(c2)
        d.add_edge(ClassRelationshipEdge(c1.id, c2.id, "Inheritance"))
        self.assertFalse(d.add_edge(ClassRelationshipEdge(c2.id, c1.id, "Inheritance")).is_valid)

    def test_object_field_cannot_exist_as_root(self):
        d = Diagram(DiagramType.OBJECT)
        f = FieldNode("name", "val")
        self.assertFalse(d.add_node(f).is_valid)
        obj = ObjectNode("o:Obj")
        d.add_node(obj)
        self.assertTrue(d.add_node(f, parent=obj).is_valid)

if __name__ == "__main__":
    unittest.main()

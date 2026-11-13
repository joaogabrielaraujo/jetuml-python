import unittest
from jetuml.core.diagram import Diagram, DiagramType
from jetuml.core.node import ClassNode
from jetuml.core.commands import CommandStack, AddNodeCommand, MoveElementsCommand

class TestCommands(unittest.TestCase):
    def test_undo_redo(self):
        d = Diagram(DiagramType.CLASS)
        stack = CommandStack(d)
        node = ClassNode("A")
        stack.execute(AddNodeCommand(d, node))
        self.assertEqual(len(d.nodes), 1)
        stack.undo()
        self.assertEqual(len(d.nodes), 0)
        stack.redo()
        self.assertEqual(len(d.nodes), 1)

if __name__ == "__main__":
    unittest.main()

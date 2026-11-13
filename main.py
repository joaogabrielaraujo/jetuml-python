"""Entry point for JetUML."""

import tkinter as tk
from jetuml.view.app import JetUMLApp


def main() -> None:
    root = tk.Tk()
    app = JetUMLApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

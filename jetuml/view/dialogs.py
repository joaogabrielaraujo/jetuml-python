"""Modal dialogs for Properties, Fonts, Diagram Size, and Durations (RF20, RF22, RF23, RF38, RF39, RF42)."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional
from ..core.node import FieldNode, CallNode


class PropertiesDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, element: Any, on_save: Callable[[Dict[str, Any]], None]) -> None:
        super().__init__(parent)
        self.element = element
        self.on_save = on_save
        self.title(f"Properties — {element.__class__.__name__}")
        self.geometry("420x460")
        self.transient(parent)
        self.grab_set()

        self.fields: Dict[str, tk.Widget] = {}
        self._build_ui()

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-q>", self._insert_stereotype)
        self.bind("<Control-Q>", self._insert_stereotype)

    def _insert_stereotype(self, event: tk.Event) -> str:
        widget = self.focus_get()
        if isinstance(widget, tk.Entry):
            idx = widget.index(tk.INSERT)
            widget.insert(idx, "«»")
            widget.icursor(idx + 1)
        elif isinstance(widget, tk.Text):
            idx = widget.index(tk.INSERT)
            widget.insert(idx, "«»")
            widget.mark_set(tk.INSERT, f"{idx}+1c")
        return "break"

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        row = 0
        elem = self.element

        if hasattr(elem, "name") and not isinstance(elem, FieldNode):
            ttk.Label(main, text="Name:").grid(row=row, column=0, sticky="w", pady=4)
            ent = ttk.Entry(main, width=35)
            ent.insert(0, elem.name)
            ent.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["name"] = ent
            row += 1

        if hasattr(elem, "attributes"):
            ttk.Label(main, text="Attributes:").grid(row=row, column=0, sticky="nw", pady=4)
            txt = tk.Text(main, width=32, height=6)
            txt.insert("1.0", elem.attributes)
            txt.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["attributes"] = txt
            row += 1

        if hasattr(elem, "methods"):
            ttk.Label(main, text="Methods:").grid(row=row, column=0, sticky="nw", pady=4)
            txt = tk.Text(main, width=32, height=6)
            txt.insert("1.0", elem.methods)
            txt.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["methods"] = txt
            row += 1

        if isinstance(elem, FieldNode):
            ttk.Label(main, text="Field Name:").grid(row=row, column=0, sticky="w", pady=4)
            ent1 = ttk.Entry(main, width=35)
            ent1.insert(0, elem.name)
            ent1.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["name"] = ent1
            row += 1

            ttk.Label(main, text="Value:").grid(row=row, column=0, sticky="w", pady=4)
            ent2 = ttk.Entry(main, width=35)
            ent2.insert(0, elem.value)
            ent2.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["value"] = ent2
            row += 1

        if hasattr(elem, "text"):
            ttk.Label(main, text="Note Text:").grid(row=row, column=0, sticky="nw", pady=4)
            txt = tk.Text(main, width=32, height=8)
            txt.insert("1.0", elem.text)
            txt.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["text"] = txt
            row += 1

        if isinstance(elem, CallNode):
            self.open_bottom_var = tk.BooleanVar(value=elem.open_bottom)
            chk = ttk.Checkbutton(main, text="Open Bottom (Incomplete sequence)", variable=self.open_bottom_var)
            chk.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
            row += 1

        if hasattr(elem, "middle_label"):
            ttk.Label(main, text="Middle Label:").grid(row=row, column=0, sticky="w", pady=4)
            ent = ttk.Entry(main, width=35)
            ent.insert(0, elem.middle_label)
            ent.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["middle_label"] = ent
            row += 1

        if hasattr(elem, "start_label"):
            ttk.Label(main, text="Start Label:").grid(row=row, column=0, sticky="w", pady=4)
            ent = ttk.Entry(main, width=35)
            ent.insert(0, elem.start_label)
            ent.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["start_label"] = ent
            row += 1

        if hasattr(elem, "end_label"):
            ttk.Label(main, text="End Label:").grid(row=row, column=0, sticky="w", pady=4)
            ent = ttk.Entry(main, width=35)
            ent.insert(0, elem.end_label)
            ent.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["end_label"] = ent
            row += 1

        if hasattr(elem, "directionality"):
            ttk.Label(main, text="Directionality:").grid(row=row, column=0, sticky="w", pady=4)
            cb = ttk.Combobox(main, values=["Unspecified", "Unidirectional", "Bidirectional"], state="readonly")
            cb.set(elem.directionality)
            cb.grid(row=row, column=1, sticky="ew", pady=4)
            self.fields["directionality"] = cb
            row += 1

        btn_box = ttk.Frame(main)
        btn_box.grid(row=row + 1, column=0, columnspan=2, pady=16, sticky="e")
        ttk.Button(btn_box, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_box, text="OK", command=self._apply).pack(side=tk.RIGHT, padx=4)

    def _apply(self) -> None:
        res: Dict[str, Any] = {}
        for key, widget in self.fields.items():
            if isinstance(widget, ttk.Entry):
                res[key] = widget.get()
            elif isinstance(widget, tk.Text):
                res[key] = widget.get("1.0", "end-1c")
            elif isinstance(widget, ttk.Combobox):
                res[key] = widget.get()

        if hasattr(self, "open_bottom_var"):
            res["open_bottom"] = self.open_bottom_var.get()

        self.on_save(res)
        self.destroy()


class DiagramSizeDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, current_w: float, current_h: float, on_confirm: Callable[[float, float], None]) -> None:
        super().__init__(parent)
        self.title("Set Diagram Size")
        self.geometry("300x180")
        self.transient(parent)
        self.grab_set()

        ttk.Label(self, text="Width (250 - 4000):").pack(pady=4)
        self.ent_w = ttk.Entry(self)
        self.ent_w.insert(0, str(int(current_w)))
        self.ent_w.pack(pady=2)

        ttk.Label(self, text="Height (250 - 4000):").pack(pady=4)
        self.ent_h = ttk.Entry(self)
        self.ent_h.insert(0, str(int(current_h)))
        self.ent_h.pack(pady=2)

        bbox = ttk.Frame(self)
        bbox.pack(pady=10)
        ttk.Button(bbox, text="Restore Defaults", command=lambda: on_confirm(1200.0, 800.0) or self.destroy()).pack(side=tk.LEFT, padx=4)
        ttk.Button(bbox, text="OK", command=self._ok).pack(side=tk.LEFT, padx=4)
        self.on_confirm = on_confirm

    def _ok(self) -> None:
        try:
            w = max(250.0, min(4000.0, float(self.ent_w.get())))
            h = max(250.0, min(4000.0, float(self.ent_h.get())))
            self.on_confirm(w, h)
            self.destroy()
        except ValueError:
            pass


class NotificationDurationDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, current_val: float, on_confirm: Callable[[float], None]) -> None:
        super().__init__(parent)
        self.title("Notification Duration")
        self.geometry("280x140")
        self.transient(parent)
        self.grab_set()

        ttk.Label(self, text="Duration (0 to 10 seconds):").pack(pady=6)
        self.scale = ttk.Scale(self, from_=0, to=10, value=current_val)
        self.scale.pack(fill=tk.X, padx=20, pady=4)

        bbox = ttk.Frame(self)
        bbox.pack(pady=10)
        ttk.Button(bbox, text="Restore Default (5s)", command=lambda: on_confirm(5.0) or self.destroy()).pack(side=tk.LEFT, padx=4)
        ttk.Button(bbox, text="OK", command=lambda: on_confirm(round(self.scale.get(), 1)) or self.destroy()).pack(side=tk.LEFT, padx=4)

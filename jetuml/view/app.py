"""Main Application Window, Menu Bar, Tab Notebook, and Shortcuts (RF01-RF06, RF33-RF42)."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional, Any
from ..core.diagram import Diagram, DiagramType
from ..core.commands import CommandStack, RemoveElementsCommand, EditPropertiesCommand
from ..core.serializer import DiagramSerializer
from ..core.clipboard import ClipboardManager
from ..export.svg_exporter import SvgExporter
from ..export.raster_exporter import RasterExporter
from ..export.clipboard_image import copy_diagram_to_clipboard
from .theme import ThemeManager
from .canvas import DiagramCanvas
from .toolbar import DiagramToolbar
from .notification import NotificationManager
from .dialogs import PropertiesDialog, DiagramSizeDialog, NotificationDurationDialog


class JetUMLApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("JetUML")
        self.root.geometry("1100x750")

        self.notifier = NotificationManager(self.root)
        self.auto_edit_node: bool = True
        self.recent_files: List[str] = []

        self.tab_data: Dict[str, Dict] = {}

        self._build_menu()
        self._build_ui()
        self._bind_global_shortcuts()

        self.new_diagram(DiagramType.CLASS)

    def _build_menu(self) -> None:
        mb = tk.Menu(self.root)

        file_m = tk.Menu(mb, tearoff=0)
        new_m = tk.Menu(file_m, tearoff=0)
        for dt in DiagramType:
            new_m.add_command(label=f"{dt.value} Diagram", command=lambda t=dt: self.new_diagram(t))
        file_m.add_cascade(label="New", menu=new_m)
        file_m.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_diagram)
        file_m.add_command(label="Save", accelerator="Ctrl+S", command=self.save_diagram)
        file_m.add_command(label="Save As...", command=self.save_as_diagram)
        file_m.add_command(label="Duplicate", accelerator="Ctrl+D", command=self.duplicate_current_diagram)
        file_m.add_separator()
        file_m.add_command(label="Export Image...", command=self.export_image)
        file_m.add_command(label="Copy to Clipboard", accelerator="Ctrl+B", command=self.copy_to_clipboard)
        file_m.add_separator()
        file_m.add_command(label="Close", accelerator="Ctrl+W", command=self.close_current_tab)
        file_m.add_command(label="Exit", accelerator="Ctrl+Q", command=self.root.quit)
        mb.add_cascade(label="File", menu=file_m)

        edit_m = tk.Menu(mb, tearoff=0)
        edit_m.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_m.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        edit_m.add_separator()
        edit_m.add_command(label="Cut", accelerator="Ctrl+X", command=self.cut)
        edit_m.add_command(label="Copy", accelerator="Ctrl+C", command=self.copy)
        edit_m.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste)
        edit_m.add_command(label="Delete", accelerator="Del", command=self.delete_selected)
        edit_m.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        edit_m.add_separator()
        edit_m.add_command(label="Properties", accelerator="Ctrl+Enter", command=self.open_properties)
        mb.add_cascade(label="Edit", menu=edit_m)

        view_m = tk.Menu(mb, tearoff=0)
        self.show_grid_var = tk.BooleanVar(value=True)
        view_m.add_checkbutton(label="Show Grid", variable=self.show_grid_var, command=self.toggle_grid)
        self.auto_edit_var = tk.BooleanVar(value=True)
        view_m.add_checkbutton(label="Auto Edit Node", variable=self.auto_edit_var, command=self.toggle_auto_edit)
        view_m.add_separator()
        view_m.add_command(label="Zoom In", accelerator="Ctrl+=", command=self.zoom_in)
        view_m.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self.zoom_out)
        view_m.add_command(label="Reset Zoom", accelerator="Ctrl+0", command=self.zoom_reset)
        view_m.add_separator()
        view_m.add_command(label="Set Diagram Size...", command=self.set_diagram_size)
        view_m.add_command(label="Notification Duration...", command=self.set_notification_duration)
        view_m.add_command(label="Dark Mode", command=self.toggle_dark_mode)
        mb.add_cascade(label="View", menu=view_m)

        self.root.config(menu=mb)

    def _build_ui(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

    def _bind_global_shortcuts(self) -> None:
        self.root.bind("<Control-n>", lambda e: self.new_diagram(DiagramType.CLASS))
        self.root.bind("<Control-o>", lambda e: self.open_diagram())
        self.root.bind("<Control-s>", lambda e: self.save_diagram())
        self.root.bind("<Control-d>", lambda e: self.duplicate_current_diagram())
        self.root.bind("<Control-w>", lambda e: self.close_current_tab())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-b>", lambda e: self.copy_to_clipboard())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<Control-Return>", lambda e: self.open_properties())
        self.root.bind("<Control-equal>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.zoom_reset())

    def new_diagram(self, dtype: DiagramType) -> None:
        diag = Diagram(dtype, f"New {dtype.value}")
        self._create_tab(diag)

    def _create_tab(self, diag: Diagram) -> None:
        frame = ttk.Frame(self.notebook)
        stack = CommandStack(diag)

        side_tb = DiagramToolbar(frame, diag.diagram_type, on_tool_selected=lambda t: canvas.set_tool(t))
        side_tb.pack(side=tk.LEFT, fill=tk.Y)

        canvas = DiagramCanvas(
            frame,
            diag,
            stack,
            on_notify=lambda msg, ok: self.notifier.show_success(msg) if ok else self.notifier.show_error(msg),
            on_auto_edit=self._open_props_dialog,
        )
        canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tab_title = diag.title
        self.notebook.add(frame, text=tab_title)
        tab_id = str(frame)
        self.tab_data[tab_id] = {
            "canvas": canvas,
            "diagram": diag,
            "stack": stack,
            "toolbar": side_tb,
            "frame": frame,
        }
        self.notebook.select(frame)

    def _get_active(self) -> Optional[Dict]:
        curr = self.notebook.select()
        return self.tab_data.get(curr)

    def open_diagram(self) -> None:
        fp = filedialog.askopenfilename(filetypes=[("JetUML JSON", "*.json"), ("All Files", "*.*")])
        if fp:
            try:
                diag = DiagramSerializer.load_from_file(fp)
                self._create_tab(diag)
                self.notifier.show_success(f"Opened: {diag.title}")
            except Exception as e:
                self.notifier.show_error(f"Failed to open file: {e}")

    def save_diagram(self) -> None:
        active = self._get_active()
        if not active:
            return
        diag: Diagram = active["diagram"]
        if diag.file_path:
            DiagramSerializer.save_to_file(diag, diag.file_path)
            self.notifier.show_success("Saved successfully.")
        else:
            self.save_as_diagram()

    def save_as_diagram(self) -> None:
        active = self._get_active()
        if not active:
            return
        diag: Diagram = active["diagram"]
        fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JetUML JSON", "*.json")])
        if fp:
            DiagramSerializer.save_to_file(diag, fp)
            self.notifier.show_success("File saved.")

    def duplicate_current_diagram(self) -> None:
        active = self._get_active()
        if active:
            dup = active["diagram"].duplicate()
            self._create_tab(dup)
            self.notifier.show_success("Diagram duplicated.")

    def copy_to_clipboard(self) -> None:
        active = self._get_active()
        if active:
            copy_diagram_to_clipboard(active["diagram"])
            self.notifier.show_success("Diagram image copied to clipboard.")

    def export_image(self) -> None:
        active = self._get_active()
        if not active:
            return
        fp = filedialog.asksaveasfilename(filetypes=[("SVG Vector", "*.svg"), ("PNG Image", "*.png"), ("JPEG Image", "*.jpg")])
        if fp:
            if fp.endswith(".svg"):
                svg = SvgExporter.export(active["diagram"])
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(svg)
            else:
                fmt = "JPEG" if fp.endswith(".jpg") or fp.endswith(".jpeg") else "PNG"
                RasterExporter.export_to_file(active["diagram"], fp, fmt)
            self.notifier.show_success(f"Exported to {fp}")

    def undo(self) -> None:
        active = self._get_active()
        if active and active["stack"].undo():
            active["canvas"].redraw()

    def redo(self) -> None:
        active = self._get_active()
        if active and active["stack"].redo():
            active["canvas"].redraw()

    def cut(self) -> None:
        active = self._get_active()
        if active:
            ClipboardManager.get_instance().copy(active["diagram"])
            self.delete_selected()

    def copy(self) -> None:
        active = self._get_active()
        if active:
            cnt = ClipboardManager.get_instance().copy(active["diagram"])
            self.notifier.show_success(f"Copied {cnt} elements.")

    def paste(self) -> None:
        active = self._get_active()
        if active:
            ok, err, cmd = ClipboardManager.get_instance().paste(active["diagram"])
            if ok and cmd:
                active["stack"].execute(cmd)
                active["canvas"].redraw()
            else:
                self.notifier.show_error(err or "Paste failed.")

    def delete_selected(self) -> None:
        active = self._get_active()
        if active:
            sel = active["diagram"].selected_elements
            if sel:
                cmd = RemoveElementsCommand(active["diagram"], sel)
                active["stack"].execute(cmd)
                active["canvas"].redraw()

    def select_all(self) -> None:
        active = self._get_active()
        if active:
            active["diagram"].select_all()
            active["canvas"].redraw()

    def open_properties(self) -> None:
        active = self._get_active()
        if active:
            sel = active["diagram"].selected_elements
            if sel:
                self._open_props_dialog(sel[0])

    def _open_props_dialog(self, element: Any) -> None:
        active = self._get_active()
        if not active:
            return

        tracked_keys = (
            "name", "attributes", "methods", "value", "text", "content",
            "open_bottom", "middle_label", "start_label", "end_label", "directionality"
        )
        old_props = {k: getattr(element, k) for k in tracked_keys if hasattr(element, k)}

        def on_save(new_props: Dict[str, Any]) -> None:
            cmd = EditPropertiesCommand(active["diagram"], element, old_props, new_props)
            active["stack"].execute(cmd)
            active["canvas"].redraw()

        PropertiesDialog(self.root, element, on_save=on_save)

    def toggle_grid(self) -> None:
        active = self._get_active()
        if active:
            active["canvas"].show_grid = self.show_grid_var.get()
            active["canvas"].redraw()

    def toggle_auto_edit(self) -> None:
        self.auto_edit_node = self.auto_edit_var.get()

    def zoom_in(self) -> None:
        active = self._get_active()
        if active and active["canvas"].zoom_level < 2:
            active["canvas"].zoom_level += 1
            active["canvas"].redraw()

    def zoom_out(self) -> None:
        active = self._get_active()
        if active and active["canvas"].zoom_level > -2:
            active["canvas"].zoom_level -= 1
            active["canvas"].redraw()

    def zoom_reset(self) -> None:
        active = self._get_active()
        if active:
            active["canvas"].zoom_level = 0
            active["canvas"].redraw()

    def set_diagram_size(self) -> None:
        active = self._get_active()
        if active:
            d = active["diagram"]
            DiagramSizeDialog(self.root, d.width, d.height, lambda w, h: setattr(d, "width", w) or setattr(d, "height", h) or active["canvas"].redraw())

    def set_notification_duration(self) -> None:
        NotificationDurationDialog(self.root, self.notifier.duration_seconds, lambda s: setattr(self.notifier, "duration_seconds", s))

    def toggle_dark_mode(self) -> None:
        ThemeManager.toggle()
        for tab in self.tab_data.values():
            tab["canvas"].redraw()

    def close_current_tab(self) -> None:
        curr = self.notebook.select()
        if curr and len(self.tab_data) > 1:
            self.notebook.forget(curr)
            del self.tab_data[curr]
        elif len(self.tab_data) <= 1:
            self.root.quit()

"""Toast notifications in bottom-left corner (RF41, RF42)."""

from __future__ import annotations
import tkinter as tk
from .theme import ThemeManager


class NotificationManager:
    def __init__(self, parent: tk.Widget) -> None:
        self.parent = parent
        self.duration_seconds: float = 5.0
        self._toast_frame: tk.Frame | None = None
        self._timer_id: str | None = None

    def show_error(self, message: str) -> None:
        theme = ThemeManager.get_current()
        self._show(message, theme.error_toast_bg, theme.toast_fg)

    def show_success(self, message: str) -> None:
        theme = ThemeManager.get_current()
        self._show(message, theme.confirm_toast_bg, theme.toast_fg)

    def _show(self, message: str, bg_color: str, fg_color: str) -> None:
        if self.duration_seconds <= 0.0:
            return

        self._dismiss()

        frame = tk.Frame(self.parent, bg=bg_color, padx=12, pady=8, relief=tk.RAISED, borderwidth=1)
        label = tk.Label(frame, text=message, bg=bg_color, fg=fg_color, font=("Segoe UI", 10, "bold"))
        label.pack()

        frame.place(relx=0.02, rely=0.96, anchor="sw")
        self._toast_frame = frame

        ms = int(self.duration_seconds * 1000)
        self._timer_id = self.parent.after(ms, self._dismiss)

    def _dismiss(self) -> None:
        if self._timer_id:
            self.parent.after_cancel(self._timer_id)
            self._timer_id = None
        if self._toast_frame:
            self._toast_frame.destroy()
            self._toast_frame = None

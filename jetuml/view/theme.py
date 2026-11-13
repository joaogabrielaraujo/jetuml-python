"""Theme and color definitions for Light and Dark modes (RF40)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    canvas_bg: str
    grid_color: str
    node_fill: str
    node_stroke: str
    text_color: str
    selection_color: str
    rubberband_color: str
    panel_bg: str
    toolbar_bg: str
    toolbar_btn_active: str
    error_toast_bg: str
    confirm_toast_bg: str
    toast_fg: str


LIGHT_THEME = Theme(
    name="Light",
    canvas_bg="#ffffff",
    grid_color="#e5e5e5",
    node_fill="#fcfcfc",
    node_stroke="#1a1a1a",
    text_color="#111111",
    selection_color="#0066cc",
    rubberband_color="#0088ff",
    panel_bg="#f3f3f3",
    toolbar_bg="#ececec",
    toolbar_btn_active="#d0d0d0",
    error_toast_bg="#d9534f",
    confirm_toast_bg="#5cb85c",
    toast_fg="#ffffff",
)

DARK_THEME = Theme(
    name="Dark",
    canvas_bg="#1e1e1e",
    grid_color="#2d2d2d",
    node_fill="#252526",
    node_stroke="#d4d4d4",
    text_color="#e0e0e0",
    selection_color="#4daafc",
    rubberband_color="#3794ff",
    panel_bg="#252526",
    toolbar_bg="#333333",
    toolbar_btn_active="#505050",
    error_toast_bg="#c9302c",
    confirm_toast_bg="#449d44",
    toast_fg="#ffffff",
)


class ThemeManager:
    _current: Theme = LIGHT_THEME

    @classmethod
    def get_current(cls) -> Theme:
        return cls._current

    @classmethod
    def toggle(cls) -> Theme:
        cls._current = DARK_THEME if cls._current == LIGHT_THEME else LIGHT_THEME
        return cls._current

    @classmethod
    def is_dark(cls) -> bool:
        return cls._current == DARK_THEME

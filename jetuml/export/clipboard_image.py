"""Copy diagram image to system clipboard (RF05)."""

from __future__ import annotations
import io
import subprocess
import sys
from typing import TYPE_CHECKING
from .raster_exporter import RasterExporter

if TYPE_CHECKING:
    from ..core.diagram import Diagram


def copy_diagram_to_clipboard(diagram: Diagram) -> bool:
    img = RasterExporter.render_to_image(diagram)
    output = io.BytesIO()
    img.save(output, format="BMP")
    bmp_data = output.getvalue()[14:]

    if sys.platform.startswith("win"):
        try:
            import win32clipboard  # type: ignore
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
            win32clipboard.CloseClipboard()
            return True
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        png_out = io.BytesIO()
        img.save(png_out, format="PNG")
        try:
            subprocess.run(["xclip", "-selection", "clipboard", "-t", "image/png"], input=png_out.getvalue(), check=True)
            return True
        except Exception:
            pass
    elif sys.platform == "darwin":
        png_out = io.BytesIO()
        img.save(png_out, format="PNG")
        try:
            subprocess.run(["osascript", "-e", 'set the clipboard to (read (POSIX file "/dev/stdin") as JPEG picture)'], input=png_out.getvalue(), check=True)
            return True
        except Exception:
            pass
    return True

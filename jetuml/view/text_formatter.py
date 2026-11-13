"""Text formatting conventions parser for UML (RF24)."""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List


@dataclass
class FormattedSegment:
    text: str
    is_italic: bool
    is_underline: bool


class TextFormatter:
    @staticmethod
    def parse_line(line: str) -> List[FormattedSegment]:
        segments: List[FormattedSegment] = []
        pattern = re.compile(r"(/[^/]+/_|_[^_]+_/|/[^/]+/|_[^_]+_)")
        last_idx = 0

        for match in pattern.finditer(line):
            start, end = match.span()
            if start > last_idx:
                segments.append(FormattedSegment(line[last_idx:start], False, False))

            token = match.group(0)
            is_it = False
            is_un = False

            if token.startswith("/") and token.endswith("/"):
                is_it = True
                content = token[1:-1]
            elif token.startswith("_") and token.endswith("_"):
                is_un = True
                content = token[1:-1]
            else:
                content = token

            segments.append(FormattedSegment(content, is_it, is_un))
            last_idx = end

        if last_idx < len(line):
            segments.append(FormattedSegment(line[last_idx:], False, False))

        return segments

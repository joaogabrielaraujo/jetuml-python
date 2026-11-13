"""
Geometry primitives and utilities for JetUML.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Point:
        return Point(self.x * scalar, self.y * scalar)

    def distance_to(self, other: Point) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass(frozen=True)
class Dimension:
    width: float
    height: float


@dataclass
class Rectangle:
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Point:
        return Point(self.x + self.width / 2.0, self.y + self.height / 2.0)

    def contains(self, p: Point) -> bool:
        return self.x <= p.x <= self.right and self.y <= p.y <= self.bottom

    def intersects(self, other: Rectangle) -> bool:
        return not (
            self.right < other.x
            or other.right < self.x
            or self.bottom < other.y
            or other.bottom < self.y
        )

    def union(self, other: Rectangle) -> Rectangle:
        min_x = min(self.x, other.x)
        min_y = min(self.y, other.y)
        max_x = max(self.right, other.right)
        max_y = max(self.bottom, other.bottom)
        return Rectangle(min_x, min_y, max_x - min_x, max_y - min_y)

    def intersection_with_ray(self, target: Point) -> Point:
        """
        Finds the intersection point of the line from the rectangle's center
        to `target` with the perimeter of the rectangle.
        """
        c = self.center
        dx = target.x - c.x
        dy = target.y - c.y

        if dx == 0 and dy == 0:
            return c

        half_w = self.width / 2.0
        half_h = self.height / 2.0

        # Check intersection with left/right vertical edges
        # and top/bottom horizontal edges
        t_candidates = []
        if dx != 0:
            tx1 = half_w / abs(dx)
            t_candidates.append(tx1)
        if dy != 0:
            ty1 = half_h / abs(dy)
            t_candidates.append(ty1)

        t = min(t_candidates)
        return Point(c.x + dx * t, c.y + dy * t)

    def connection_point(self, target: Point) -> Point:
        return self.intersection_with_ray(target)

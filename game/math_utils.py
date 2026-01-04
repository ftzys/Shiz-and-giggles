from __future__ import annotations

import math
from typing import Iterable, Tuple

Vector = Tuple[float, float, float]


def distance(a: Vector, b: Vector) -> float:
    return math.dist(a, b)


def normalize(v: Vector) -> Vector:
    magnitude = math.dist(v, (0.0, 0.0, 0.0))
    if magnitude == 0:
        return (0.0, 0.0, 0.0)
    return tuple(component / magnitude for component in v)  # type: ignore[return-value]


def scale(v: Vector, amount: float) -> Vector:
    return tuple(component * amount for component in v)  # type: ignore[return-value]


def add(a: Vector, b: Vector) -> Vector:
    return tuple(x + y for x, y in zip(a, b))  # type: ignore[return-value]


def average(vectors: Iterable[Vector]) -> Vector:
    vectors = list(vectors)
    if not vectors:
        return (0.0, 0.0, 0.0)
    count = len(vectors)
    return tuple(sum(components) / count for components in zip(*vectors))  # type: ignore[return-value]

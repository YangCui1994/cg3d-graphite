"""Isolated Leclaire-2017 D3Q19 colour-gradient research line.

Task: BI-CG-LECLAIRE-IMPLEMENTATION-001.
Nothing in this package is imported by, or imports, the production solver.
"""
from .solver import LeclaireCG3D  # noqa: F401

__all__ = ["LeclaireCG3D"]

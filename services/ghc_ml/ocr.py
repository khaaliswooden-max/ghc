"""LayoutLMv3-based ingredient/label OCR.

The Phase A stub exposes the call signature only; weights and
fine-tuning data land in Phase E.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OcrResult:
    text: str
    e_numbers: list[str]
    suspect_ingredients: list[str]


def extract_label(_image_path: str) -> OcrResult:
    """Run LayoutLMv3 on a product label image. NotImplemented in v0.0.1."""
    raise NotImplementedError("LayoutLMv3 fine-tune lands in Phase E.")

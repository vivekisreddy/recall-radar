"""Normalisers for product identifiers. Both sides of a match (recall and user item) go through
the same function, so "XJ-200 b" on a label and "XJ200B" in a recall notice compare equal."""

import re


def normalize_model(value: str | None) -> str | None:
    """'7927-OZ1' -> '7927OZ1', 'xj-200 b' -> 'XJ200B'. Empty input -> None."""
    if not value:
        return None
    norm = re.sub(r"[^A-Z0-9]", "", value.upper())
    return norm or None


def normalize_upc(value: str | None) -> str | None:
    """'0 75465 11111 0' -> '075465111110'.

    Keeps 8-14 digit codes (UPC-E, UPC-A, EAN-13, GTIN-14); anything else returns None.
    """
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits if 8 <= len(digits) <= 14 else None

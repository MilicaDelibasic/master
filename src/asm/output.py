"""Emit machine-code artifacts (.bin / .hex / listing)."""

from __future__ import annotations

from pathlib import Path


def write_bin(path: Path, words: list[int]) -> None:
    """Write little-endian 32-bit words to a binary file."""
    data = b"".join(int(w & 0xFFFFFFFF).to_bytes(4, "little") for w in words)
    path.write_bytes(data)


def write_hex(path: Path, words: list[int], *, base_address: int = 0) -> None:
    """Write a simple address/value hex listing (one word per line)."""
    lines = [
        f"{base_address + 4 * i:08x}: {w & 0xFFFFFFFF:08x}" for i, w in enumerate(words)
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

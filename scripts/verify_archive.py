#!/usr/bin/env python3
"""Verify checksummed final results and frozen checkpoint artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "artifacts" / "SHA256SUMS.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if not MANIFEST.is_file():
        print(f"Missing manifest: {MANIFEST}")
        return 1

    failures = []
    checked = 0
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split(maxsplit=1)
        path = REPO_ROOT / relative
        checked += 1
        if not path.is_file():
            failures.append(f"MISSING  {relative}")
            continue
        actual = sha256(path)
        if actual != expected:
            failures.append(f"MISMATCH {relative}")

    if failures:
        print("Archive verification failed:")
        print("\n".join(failures))
        return 1

    print(f"Archive verification passed: {checked} files match SHA-256 manifest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

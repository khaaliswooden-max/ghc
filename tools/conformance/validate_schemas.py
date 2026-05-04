#!/usr/bin/env python3
"""Validate every JSON Schema under the given directory.

Used by CI (`spec` job) to gate the protocol on schema integrity even
before Phase F freezes v0.1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


def main(root: str) -> int:
    root_path = Path(root)
    if not root_path.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    failures = 0
    schemas = sorted(root_path.glob("*.json"))
    if not schemas:
        print(f"no schemas under {root}", file=sys.stderr)
        return 1

    for path in schemas:
        try:
            with path.open() as f:
                schema = json.load(f)
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            failures += 1
            continue
        print(f"ok   {path}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "spec/schemas"))

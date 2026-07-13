#!/usr/bin/env python3
"""Check Python files for a final newline and lines longer than 119 characters."""

from __future__ import annotations

import argparse
from pathlib import Path

MAX_LINE_LENGTH = 119
SKIPPED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "migrations",
    "__pycache__",
    "htmlcov",
    "staticfiles",
    "media",
}


def iter_python_files(root: Path) -> list[Path]:
    """Return project Python files,
    excluding generated and virtual-environment directories."""
    return sorted(
        path
        for path in root.rglob("*.py")
        if not any(part in SKIPPED_PARTS for part in path.parts)
    )


def main() -> int:
    """Run style preflight checks and optionally repair missing final newlines."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fix-eof",
        action="store_true",
        help="Add a missing final newline to Python files.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    fixed: list[str] = []

    for path in iter_python_files(Path(".")):
        data = path.read_bytes()

        if data and not data.endswith(b"\n"):
            if args.fix_eof:
                path.write_bytes(data + b"\n")
                fixed.append(str(path))
                data += b"\n"
            else:
                errors.append(f"{path}: missing final newline")

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            errors.append(f"{path}: not valid UTF-8: {error}")
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if len(line) > MAX_LINE_LENGTH:
                errors.append(
                    f"{path}:{line_number}: {len(line)} characters "
                    f"(maximum {MAX_LINE_LENGTH})"
                )

    for path in fixed:
        print(f"Fixed final newline: {path}")

    if errors:
        print("\n".join(errors))
        return 1

    print("Style preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

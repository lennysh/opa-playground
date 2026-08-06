#!/usr/bin/env python3
"""Sync kustomization.yaml configMapGenerator files from policies/**/*.rego."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KUSTOMIZATION = ROOT / "kustomization.yaml"
DEFAULT_POLICIES = ROOT / "policies"
CONFIGMAP_NAME = "opa-policies"


def find_rego_files(policies_dir: Path) -> list[Path]:
    return sorted(policies_dir.rglob("*.rego"))


def relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def build_files_block(rel_paths: list[str], indent: str = "      ") -> str:
    if not rel_paths:
        return f"{indent}files: []\n"
    lines = [f"{indent}files:"]
    lines.extend(f"{indent}  - {p}" for p in rel_paths)
    return "\n".join(lines) + "\n"


def update_kustomization(text: str, rel_paths: list[str]) -> str:
    marker = f"- name: {CONFIGMAP_NAME}"
    start = text.find(marker)
    if start < 0:
        raise SystemExit(
            f"Could not find configMapGenerator entry named {CONFIGMAP_NAME!r}"
        )

    files_key = text.find("files:", start)
    if files_key < 0:
        raise SystemExit("Could not find 'files:' under opa-policies configMapGenerator")

    # Indent of the 'files:' key (spaces before it)
    line_start = text.rfind("\n", 0, files_key) + 1
    indent = text[line_start:files_key]

    # Consume the files list: current line plus following list items at deeper indent
    i = files_key
    while i < len(text) and text[i] != "\n":
        i += 1
    i += 1  # past newline after 'files:'

    while i < len(text):
        line_end = text.find("\n", i)
        if line_end < 0:
            line_end = len(text)
        line = text[i:line_end]
        stripped = line.lstrip(" ")
        if not line.strip():
            # blank line ends the list
            break
        line_indent = len(line) - len(stripped)
        if line_indent <= len(indent):
            break
        if not stripped.startswith("- "):
            break
        i = line_end + 1 if line_end < len(text) else line_end

    new_block = build_files_block(rel_paths, indent=indent)
    return text[:line_start] + new_block + text[i:]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update kustomization.yaml files: list from policies/**/*.rego"
    )
    parser.add_argument(
        "-k",
        "--kustomization",
        type=Path,
        default=DEFAULT_KUSTOMIZATION,
        help="Path to kustomization.yaml",
    )
    parser.add_argument(
        "-p",
        "--policies",
        type=Path,
        default=DEFAULT_POLICIES,
        help="Policies directory to scan",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Print the updated files list without writing",
    )
    parser.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="Exit 1 if kustomization.yaml is out of date (do not write)",
    )
    parser.add_argument(
        "--fail-on-change",
        action="store_true",
        help="Write updates if needed, then exit 1 when the file changed "
        "(for pre-commit: stage the updated file and re-commit)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only print errors",
    )
    args = parser.parse_args()

    if args.dry_run and args.check:
        print("Use only one of --dry-run / --check", file=sys.stderr)
        return 2
    if args.check and args.fail_on_change:
        print("Use only one of --check / --fail-on-change", file=sys.stderr)
        return 2

    policies_dir = args.policies.resolve()
    kustomization = args.kustomization.resolve()
    root = kustomization.parent

    if not policies_dir.is_dir():
        print(f"Policies directory not found: {policies_dir}", file=sys.stderr)
        return 1
    if not kustomization.is_file():
        print(f"kustomization.yaml not found: {kustomization}", file=sys.stderr)
        return 1

    rego_files = find_rego_files(policies_dir)
    try:
        rel_paths = [relative_posix(p, root) for p in rego_files]
    except ValueError:
        print(
            f"ERROR: policies under {policies_dir} must be inside "
            f"the kustomization directory ({root})",
            file=sys.stderr,
        )
        return 1

    basenames = [Path(p).name for p in rel_paths]
    dupes = [name for name, count in Counter(basenames).items() if count > 1]
    if dupes:
        print(
            "ERROR: ConfigMap keys use file basenames; duplicate .rego names found:",
            file=sys.stderr,
        )
        for name in sorted(dupes):
            matches = [p for p in rel_paths if Path(p).name == name]
            print(f"  {name}:", file=sys.stderr)
            for m in matches:
                print(f"    - {m}", file=sys.stderr)
        print(
            "Rename files so each basename is unique under policies/.",
            file=sys.stderr,
        )
        return 1

    original = kustomization.read_text(encoding="utf-8")
    updated = update_kustomization(original, rel_paths)
    rel_kustomization = kustomization.relative_to(root)

    if args.dry_run:
        print(build_files_block(rel_paths), end="")
        return 0

    if updated == original:
        if not args.quiet:
            print(f"Already up to date ({len(rel_paths)} .rego file(s)).")
        return 0

    if args.check:
        print(
            f"ERROR: {rel_kustomization} is out of date with policies/**/*.rego",
            file=sys.stderr,
        )
        print(
            f"Run: python3 scripts/sync-kustomization-files.py && git add {rel_kustomization}",
            file=sys.stderr,
        )
        return 1

    kustomization.write_text(updated, encoding="utf-8")
    if not args.quiet:
        print(f"Updated {rel_kustomization} with {len(rel_paths)} .rego file(s):")
        for p in rel_paths:
            print(f"  - {p}")

    if args.fail_on_change:
        print(
            f"ERROR: {rel_kustomization} was updated. Stage it and re-commit:",
            file=sys.stderr,
        )
        print(f"  git add {rel_kustomization} && git commit", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

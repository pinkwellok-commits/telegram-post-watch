#!/usr/bin/env python3
"""Copy a project to a new isolated folder without common private/runtime files.

This is a preliminary filter, not a secret scanner. Review before publishing.
Uses only the Python standard library.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import sys


EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".codex", ".agents", ".aws", ".ssh",
    ".cloudflared", ".idea", ".vscode", "node_modules", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache",
    ".next", ".nuxt", ".output", ".turbo", ".vercel", ".netlify",
    "dist", "build", "coverage", "logs", "secrets", "backups",
}
EXCLUDED_NAMES = {
    ".env", ".npmrc", ".pypirc", ".netrc", "credentials", "credentials.json",
    "service-account.json", "service_account.json", "id_rsa", "id_ed25519",
    ".ds_store", "thumbs.db",
}
EXCLUDED_SUFFIXES = {
    ".pem", ".key", ".p12", ".pfx", ".keystore", ".jks",
    ".sqlite", ".sqlite3", ".db", ".dump", ".bak", ".log", ".pyc",
}
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def is_link_or_reparse(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & REPARSE_POINT
    )


def exclusion_reason(path):
    name = path.name.lower()
    if is_link_or_reparse(path):
        return "file-link-or-reparse-point"
    if path.is_dir() and name in EXCLUDED_DIRS:
        return "private-or-generated-directory"
    if name in EXCLUDED_NAMES or name.startswith(".env."):
        return "possible-secret-or-machine-config"
    if name.endswith(".sql") and any(word in name for word in ("dump", "backup")):
        return "possible-database-dump"
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return "private-data-or-runtime-file"
    if not path.is_dir() and not stat.S_ISREG(path.lstat().st_mode):
        return "non-regular-file"
    return None


def is_within(path, parent):
    return path == parent or parent in path.parents


def copy_project(source, destination):
    source_input = Path(source).expanduser()
    destination_input = Path(destination).expanduser()
    if not source_input.is_dir():
        raise ValueError("Source must be an existing project directory.")
    if is_link_or_reparse(source_input):
        raise ValueError("Choose a real source directory, not a link or junction.")
    if os.path.lexists(destination_input):
        raise ValueError("Destination already exists; choose a new directory.")
    source_path = source_input.resolve(strict=True)
    destination_path = destination_input.resolve(strict=False)
    if is_within(destination_path, source_path) or is_within(source_path, destination_path):
        raise ValueError("Source and destination must not overlap.")

    # Never copy through a junction or another filesystem link.
    for ancestor in [destination_input.absolute(), *destination_input.absolute().parents]:
        if os.path.lexists(ancestor) and is_link_or_reparse(ancestor):
            raise ValueError("Destination ancestors must not be links or junctions.")

    destination_path.mkdir(parents=True, exist_ok=False)
    copied_count = 0
    skipped = []

    def copy_directory(current_source, current_destination):
        nonlocal copied_count
        for child in sorted(current_source.iterdir(), key=lambda entry: entry.name.lower()):
            relative = child.relative_to(source_path).as_posix()
            reason = exclusion_reason(child)
            if reason:
                skipped.append({"path": relative, "reason": reason})
                continue
            target = current_destination / child.name
            if child.is_dir():
                target.mkdir()
                copy_directory(child, target)
            else:
                shutil.copy2(child, target)
                copied_count += 1

    try:
        copy_directory(source_path, destination_path)
    except Exception as exc:
        raise RuntimeError(
            f"Copy failed; partial copy remains at {destination_path}. "
            "Inspect it and use a new destination for a retry."
        ) from exc

    return {
        "source": str(source_path),
        "destination": str(destination_path),
        "copied_files": copied_count,
        "skipped": skipped,
        "publication_ready": False,
        "next": "Review remaining secrets, integrations and original business data before publication.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Existing local project directory")
    parser.add_argument("destination", help="New copy directory outside the source")
    arguments = parser.parse_args()
    try:
        result = copy_project(arguments.source, arguments.destination)
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import argparse
import hashlib
import json
import os


BASELINE_FILE = "baseline_hashes.json"
INCLUDED_ROOTS = ("SKILL.md", "README.md", "LICENSE.txt", "agents", "scripts", "tests")
EXCLUDED_DIRS = {"__pycache__", ".git"}
EXCLUDED_FILES = {".DS_Store", BASELINE_FILE}


def _is_included(rel_path):
    return any(rel_path == root or rel_path.startswith(root + "/") for root in INCLUDED_ROOTS)


def package_files(root="."):
    root = os.path.abspath(root)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            dirname for dirname in dirnames
            if dirname not in EXCLUDED_DIRS and not dirname.startswith(".")
        ]

        for filename in filenames:
            if filename in EXCLUDED_FILES or filename.endswith(".pyc"):
                continue

            path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(path, root).replace(os.sep, "/")
            if _is_included(rel_path):
                yield rel_path


def file_hash(path):
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def build_hashes(root="."):
    root = os.path.abspath(root)
    return {
        rel_path: file_hash(os.path.join(root, rel_path))
        for rel_path in sorted(package_files(root))
    }


def load_baseline(root="."):
    path = os.path.join(root, BASELINE_FILE)
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def compare_hashes(root="."):
    root = os.path.abspath(root)
    baseline = load_baseline(root)
    current = build_hashes(root)

    changed = {
        path: {
            "baseline": baseline[path],
            "current": current[path],
        }
        for path in sorted(set(baseline) & set(current))
        if baseline[path] != current[path]
    }

    missing = sorted(set(baseline) - set(current))
    new = sorted(set(current) - set(baseline))

    return {
        "status": "MATCH" if not changed and not missing and not new else "DIFF",
        "changed": changed,
        "missing": missing,
        "new": new,
        "baseline_count": len(baseline),
        "current_count": len(current),
    }


def write_baseline(root="."):
    root = os.path.abspath(root)
    hashes = build_hashes(root)
    path = os.path.join(root, BASELINE_FILE)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(hashes, file, indent=2)
        file.write("\n")

    return {
        "status": "WRITTEN",
        "file": BASELINE_FILE,
        "count": len(hashes),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare package file hashes with the baseline.")
    parser.add_argument("root", nargs="?", default=".", help="Skill package root.")
    parser.add_argument("--write", action="store_true", help="Refresh baseline_hashes.json.")
    args = parser.parse_args(argv)

    result = write_baseline(args.root) if args.write else compare_hashes(args.root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

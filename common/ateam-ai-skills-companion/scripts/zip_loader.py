## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import os
import stat
import tempfile
import zipfile
from pathlib import PurePosixPath


PRIORITY_FILES = ("README.md", "SKILL.md", "LICENSE.txt", "openai.yaml")
READABLE_SUFFIXES = (".md", ".txt", ".yaml", ".yml", ".py")
MAX_FILES = 100
MAX_TOTAL_UNCOMPRESSED = 10 * 1024 * 1024
MAX_MEMBER_UNCOMPRESSED = 5 * 1024 * 1024


def _normalized_member_name(name):
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)

    if path.is_absolute() or normalized.startswith("/"):
        raise ValueError(f"Unsafe absolute path in ZIP: {name}")

    if any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"Unsafe path segment in ZIP: {name}")

    if path.parts and ":" in path.parts[0]:
        raise ValueError(f"Unsafe drive-like path in ZIP: {name}")

    return normalized


def _is_symlink(info):
    mode = info.external_attr >> 16
    return stat.S_ISLNK(mode)


def _target_path(extract_to, member_name):
    root = os.path.realpath(extract_to)
    target = os.path.realpath(os.path.join(root, member_name))

    if target != root and not target.startswith(root + os.sep):
        raise ValueError(f"ZIP member escapes extraction root: {member_name}")

    return target


def extract_zip(zip_path, extract_to=None):
    if not zipfile.is_zipfile(zip_path):
        raise ValueError("Invalid ZIP file")

    if extract_to is None:
        extract_to = tempfile.mkdtemp(prefix="skill_review_")

    os.makedirs(extract_to, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        members = zip_ref.infolist()

        if len(members) > MAX_FILES:
            raise ValueError("Too many files in ZIP")

        total_size = 0
        for info in members:
            member_name = _normalized_member_name(info.filename)

            if _is_symlink(info):
                raise ValueError(f"Symlink entries are not allowed: {info.filename}")

            total_size += info.file_size
            if info.file_size > MAX_MEMBER_UNCOMPRESSED:
                raise ValueError(f"ZIP member is too large: {info.filename}")

            if total_size > MAX_TOTAL_UNCOMPRESSED:
                raise ValueError("ZIP package is too large")

            target = _target_path(extract_to, member_name)

            if info.is_dir():
                os.makedirs(target, exist_ok=True)
                continue

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zip_ref.open(info, "r") as source, open(target, "wb") as dest:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    dest.write(chunk)

    return extract_to


def _file_key(folder, path):
    return os.path.relpath(path, folder).replace(os.sep, "/")


def _content_root(folder):
    package_name = infer_package_name(folder)
    if package_name:
        return os.path.join(folder, package_name)
    return folder


def _file_priority(key):
    base_name = os.path.basename(key)
    if "/" not in key and base_name in PRIORITY_FILES:
        return 0
    if key == "agents/openai.yaml":
        return 0
    return 1


def _legacy_display_key(key):
    if key == "agents/openai.yaml":
        return "openai.yaml"
    return key


def _package_file_key(folder, path):
    rel_path = os.path.relpath(path, folder).replace(os.sep, "/")
    return rel_path


def _readable_files(folder):
    candidates = []
    root_folder = _content_root(folder)

    for root, _, files in os.walk(root_folder):
        for filename in files:
            if filename.endswith(READABLE_SUFFIXES):
                path = os.path.join(root, filename)
                key = _file_key(root_folder, path)
                candidates.append((_file_priority(key), key, path))

    return sorted(candidates)


def _package_files(folder):
    candidates = []
    root_folder = _content_root(folder)

    for root, dirnames, files in os.walk(root_folder):
        dirnames[:] = [
            dirname for dirname in dirnames
            if dirname not in {"__pycache__", ".git"} and not dirname.startswith(".")
        ]

        for filename in files:
            if filename == ".DS_Store" or filename.endswith(".pyc"):
                continue

            path = os.path.join(root, filename)
            candidates.append((_package_file_key(root_folder, path), path))

    return sorted(candidates)


def read_package_text_files(folder):
    file_map = {}
    package_files = []

    for key, path in _package_files(folder):
        package_files.append(key)
        try:
            with open(path, "r", encoding="utf-8") as file:
                file_map[key] = file.read()
        except UnicodeDecodeError:
            continue
        except OSError:
            continue

    return file_map, package_files


def infer_package_name(folder):
    top_level_dirs = set()
    root_files = set()

    for root, dirnames, files in os.walk(folder):
        dirnames[:] = [
            dirname for dirname in dirnames
            if dirname not in {"__pycache__", ".git"} and not dirname.startswith(".")
        ]

        for filename in files:
            if filename == ".DS_Store":
                continue

            rel_path = os.path.relpath(os.path.join(root, filename), folder).replace(os.sep, "/")
            parts = rel_path.split("/")
            if len(parts) == 1:
                root_files.add(parts[0])
            else:
                top_level_dirs.add(parts[0])

    if not root_files and len(top_level_dirs) == 1:
        return next(iter(top_level_dirs))

    return None


def read_skill_files_with_context(folder):
    combined_text = ""
    file_map = {}

    for _, key, path in _readable_files(folder):
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
        except UnicodeDecodeError:
            continue
        except OSError:
            continue

        display_key = _legacy_display_key(key)
        file_map[display_key] = content
        combined_text += f"\n\n### FILE: {display_key}\n"
        combined_text += content

    return combined_text, file_map


def read_skill_files(folder):
    combined_text, _ = read_skill_files_with_context(folder)
    return combined_text

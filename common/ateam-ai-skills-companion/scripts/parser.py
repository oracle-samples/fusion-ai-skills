## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import re


SECTION_HEADERS = {
    "inputs": "inputs",
    "input": "inputs",
    "outputs": "outputs",
    "output": "outputs",
    "prompts": "prompts",
    "prompt": "prompts",
    "workflow": "workflow",
    "steps": "steps",
}

FILE_MARKER_RE = re.compile(r"^###\s+FILE:\s*(?P<name>.+?)\s*$")
MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}(?P<level>#{1,6})\s+(?P<title>.+?)\s*#*\s*$")
COLON_HEADING_RE = re.compile(
    r"^\s*(?P<title>inputs?|outputs?|prompts?|workflow|steps)\s*:\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(?P<item>.+?)\s*$")
FRONTMATTER_RE = re.compile(r"^\s*---\s*\n(?P<body>.*?)\n---\s*", re.DOTALL)


def normalize(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def unique_preserve(items):
    seen = set()
    unique = []

    for item in items:
        clean = item.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            unique.append(clean)

    return unique


def split_by_file(text):
    """
    Splits aggregated text into file-aware chunks.

    Aggregated review text uses markers such as:
    ### FILE: SKILL.md

    Plain pasted text is kept under UNKNOWN.
    """
    files = {}
    current_file = "UNKNOWN"
    buffer = []

    for line in text.split("\n"):
        marker = FILE_MARKER_RE.match(line)
        if marker:
            if buffer:
                files[current_file] = "\n".join(buffer).strip()
                buffer = []

            current_file = marker.group("name").strip()
        else:
            buffer.append(line)

    if buffer:
        files[current_file] = "\n".join(buffer).strip()

    return files


def canonical_header(title):
    title = re.sub(r"\([^)]*\)", "", title).strip().lower()
    title = re.sub(r"[^a-z0-9\s-]", " ", title)
    words = [word for word in re.split(r"\s+", title) if word]

    if not words:
        return None

    first = words[0]
    if first in SECTION_HEADERS:
        return SECTION_HEADERS[first]

    if words[:2] == ["prompt", "guide"]:
        return "prompts"

    return None


def section_marker(line):
    markdown = MARKDOWN_HEADING_RE.match(line)
    if markdown and len(markdown.group("level")) <= 2:
        header = canonical_header(markdown.group("title"))
        if header:
            return header, ""

    colon = COLON_HEADING_RE.match(line)
    if colon:
        header = canonical_header(colon.group("title"))
        if header:
            return header, colon.group("rest").strip()

    return None, None


def find_sections(text):
    sections = {}
    current_header = None
    buffer = []

    def flush():
        if not current_header:
            return

        content = "\n".join(buffer).strip()
        if not content:
            return

        existing = sections.get(current_header)
        sections[current_header] = f"{existing}\n{content}" if existing else content

    for line in text.split("\n"):
        header, rest = section_marker(line)
        if header:
            flush()
            current_header = header
            buffer = [rest] if rest else []
            continue

        if current_header:
            buffer.append(line)

    flush()
    return sections


def find_headings(text):
    headings = []

    for line in text.split("\n"):
        match = MARKDOWN_HEADING_RE.match(line)
        if match:
            headings.append(match.group("title").strip())

    return headings


def extract_frontmatter(text):
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}

    metadata = {}
    for line in match.group("body").split("\n"):
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")

    return metadata


def clean_list_item(value):
    value = value.strip()
    value = re.sub(r"\s{2,}$", "", value)
    value = value.strip("` ")

    if value.endswith(":"):
        value = value[:-1].strip()

    return value


def is_noise_line(line):
    stripped = line.strip()
    return (
        not stripped
        or stripped in {"---", "***", "```"}
        or stripped.startswith("```")
        or MARKDOWN_HEADING_RE.match(stripped)
    )


def extract_list(section):
    if not section:
        return []

    items = []
    fallback = []

    for line in section.split("\n"):
        if is_noise_line(line):
            continue

        match = LIST_ITEM_RE.match(line)
        if match:
            items.append(clean_list_item(match.group("item")))
        else:
            fallback.append(clean_list_item(line))

    return unique_preserve(items or fallback)


def extract_prompts(section):
    if not section:
        return []

    quoted = re.findall(r'"([^"\n]+)"', section)
    if quoted:
        return unique_preserve(quoted)

    return extract_list(section)


def extract_prompts_fallback(text):
    prompts = re.findall(r'"([^"\n]+)"', text)

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith(("generate", "validate", "review", "improve")):
            prompts.append(stripped)

    return unique_preserve(prompts)


def analyze(text):
    text = normalize(text)
    file_map = split_by_file(text)

    all_inputs = []
    all_outputs = []
    all_prompts = []
    all_workflow = []
    file_sections = {}
    file_headings = {}
    file_metadata = {}

    for fname, content in file_map.items():
        parse_document = fname == "UNKNOWN" or fname.endswith((".md", ".txt", ".yaml", ".yml"))
        sections = find_sections(content) if parse_document else {}
        file_sections[fname] = sections
        file_headings[fname] = find_headings(content) if parse_document else []
        file_metadata[fname] = extract_frontmatter(content) if parse_document else {}

        inputs = extract_list(sections.get("inputs"))
        outputs = extract_list(sections.get("outputs"))
        prompts = extract_prompts(sections.get("prompts"))
        workflow = extract_list(sections.get("workflow"))
        workflow.extend(extract_list(sections.get("steps")))

        if not prompts and (fname == "UNKNOWN" or fname.endswith((".md", ".txt", ".yaml", ".yml"))):
            prompts = extract_prompts_fallback(content)

        all_inputs.extend(inputs)
        all_outputs.extend(outputs)
        all_prompts.extend(prompts)
        all_workflow.extend(workflow)

    inputs_list = unique_preserve(all_inputs)
    outputs_list = unique_preserve(all_outputs)
    prompts_list = unique_preserve(all_prompts)
    workflow_steps = unique_preserve(all_workflow)

    return {
        "file_sections": file_sections,
        "file_headings": file_headings,
        "file_metadata": file_metadata,
        "file_text": file_map,
        "inputs_list": inputs_list,
        "outputs_list": outputs_list,
        "prompts_list": prompts_list,
        "workflow_steps": workflow_steps,
        "inputs_count": len(inputs_list),
        "outputs_count": len(outputs_list),
        "prompts_count": len(prompts_list),
        "workflow_count": len(workflow_steps),
    }

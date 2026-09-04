## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import re


AGGREGATE_FILE_MARKER_RE = re.compile(r"^###\s+FILE:\s*(?P<name>.+?)\s*$")

SECRET_PATTERNS = [
    (
        "openai_api_key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        "critical",
        "OpenAI-style API key detected.",
        "Remove the key, rotate it, and load it from an environment variable or secret manager.",
    ),
    (
        "generic_secret_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|password)\b"
            r"\s*[:=]\s*['\"]?([A-Za-z0-9_./+=-]{16,})['\"]?"
        ),
        "critical",
        "Possible hard-coded secret or credential detected.",
        "Remove the value, rotate it if real, and reference it through configuration or a secret manager.",
    ),
    (
        "aws_access_key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "critical",
        "AWS access key ID detected.",
        "Remove the key, rotate the credential, and use an IAM role or secret manager.",
    ),
    (
        "github_token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
        "critical",
        "GitHub token detected.",
        "Remove the token, revoke or rotate it, and read it from a secure runtime secret.",
    ),
    (
        "slack_token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
        "critical",
        "Slack token detected.",
        "Remove the token, rotate it, and load it from a secret manager.",
    ),
]

PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b\+?\d[\d\s().-]{8,}\d\b")
ISO_DATE_RE = re.compile(
    r"\b(?:19|20)\d{2}[-/.](?:0[1-9]|1[0-2])[-/.](?:0[1-9]|[12]\d|3[01])\b"
)
COMPACT_DATE_RE = re.compile(
    r"^(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])$"
)
URL_RE = re.compile(r"\bhttps?://[^\s)>\]\"']+", re.IGNORECASE)
ABSOLUTE_PATH_RE = re.compile(r"(?<![\w.-])(?:/[A-Za-z0-9._ -]+){2,}")

DESTRUCTIVE_SHELL_PATTERNS = [
    re.compile(r"\brm\s+-[A-Za-z]*[rf][A-Za-z]*\s+(?:/|\$HOME|~|\*)"),
    re.compile(r"\bsudo\s+rm\s+-[A-Za-z]*[rf][A-Za-z]*\b"),
    re.compile(r"\bdd\s+if=.*\s+of=/dev/(?:disk|rdisk|sd|nvme)", re.IGNORECASE),
    re.compile(r"\bmkfs(?:\.[A-Za-z0-9]+)?\s+/dev/", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;:"),
]

UNSAFE_PYTHON_PATTERNS = [
    re.compile(r"\bshutil\.rmtree\s*\("),
    re.compile(r"\bos\.remove\s*\(\s*['\"]?/"),
    re.compile(r"\bos\.unlink\s*\(\s*['\"]?/"),
    re.compile(r"\bos\.system\s*\("),
    re.compile(r"\bsubprocess\.(?:run|call|Popen)\s*\([^)]*shell\s*=\s*True"),
]

URL_SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
}

SAFE_URL_HOSTS = {
    "example.com",
    "example.org",
    "example.net",
    "localhost",
    "127.0.0.1",
    "oss.oracle.com",
}

PROMPT_INJECTION_PHRASES = [
    ("ignore " + "previous instructions"),
    ("ignore " + "all previous instructions"),
    ("disregard " + "previous instructions"),
    ("reveal " + "system prompt"),
    ("print " + "system prompt"),
    ("developer " + "message"),
    ("bypass " + "safety"),
    ("jail" + "break"),
]


def _split_aggregate_text(text):
    files = {}
    current_file = "UNKNOWN"
    buffer = []

    for line in text.splitlines():
        match = AGGREGATE_FILE_MARKER_RE.match(line)
        if match:
            files[current_file] = "\n".join(buffer)
            current_file = match.group("name").strip()
            buffer = []
        else:
            buffer.append(line)

    files[current_file] = "\n".join(buffer)
    return {name: content for name, content in files.items() if content.strip()}


def _sources(text, file_map=None):
    if file_map:
        return file_map.items()

    split = _split_aggregate_text(text)
    if split:
        return split.items()

    return [("UNKNOWN", text)]


def _redact(value, keep_start=4, keep_end=4):
    value = str(value)
    if len(value) <= keep_start + keep_end + 3:
        return "***"

    return f"{value[:keep_start]}...{value[-keep_end:]}"


def _safe_excerpt(value, max_len=90):
    value = " ".join(str(value).strip().split())
    if len(value) <= max_len:
        return value

    return value[: max_len - 3] + "..."


def _redact_email(value):
    local, _, domain = value.partition("@")
    if not domain:
        return _redact(value)

    safe_local = local[:2] + "***" if len(local) > 2 else "***"
    return f"{safe_local}@{domain}"


def _redact_phone(value):
    digits = re.sub(r"\D", "", value)
    if len(digits) < 4:
        return "***"
    return f"***-***-{digits[-4:]}"


def _looks_like_date_not_phone(value):
    if ISO_DATE_RE.search(value):
        without_dates = ISO_DATE_RE.sub("", value)
        remaining_digits = re.sub(r"\D", "", without_dates)
        return len(remaining_digits) <= 4

    digits = re.sub(r"\D", "", value)
    return bool(COMPACT_DATE_RE.match(digits))


def _looks_like_portable_env_path(path):
    return path.startswith("/usr/bin/env")


def _looks_like_nonliteral_secret_reference(value):
    value = str(value).strip().strip("\"'")
    nonliteral_prefixes = (
        "args.",
        "config.",
        "settings.",
        "self.",
        "os.environ",
        "os.getenv",
        "getenv",
        "getpass",
        "secrets.",
    )
    return value.startswith(nonliteral_prefixes)


def _looks_like_absolute_local_path(path):
    local_roots = (
        "/Applications/",
        "/Library/",
        "/System/",
        "/Users/",
        "/Volumes/",
        "/bin/",
        "/etc/",
        "/home/",
        "/mnt/",
        "/opt/",
        "/private/",
        "/root/",
        "/sbin/",
        "/srv/",
        "/usr/",
        "/var/",
    )
    return path.startswith(local_roots)


def _hostname(url):
    host = re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/", 1)[0]
    return host.split("@")[-1].split(":")[0].lower()


def _is_suspicious_url(url):
    host = _hostname(url)
    if host in SAFE_URL_HOSTS or host.endswith(".example.com"):
        return False

    if url.lower().startswith("http://"):
        return True

    if "@" in url.split("/", 3)[2]:
        return True

    if host in URL_SHORTENERS:
        return True

    if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", host) and host != "127.0.0.1":
        return True

    return False


def _finding(file, line, finding_type, severity, value, why, fix):
    result = {
        "file": file,
        "line": line,
        "type": finding_type,
        "severity": severity,
        "value": value,
        "why": why,
        "fix": fix,
    }

    if file == "UNKNOWN":
        result.pop("file")

    return result


def _skip_comment_line(line):
    stripped = line.strip()
    return stripped.startswith("#") and "example" in stripped.lower()


def _scan_line(file, line_number, line):
    findings = []

    if _skip_comment_line(line):
        return findings

    for finding_type, pattern, severity, why, fix in SECRET_PATTERNS:
        for match in pattern.finditer(line):
            value = match.group(1) if match.lastindex else match.group(0)
            if finding_type == "generic_secret_assignment" and _looks_like_nonliteral_secret_reference(value):
                continue
            findings.append(_finding(file, line_number, finding_type, severity, _redact(value), why, fix))

    if PRIVATE_KEY_RE.search(line):
        findings.append(_finding(
            file,
            line_number,
            "private_key",
            "critical",
            "-----BEGIN ... PRIVATE KEY-----",
            "Private key material appears to be embedded in the package.",
            "Remove the private key, rotate it, and store it in a secret manager.",
        ))

    for match in EMAIL_RE.finditer(line):
        email = match.group(0)
        severity = "minor" if "example" in email.lower() else "medium"
        findings.append(_finding(
            file,
            line_number,
            "email",
            severity,
            _redact_email(email),
            "Email addresses can expose personal or operational contact information.",
            "Use a placeholder email address unless the address is intentional public documentation.",
        ))

    for match in PHONE_RE.finditer(line):
        phone = match.group(0)
        if _looks_like_date_not_phone(phone):
            continue

        digits = re.sub(r"\D", "", phone)
        if not 10 <= len(digits) <= 15:
            continue

        findings.append(_finding(
            file,
            line_number,
            "phone",
            "medium",
            _redact_phone(phone),
            "Phone numbers can expose personal or operational contact information.",
            "Use a placeholder number or remove it unless it is intentional public documentation.",
        ))

    for pattern in DESTRUCTIVE_SHELL_PATTERNS:
        for match in pattern.finditer(line):
            findings.append(_finding(
                file,
                line_number,
                "destructive_shell_command",
                "high",
                _safe_excerpt(match.group(0)),
                "Destructive shell commands can remove user data or damage the environment if executed.",
                "Replace destructive examples with guarded dry-run commands or explicit approval workflows.",
            ))

    for pattern in UNSAFE_PYTHON_PATTERNS:
        for match in pattern.finditer(line):
            findings.append(_finding(
                file,
                line_number,
                "unsafe_python_file_operation",
                "high",
                _safe_excerpt(match.group(0)),
                "Unsafe Python file operations can delete files or execute shell commands unexpectedly.",
                "Use scoped paths, explicit confirmations, and subprocess calls without shell=True.",
            ))

    for match in URL_RE.finditer(line):
        url = match.group(0).rstrip(".,")
        if _is_suspicious_url(url):
            findings.append(_finding(
                file,
                line_number,
                "suspicious_external_url",
                "medium",
                _safe_excerpt(url),
                "Suspicious URLs can hide redirects, credentials, IP targets, or insecure HTTP links.",
                "Use HTTPS URLs from trusted domains and avoid shorteners or credential-bearing URLs.",
            ))

    lowered = line.lower()
    for phrase in PROMPT_INJECTION_PHRASES:
        if phrase in lowered:
            findings.append(_finding(
                file,
                line_number,
                "prompt_injection_instruction",
                "high",
                _safe_excerpt(phrase),
                "Prompt-injection-style instructions can override the intended skill behavior.",
                "Remove the instruction or clearly mark it as an example of text to detect, not obey.",
            ))

    for match in ABSOLUTE_PATH_RE.finditer(line):
        if match.start() > 0 and line[match.start() - 1] == "/":
            continue

        path = match.group(0).rstrip(".,:;)")
        if _looks_like_portable_env_path(path):
            continue

        if path.startswith(("/tmp", "/private/tmp", "/var/folders")):
            continue

        if not _looks_like_absolute_local_path(path):
            continue

        findings.append(_finding(
            file,
            line_number,
            "absolute_local_path",
            "low",
            _safe_excerpt(path),
            "Absolute local paths can leak machine-specific details and make packages less portable.",
            "Use relative paths, environment variables, or placeholders.",
        ))

    return findings


def _dedupe(findings):
    seen = set()
    unique = []

    for finding in findings:
        key = (
            finding.get("file"),
            finding.get("line"),
            finding["type"],
            finding["value"],
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)

    return unique


def detect_security_issues(text, file_map=None):
    findings = []

    for file, content in _sources(text, file_map):
        for line_number, line in enumerate(str(content).splitlines(), start=1):
            findings.extend(_scan_line(file, line_number, line))

    return _dedupe(findings)

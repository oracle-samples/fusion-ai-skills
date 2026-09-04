#!/usr/bin/env python3
## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

"""Reference redaction helper for supplier-onboarding consuming applications.

Run this before constructing prompts and before writing model inputs, outputs,
logs, telemetry, or error messages. The helper is intentionally conservative and
standard-library only; consuming applications should also map known structured
fields directly to placeholders before calling an LLM.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SWIFT_COUNTRY_CODES = (
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT",
    "AU", "AW", "AX", "AZ", "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI",
    "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS", "BT", "BV", "BW", "BY",
    "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN",
    "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM",
    "DO", "DZ", "EC", "EE", "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK",
    "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL",
    "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM",
    "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR",
    "IS", "IT", "JE", "JM", "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN",
    "KP", "KR", "KW", "KY", "KZ", "LA", "LB", "LC", "LI", "LK", "LR", "LS",
    "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK",
    "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW",
    "MX", "MY", "MZ", "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP",
    "NR", "NU", "NZ", "OM", "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM",
    "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM",
    "SN", "SO", "SR", "SS", "ST", "SV", "SX", "SY", "SZ", "TC", "TD", "TF",
    "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TR", "TT", "TV", "TW",
    "TZ", "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI",
    "VN", "VU", "WF", "WS", "XK", "YE", "YT", "ZA", "ZM", "ZW",
)


ADDRESS_LABEL = (
    r"(?:supplier\s+address|remit-?to\s+address|remittance\s+address|"
    r"registered\s+address|street\s+address|mailing\s+address|billing\s+address|"
    r"legal\s+address|postal\s+address|city\s*/\s*state\s*/\s*postal|"
    r"city\s*,?\s*state\s*,?\s*postal|city/state/postal|address)"
)

ADDRESS_SUBFIELD_LABEL = (
    r"(?:postal\s+code|postcode|zip(?:\s+code)?|country|city|province|"
    r"state\s*/\s*province|city\s*/\s*state\s*/\s*postal|"
    r"city\s*,?\s*state\s*,?\s*postal|city/state/postal)"
)

ADDRESS_LINE_TERMINATOR = r"(?:[A-Za-z][A-Za-z /-]{1,40}\s*[:=-]|\s*$)"

BANK_ACCOUNT_LABEL = (
    r"(?:bank\s+account(?:\s+number)?|supplier\s+bank\s+account|"
    r"remit(?:tance)?\s+account|remit-?to\s+account|account(?:\s+number)?|"
    r"payment\s+account|beneficiary\s+account|bank\s+acct|acct(?:\s+no\.?)?)"
)

BANK_ROUTING_LABEL = (
    r"(?:sort\s+code|bsb|branch\s+code|bank\s+code|routing\s+code|"
    r"clearing\s+code|national\s+clearing\s+code|bank\s+routing\s+code)"
)

TAX_REGISTRATION_LABEL = (
    r"(?:tax\s+number|tax\s+registration\s+number|supplier\s+tax\s+number|"
    r"tax\s+no\.?|tax\s+registration\s+no\.?|vat\s+number|"
    r"vat\s+registration\s+number|vat\s+no\.?|vat\s+registration\s+no\.?|"
    r"gst\s+number|gst\s+no\.?|tax\s+registration|vat\s+registration|"
    r"gst\s+registration)"
)

IDENTITY_LABEL = (
    r"(?:identity\s+value|identity\s+document(?:\s+number)?|document\s+number|"
    r"government\s+id|registration\s+id|supplier\s+registration\s+id|"
    r"legal\s+registration\s+id|national\s+id|passport\s+number|"
    r"driver(?:'s)?\s+license(?:\s+number)?)"
)

PHONE_LABEL = (
    r"(?:contact\s+phone|supplier\s+phone|remit(?:tance)?\s+phone|"
    r"remit-?to\s+phone|telephone|mobile|cell(?:\s+phone)?|phone|tel\.?)"
)

SWIFT_BIC_LABEL = (
    r"(?:swift(?:\s*/\s*bic)?|swift\s+code|bic|bic\s+code|"
    r"bank\s+identifier\s+code)"
)

SWIFT_BIC_VALUE = (
    r"[A-Z]{4}(?:" + "|".join(SWIFT_COUNTRY_CODES) + r")[A-Z0-9]{2}(?:[A-Z0-9]{3})?"
)

LABELED_DIGIT_VALUE = r"(?:[A-Z]{0,4}[- ]*)?\d(?:[ -]?\d){7,19}\b"
LABELED_ID_VALUE = r"(?=[A-Z0-9 /-]*\d)[A-Z0-9][A-Z0-9 /-]{3,30}\b"
LABELED_ROUTING_VALUE = r"(?=(?:[A-Z0-9 /-]*\d){4,})[A-Z0-9][A-Z0-9 /-]{3,30}\b"
LABELED_PHONE_VALUE = r"(?=(?:[+()0-9 .-]*\d){7,15})[+()0-9 .-]{7,32}\b"


@dataclass(frozen=True)
class RedactionResult:
    """Redaction output plus verification details for fail-closed callers."""

    text: str
    counts_by_placeholder: dict[str, int]
    counts_by_category: dict[str, int]
    residual_categories: list[str]

    @property
    def has_residuals(self) -> bool:
        return bool(self.residual_categories)


class RedactionResidualError(ValueError):
    """Raised when strict redaction still sees sensitive-looking residue."""

    def __init__(self, result: RedactionResult):
        self.result = result
        categories = ", ".join(result.residual_categories)
        super().__init__(f"Residual sensitive-looking categories after redaction: {categories}")


REDACTION_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("personal_email", "[PERSONAL_EMAIL_REDACTED]", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    (
        "bank_account",
        "[BANK_ACCOUNT_MASKED]",
        re.compile(
            r"(?im)^\s*" + BANK_ACCOUNT_LABEL + r"\s*[:#=-]\s*" + LABELED_DIGIT_VALUE
        ),
    ),
    (
        "bank_routing",
        "[BANK_ACCOUNT_MASKED]",
        re.compile(
            r"(?im)^\s*" + BANK_ROUTING_LABEL + r"\s*[:#=-]\s*" + LABELED_ROUTING_VALUE
        ),
    ),
    (
        "tax_id",
        "[TAX_ID_MASKED]",
        re.compile(
            r"(?im)^\s*" + TAX_REGISTRATION_LABEL + r"\s*[:#=-]\s*" + LABELED_ID_VALUE
        ),
    ),
    (
        "identity_document",
        "[IDENTITY_VALUE_MASKED]",
        re.compile(
            r"(?im)^\s*" + IDENTITY_LABEL + r"\s*[:#=-]\s*" + LABELED_ID_VALUE
        ),
    ),
    (
        "address",
        "[ADDRESS_REDACTED]",
        re.compile(
            r"(?im)^\s*" + ADDRESS_LABEL + r"\s*[:=-]\s*\S[^\n]*"
            r"(?:\n(?!\s*" + ADDRESS_LINE_TERMINATOR + r").{1,160}){0,4}"
        ),
    ),
    (
        "address",
        "[ADDRESS_REDACTED]",
        re.compile(
            r"(?im)^\s*" + ADDRESS_SUBFIELD_LABEL + r"\s*[:=-]\s*\S.{0,120}$"
        ),
    ),
    (
        "address",
        "[ADDRESS_REDACTED]",
        re.compile(
            r"\bP\.?\s*O\.?\s*(?:Box|Bx)\s+[A-Z0-9][A-Z0-9 -]{0,24}"
            r"(?:[,\s]+(?:[A-Z][A-Za-z.'-]{1,30}|[A-Z]{2,3}|\d[A-Z0-9 -]{2,10})){0,4}",
            re.IGNORECASE,
        ),
    ),
    ("iban", "[IBAN_MASKED]", re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,30}\b")),
    (
        "swift_bic",
        "[SWIFT_MASKED]",
        re.compile(
            r"\b" + SWIFT_BIC_LABEL + r"\s*[:#=-]\s*" + SWIFT_BIC_VALUE + r"\b",
            re.IGNORECASE,
        ),
    ),
    (
        "swift_bic",
        "[SWIFT_MASKED]",
        re.compile(
            r"\b(?=[A-Z0-9]*\d)" + SWIFT_BIC_VALUE + r"\b"
        ),
    ),
    ("aba_routing", "[BANK_ACCOUNT_MASKED]", re.compile(r"\b(?:0[0-9]|1[0-2]|2[1-9]|3[0-2]|6[1-9]|7[0-2]|80)\d{7}\b")),
    ("tax_id", "[TAX_ID_MASKED]", re.compile(r"\b\d{2}-\d{7}\b")),
    (
        "tin",
        "[TIN_MASKED]",
        re.compile(
            r"\b(?:TIN|TAX ID|TAX IDENTIFICATION NUMBER|EIN|VAT|VAT ID)\s*[:#=]\s*"
            r"[A-Z0-9][A-Z0-9 -]{5,}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "tax_form_value",
        "[TAX_ID_MASKED]",
        re.compile(
            r"\bW-?[89](?:BEN(?:-E)?)?\s*(?:VALUE|TAX|TIN|ID)?\s*[:#=]\s*"
            r"[A-Z0-9][A-Z0-9 -]{5,}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "identity_document",
        "[IDENTITY_VALUE_MASKED]",
        re.compile(
            r"\b(?:PASSPORT|DRIVER(?:'S)? LICENSE|DRIVING LICENSE|NATIONAL ID|"
            r"IDENTITY DOCUMENT|ID DOCUMENT|GOVERNMENT ID|SSN|SIN)\s*[:#=]\s*"
            r"[A-Z0-9][A-Z0-9-]{4,}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "phone",
        "[PHONE_REDACTED]",
        re.compile(r"(?<!\w)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?!\w)"),
    ),
    (
        "phone",
        "[PHONE_REDACTED]",
        re.compile(r"(?im)^\s*" + PHONE_LABEL + r"\s*[:#=-]\s*" + LABELED_PHONE_VALUE),
    ),
    ("phone", "[PHONE_REDACTED]", re.compile(r"(?<!\w)\+\d{1,3}[\s.-](?:\d[\s.-]?){7,14}\b")),
    ("bank_account", "[BANK_ACCOUNT_MASKED]", re.compile(r"\b\d(?:[ -]?\d){11,18}\b")),
    (
        "address",
        "[ADDRESS_REDACTED]",
        re.compile(
            r"\b\d{1,6}\s+[A-Za-z0-9.' -]{2,80}\s+"
            r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|"
            r"Way|Court|Ct|Circle|Cir|Parkway|Pkwy|Highway|Hwy|Suite|Ste|Unit|"
            r"Apt|Avenida|Avda|Calle|Rua|Rue|Via|Viale|Chemin|Quai|Place|Plaza|"
            r"Strasse|Allee|Gasse)\b"
            r"(?:[.,]?\s+[A-Za-z0-9.' -]{1,40}){0,4}",
            re.IGNORECASE,
        ),
    ),
]

RESIDUAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "bank_account",
        re.compile(
            r"(?im)^\s*" + BANK_ACCOUNT_LABEL + r"\s*[:#=-]\s*"
            r"(?=(?:.*\d){6,})[A-Z0-9 -]{6,40}$"
        ),
    ),
    (
        "bank_routing",
        re.compile(
            r"(?im)^\s*" + BANK_ROUTING_LABEL + r"\s*[:#=-]\s*"
            r"(?=(?:[A-Z0-9 /-]*\d){4,})[A-Z0-9 /-]{4,40}$"
        ),
    ),
    (
        "tax_id",
        re.compile(
            r"(?im)^\s*" + TAX_REGISTRATION_LABEL + r"\s*[:#=-]\s*"
            r"(?=[A-Z0-9 /-]*\d)[A-Z0-9 /-]{4,40}$"
        ),
    ),
    (
        "identity_document",
        re.compile(
            r"(?im)^\s*" + IDENTITY_LABEL + r"\s*[:#=-]\s*"
            r"(?=[A-Z0-9 -]*\d)[A-Z0-9 -]{4,40}$"
        ),
    ),
    (
        "address",
        re.compile(
            r"(?im)^\s*(?:" + ADDRESS_LABEL + r"|" + ADDRESS_SUBFIELD_LABEL + r")"
            r"\s*[:=-]\s*\S.{0,160}$"
        ),
    ),
    (
        "phone",
        re.compile(
            r"(?im)^\s*" + PHONE_LABEL + r"\s*[:#=-]\s*"
            r"(?=(?:[+()0-9 .-]*\d){7,15})[+()0-9 .-]{7,40}$"
        ),
    ),
]


def supplier_name_patterns(supplier_names: list[str] | tuple[str, ...]) -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []
    for name in supplier_names:
        cleaned = name.strip()
        if len(cleaned) < 2 or cleaned.startswith("["):
            continue
        exact = re.escape(cleaned).replace(r"\ ", r"\s+")
        patterns.append(re.compile(r"(?<![\w])" + exact + r"(?![\w])", re.IGNORECASE))
        tokens = re.findall(r"[A-Za-z0-9]+", cleaned)
        if len(tokens) >= 2:
            flexible = r"[\s,.'&()/#-]+".join(re.escape(token) for token in tokens)
            patterns.append(re.compile(r"(?<![\w])" + flexible + r"(?![\w])", re.IGNORECASE))
    return patterns


def add_count(target: dict[str, int], key: str, count: int) -> None:
    if count:
        target[key] = target.get(key, 0) + count


def residual_sensitive_categories(
    text: str,
    supplier_names: list[str] | tuple[str, ...] = (),
) -> list[str]:
    categories: set[str] = set()
    for category, _placeholder, pattern in REDACTION_PATTERNS:
        if pattern.search(text):
            categories.add(category)
    for category, pattern in RESIDUAL_PATTERNS:
        if pattern.search(text):
            categories.add(category)
    for pattern in supplier_name_patterns(supplier_names):
        if pattern.search(text):
            categories.add("supplier_name")
    return sorted(categories)


def redact_with_report(
    text: str,
    supplier_names: list[str] | tuple[str, ...] = (),
) -> RedactionResult:
    """Return redacted text, match counts, and residual sensitive-looking categories."""

    redacted = text
    counts_by_placeholder: dict[str, int] = {}
    counts_by_category: dict[str, int] = {}
    for category, placeholder, pattern in REDACTION_PATTERNS:
        redacted, count = pattern.subn(placeholder, redacted)
        add_count(counts_by_placeholder, placeholder, count)
        add_count(counts_by_category, category, count)
    for pattern in supplier_name_patterns(supplier_names):
        redacted, count = pattern.subn("[SUPPLIER_NAME]", redacted)
        add_count(counts_by_placeholder, "[SUPPLIER_NAME]", count)
        add_count(counts_by_category, "supplier_name", count)
    residuals = residual_sensitive_categories(redacted, supplier_names=supplier_names)
    return RedactionResult(
        text=redacted,
        counts_by_placeholder=counts_by_placeholder,
        counts_by_category=counts_by_category,
        residual_categories=residuals,
    )


def redact_or_raise(text: str, supplier_names: list[str] | tuple[str, ...] = ()) -> str:
    """Return redacted text or raise when residual sensitive-looking values remain."""

    result = redact_with_report(text, supplier_names=supplier_names)
    if result.has_residuals:
        raise RedactionResidualError(result)
    return result.text


def redact_text(text: str, supplier_names: list[str] | tuple[str, ...] = ()) -> str:
    """Return text with supplier-sensitive values replaced by masked placeholders."""

    return redact_with_report(text, supplier_names=supplier_names).text


def redact_prompt_payload(text: str, supplier_names: list[str] | tuple[str, ...] = ()) -> str:
    """Alias for callers redacting data before constructing an LLM prompt."""

    return redact_text(text, supplier_names=supplier_names)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Redact supplier-sensitive values from stdin or text files."
    )
    parser.add_argument("paths", nargs="*", type=Path, help="Text files to redact. Reads stdin when omitted.")
    parser.add_argument(
        "--supplier-name",
        action="append",
        default=[],
        help="Known supplier name to replace with [SUPPLIER_NAME]. May be repeated.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero if sensitive-looking values remain after redaction.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.paths:
        chunks = [path.read_text(encoding="utf-8") for path in args.paths]
        source = "\n".join(chunks)
    else:
        source = sys.stdin.read()
    result = redact_with_report(source, supplier_names=args.supplier_name)
    sys.stdout.write(result.text)
    if args.strict and result.has_residuals:
        categories = ", ".join(result.residual_categories)
        sys.stderr.write(f"Residual sensitive-looking categories after redaction: {categories}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

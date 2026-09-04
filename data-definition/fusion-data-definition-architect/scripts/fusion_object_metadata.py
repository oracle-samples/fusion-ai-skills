#!/usr/bin/env python3
"""Interactive Oracle Fusion/CX object metadata retriever.

This script is designed for the fusion-data-definition-architect skill.
It prompts the user for a bearer token at runtime, fetches one or more
Oracle Fusion/CX object describe payloads, stores structured JSON output,
and exports all fields to an Excel workbook.

Key behaviors
-------------
- Prompts for bearer token on every fetch run
- Supports one or many object names in a single execution
- Tries common Fusion/CX metadata endpoints automatically
- Writes combined JSON and Excel (.xlsx) outputs
- Does not persist credentials

Examples
--------
Interactive mode:
    python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py

Argument-assisted mode:
    python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py \
      --base-url 'https://example.fa.oraclecloud.com/' \
      --objects Accounts Opportunities \
      --service auto

Convert an existing JSON output to Excel only:
    python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py \
      --input-json accounts_metadata.json
"""

from __future__ import annotations

import argparse
import copy
import difflib
import getpass
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape as xml_escape


CRM_OBJECT_HINTS = {
    "accounts",
    "opportunities",
    "contacts",
    "activities",
    "leads",
    "campaigns",
    "households",
    "partners",
}

TRUSTED_STANDARD_OBJECTS: Dict[str, Dict[str, str]] = {
    "crmRestApi": {
        "accounts": "Accounts",
        "contacts": "Contacts",
        "leads": "Leads",
        "opportunities": "Opportunities",
        "activities": "Activities",
        "campaigns": "Campaigns",
        "households": "Households",
        "partners": "Partners",
    },
    "fscmRestApi": {
        "ledgers": "Ledgers",
        "invoices": "Invoices",
        "journals": "Journals",
        "journalbatches": "JournalBatches",
    },
}

FIELD_NAME_KEYS: Sequence[str] = (
    "name",
    "field",
    "fieldName",
    "attributeName",
    "displayName",
    "DisplayName",
    "id",
)

FIELD_TYPE_KEYS: Sequence[str] = (
    "dataType",
    "type",
    "fieldType",
    "valueType",
    "businessType",
    "baseType",
)

REQUIRED_KEYS: Sequence[str] = (
    "required",
    "isRequired",
    "mandatory",
    "nullable",
)

ADDITIONAL_METADATA_KEYS: Sequence[str] = (
    "length",
    "maxLength",
    "minLength",
    "precision",
    "scale",
    "nullable",
    "required",
    "isRequired",
    "mandatory",
    "updatable",
    "updateable",
    "searchable",
    "filterable",
    "sortable",
    "queryable",
    "createable",
    "title",
    "label",
    "format",
    "default",
    "description",
)

CANONICAL_FIELD_COLUMNS: Sequence[str] = (
    "Field Name",
    "Category",
    "Data Type",
    "Required",
    "In Sample",
    "Score",
    "Confidence",
    "Is Mappable",
    "Length",
    "Description",
    "Source API",
)

SUMMARY_SHEET_COLUMNS: Sequence[str] = (
    "Object Name",
    "Status",
    "Field Mode",
    "Metadata Fields",
    "Sample Fields",
    "Exported Fields",
    "Business Fields",
    "System Fields",
    "Flexfields",
    "Relationship Fields",
    "Technical Fields",
    "Unknown Fields",
    "Source API",
    "Sample API",
    "Error",
)

FIELD_MODE_CHOICES: Sequence[str] = ("minimal", "standard", "full")
FIELD_GROUP_STANDARD = "standard"
FIELD_GROUP_FLEXFIELD = "flexfield"

CATEGORY_BUSINESS = "BUSINESS"
CATEGORY_SYSTEM = "SYSTEM"
CATEGORY_FLEXFIELD = "FLEXFIELD"
CATEGORY_RELATIONSHIP = "RELATIONSHIP"
CATEGORY_TECHNICAL = "TECHNICAL"
CATEGORY_UNKNOWN = "UNKNOWN"

FIELD_CATEGORIES: Sequence[str] = (
    CATEGORY_BUSINESS,
    CATEGORY_SYSTEM,
    CATEGORY_FLEXFIELD,
    CATEGORY_RELATIONSHIP,
    CATEGORY_TECHNICAL,
    CATEGORY_UNKNOWN,
)

DEFAULT_FILTER_CONFIG: Dict[str, Any] = {
    "classification": {
        "system_fields": [
            "CreatedBy",
            "CreationDate",
            "LastUpdatedBy",
            "LastUpdateDate",
            "LastUpdateLogin",
            "ObjectVersionNumber",
            "LastUpdatedByUser",
        ],
        "system_patterns": [
            r".*UID$",
            r".*GUID$",
            r".*WhoColumn.*",
            r".*VersionNumber$",
        ],
        "flex_patterns": [
            r".*DFF.*",
            r".*EFF.*",
            r".*DescriptiveFlexfield.*",
            r".*ExtensibleFlexfield.*",
            r".*Attribute\d+$",
            r".*GlobalAttribute\d+$",
            r".*_c$",
            r"^__FLEX_.*",
        ],
        "relationship_patterns": [
            r".*Link$",
            r".*Links$",
            r".*Href$",
            r".*Url$",
            r".*Child.*",
        ],
        "technical_patterns": [
            r".*Internal.*",
            r".*Hash$",
            r".*Checksum$",
            r".*Token$",
        ],
    },
    "scoring": {
        "business": 50,
        "required": 30,
        "in_sample": 20,
        "system": -50,
        "relationship": -30,
        "technical": -20,
        "flexfield": 0,
        "unknown": 0,
    },
    "modes": {
        "minimal": {
            "include_categories": [CATEGORY_BUSINESS],
            "require_required_or_in_sample": True,
        },
        "standard": {
            "include_categories": [CATEGORY_BUSINESS, CATEGORY_FLEXFIELD],
            "minimum_score": 0,
        },
        "full": {
            "exclude_categories": [CATEGORY_RELATIONSHIP],
        },
    },
}

TEMPLATE_OBJECT_KEYS: Sequence[str] = (
    "object_name",
    "object",
    "resource",
    "resource_name",
    "business_object",
)

TEMPLATE_FIELD_KEYS: Sequence[str] = (
    "field_name",
    "field",
    "name",
    "target_field",
)

TEMPLATE_COLLECTION_KEYS: Sequence[str] = (
    "fields",
    "mappings",
    "templates",
    "items",
)


class MetadataError(Exception):
    """Base error for metadata retrieval."""


class InvalidUrlError(MetadataError):
    """Raised when the base URL is invalid."""


class CredentialError(MetadataError):
    """Raised when credentials are missing or invalid."""


class AuthenticationError(MetadataError):
    """Raised when the API rejects authentication."""


class ObjectNotFoundError(MetadataError):
    """Raised when a business object could not be resolved."""


class ApiResponseError(MetadataError):
    """Raised when the service returns an unexpected response."""


@dataclass
class ObjectResult:
    object_name: str
    status: str
    resolved_endpoint: Optional[str]
    field_count: int
    fields: List[Dict[str, Any]]
    sample_endpoint: Optional[str] = None
    sample_field_names: List[str] = dataclass_field(default_factory=list)
    sample_field_types: Dict[str, str] = dataclass_field(default_factory=dict)
    sample_warning: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ObjectResolution:
    requested_name: str
    resolved_name: Optional[str]
    service: Optional[str]
    suggestions: List[str]
    note: Optional[str] = None


def log(message: str) -> None:
    print(message, flush=True)


def prompt_yes_no(question: str, default: Optional[bool] = None) -> bool:
    suffix = " [Y/n]" if default is True else " [y/N]" if default is False else " [y/n]"
    while True:
        answer = input(f"{question}{suffix}: ").strip().lower()
        if not answer and default is not None:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def sanitize_secret_value(raw_value: str, env_var_name: str = "VC_BEARER_TOKEN") -> str:
    """Extract a usable token if the user pasted a full command by mistake."""
    value = (raw_value or "").strip().strip("\"'")
    if not value:
        return value

    assignment_match = re.search(
        rf"(?:export\s+)?{re.escape(env_var_name)}\s*=\s*['\"]?([^'\"\s]+)",
        value,
        flags=re.IGNORECASE,
    )
    if assignment_match:
        return assignment_match.group(1).strip()

    bearer_match = re.search(r"\bBearer\s+([^\s'\"]+)", value, flags=re.IGNORECASE)
    if bearer_match:
        return bearer_match.group(1).strip()

    jwt_match = re.search(r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", value)
    if jwt_match:
        return jwt_match.group(0).strip()

    return value


def normalize_base_url(base_url: str) -> str:
    raw = (base_url or "").strip()
    if not raw:
        raise InvalidUrlError("Invalid URL ''. Expected format like https://<env-host>/")

    markdown_match = re.search(r"\((https?://[^)]+)\)", raw)
    if markdown_match:
        raw = markdown_match.group(1).strip()
    else:
        angle_match = re.search(r"<(https?://[^>]+)>", raw)
        if angle_match:
            raw = angle_match.group(1).strip()
        else:
            bare_match = re.search(r"https?://[^\s>]+", raw)
            if bare_match:
                raw = bare_match.group(0).strip()

    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidUrlError(
            f"Invalid URL '{base_url}'. Expected format like https://<env-host>/"
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def lower_camel(value: str) -> str:
    if not value:
        return value
    return value[:1].lower() + value[1:]


def normalize_object_input(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""

    # If the user pastes a full endpoint or URL, extract the resource segment.
    parsed = urllib.parse.urlparse(raw)
    path = parsed.path if (parsed.scheme or parsed.netloc or raw.startswith("/")) else raw
    parts = [part for part in path.split("/") if part]
    if "resources" in parts:
        resource_index = parts.index("resources")
        if resource_index + 2 < len(parts):
            candidate = parts[resource_index + 2]
            if candidate.lower() != "describe":
                return candidate.strip()
    if raw.startswith("/") and parts:
        return parts[-1].strip()
    return raw.strip()


def object_variants(object_name: str) -> List[str]:
    clean = normalize_object_input(object_name).strip().strip("/")
    return unique_preserve_order([clean, lower_camel(clean), clean.lower()])


def normalize_lookup_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def pluralization_variants(name: str) -> List[str]:
    clean = (name or "").strip()
    if not clean:
        return []

    variants = [clean]
    lowered = clean.lower()
    if lowered.endswith("ies") and len(clean) > 3:
        variants.append(clean[:-3] + "y")
    elif lowered.endswith("s") and len(clean) > 1:
        variants.append(clean[:-1])
    else:
        if lowered.endswith("y") and len(clean) > 1:
            variants.append(clean[:-1] + "ies")
        variants.append(clean + "s")
    return unique_preserve_order(variants)


def known_alias_candidates(name: str) -> List[str]:
    alias_map = {
        "account": ["Accounts"],
        "accounts": ["Accounts"],
        "contact": ["Contacts"],
        "contacts": ["Contacts"],
        "lead": ["Leads"],
        "leads": ["Leads"],
        "activity": ["Activities"],
        "activities": ["Activities"],
        "opportunity": ["Opportunities"],
        "opportunities": ["Opportunities"],
        "gl": ["Ledgers"],
        "ledger": ["Ledgers"],
        "ledgers": ["Ledgers"],
        "generalledger": ["Ledgers"],
        "invoice": ["Invoices"],
        "invoices": ["Invoices"],
        "apinvoice": ["Invoices"],
        "payablesinvoice": ["Invoices"],
        "supplierinvoice": ["Invoices"],
        "customerinvoice": ["ReceivablesInvoices", "ReceivablesTransactions"],
        "receivablesinvoice": ["ReceivablesInvoices", "ReceivablesTransactions"],
        "journal": ["Journals", "JournalBatches"],
        "journals": ["Journals", "JournalBatches"],
    }
    return alias_map.get(normalize_lookup_name(name), [])


def choose_services(service: str) -> List[str]:
    if service == "auto":
        return ["fscmRestApi", "crmRestApi"]
    return [service]


def parse_object_names(raw_values: Sequence[str]) -> List[str]:
    names: List[str] = []
    for raw_value in raw_values:
        for piece in re.split(r"[,\n]", raw_value):
            cleaned = normalize_object_input(piece).strip().strip("/")
            if cleaned:
                names.append(cleaned)
    return unique_preserve_order(names)


def api_version_candidates(service: str) -> List[str]:
    # latest is preferred, but certain Fusion/CX resources resolve correctly only on
    # a concrete versioned endpoint in some pods.
    common_versions = ["latest", "11.13.18.05"]
    if service in {"crmRestApi", "fscmRestApi"}:
        return common_versions
    return ["latest"]


def resolve_service_order(object_name: str, service: str) -> List[str]:
    if service != "auto":
        return [service]

    normalized = object_name.strip().lower()
    if normalized in CRM_OBJECT_HINTS or normalized.startswith(
        ("account", "opportunit", "contact", "lead")
    ):
        return ["crmRestApi", "fscmRestApi"]
    return ["fscmRestApi", "crmRestApi"]


def endpoint_candidates(base_url: str, object_name: str, service: str) -> List[str]:
    candidates: List[str] = []
    for svc in resolve_service_order(object_name, service):
        for version in api_version_candidates(svc):
            for obj in object_variants(object_name):
                encoded_obj = urllib.parse.quote(obj, safe="")
                candidates.append(f"{base_url}/{svc}/resources/{version}/{encoded_obj}/describe")
                candidates.append(f"{base_url}/{svc}/metadata-catalog/{encoded_obj}")
    return unique_preserve_order(candidates)


def extract_resource_names(payload: Any) -> List[str]:
    names: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("name", "resource", "resourceName", "ResourceName"):
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    names.append(value.strip())

            href = node.get("href")
            if isinstance(href, str) and "/resources/latest/" in href:
                parsed = urllib.parse.urlparse(href)
                parts = [part for part in parsed.path.split("/") if part]
                if "latest" in parts:
                    latest_index = parts.index("latest")
                    if latest_index + 1 < len(parts):
                        names.append(parts[latest_index + 1])

            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return [
        name
        for name in unique_preserve_order(names)
        if normalize_lookup_name(name) not in {"latest", "items", "links"}
    ]


def fetch_service_catalog(
    base_url: str,
    service: str,
    headers: Dict[str, str],
    timeout: int,
) -> List[str]:
    resources: List[str] = []
    errors: List[str] = []
    for version in api_version_candidates(service):
        try:
            payload = fetch_json(f"{base_url}/{service}/resources/{version}", headers=headers, timeout=timeout)
            resources.extend(extract_resource_names(payload))
        except AuthenticationError:
            raise
        except MetadataError as exc:
            errors.append(f"{service}/{version}: {exc}")

    if resources:
        return unique_preserve_order(resources)

    raise ApiResponseError(
        "Unable to read FA resource catalog for service "
        f"'{service}'. Tried versions: {', '.join(api_version_candidates(service))}. "
        + " | ".join(errors)
    )


def prompt_retry_token_by_source(token_source: str, previous_token: str, auth_retry_timeout: int) -> str:
    if token_source == "clipboard":
        return wait_for_new_clipboard_token(previous_token, timeout_seconds=auth_retry_timeout)
    return prompt_retry_token_after_auth_failure()


def validate_fa_connection(
    base_url: str,
    token: str,
    timeout: int,
    service: str,
    token_source: str,
    auth_retry_timeout: int,
    verbose: bool = False,
) -> Tuple[str, Dict[str, List[str]]]:
    current_token = token
    auth_retry_used = False
    services = choose_services(service)

    while True:
        headers = {"Accept": "application/json", "Authorization": f"Bearer {current_token}"}
        catalogs: Dict[str, List[str]] = {}
        accessible_services: List[str] = []
        errors: List[str] = []

        try:
            for current_service in services:
                if verbose:
                    log(f"Testing FA connection via {current_service} resource catalog...")
                try:
                    resources = fetch_service_catalog(base_url, current_service, headers=headers, timeout=timeout)
                    catalogs[current_service] = resources
                    accessible_services.append(current_service)
                except AuthenticationError:
                    raise
                except MetadataError as exc:
                    errors.append(f"{current_service}: {exc}")

            if accessible_services:
                log("FA environment connection test succeeded.")
                for current_service in accessible_services:
                    log(f"- {current_service}: discovered {len(catalogs.get(current_service, []))} REST resources")
                if errors:
                    log("Some service catalogs were unavailable during validation:")
                    for error in errors:
                        log(f"  - {error}")
                return current_token, catalogs

            raise ApiResponseError(
                "Could not validate access to the FA REST catalogs. " + " | ".join(errors)
            )
        except AuthenticationError as exc:
            log(f"Connection test failed authentication: {exc}")
            if auth_retry_used:
                raise
            current_token = prompt_retry_token_by_source(token_source, current_token, auth_retry_timeout)
            auth_retry_used = True
            log("Retrying FA environment connection test with the refreshed bearer token...")


def build_resource_index(resource_catalogs: Dict[str, List[str]], service: str) -> Tuple[Dict[str, List[Tuple[str, str]]], List[str]]:
    index: Dict[str, List[Tuple[str, str]]] = {}
    available_names: List[str] = []
    for current_service in choose_services(service):
        for resource_name in resource_catalogs.get(current_service, []):
            index.setdefault(normalize_lookup_name(resource_name), []).append((current_service, resource_name))
            available_names.append(resource_name)
    return index, unique_preserve_order(available_names)


def trusted_object_resolution(requested_name: str, service: str) -> Optional[Tuple[str, str]]:
    candidates = [requested_name]
    candidates.extend(pluralization_variants(requested_name))
    candidates.extend(known_alias_candidates(requested_name))

    services = choose_services(service)
    for candidate in unique_preserve_order(candidates):
        normalized = normalize_lookup_name(candidate)
        for current_service in services:
            canonical = TRUSTED_STANDARD_OBJECTS.get(current_service, {}).get(normalized)
            if canonical:
                return current_service, canonical
    return None


def probe_object_candidate(
    base_url: str,
    candidate_name: str,
    service: str,
    headers: Dict[str, str],
    timeout: int,
    verbose: bool = False,
) -> bool:
    try:
        resolve_metadata(
            base_url=base_url,
            object_name=candidate_name,
            service=service,
            headers=headers,
            timeout=timeout,
            verbose=verbose,
        )
        return True
    except AuthenticationError:
        raise
    except MetadataError:
        return False


def resolve_object_names(
    requested_names: Sequence[str],
    resource_catalogs: Dict[str, List[str]],
    service: str,
    base_url: str,
    token: str,
    timeout: int,
    verbose: bool = False,
) -> List[ObjectResolution]:
    resource_index, available_names = build_resource_index(resource_catalogs, service)
    normalized_to_name = {normalize_lookup_name(name): name for name in available_names}
    resolutions: List[ObjectResolution] = []
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}

    for requested_name in requested_names:
        normalized_requested = normalize_lookup_name(requested_name)
        direct_matches = resource_index.get(normalized_requested, [])
        candidate_matches: List[Tuple[str, str]] = list(direct_matches)
        for candidate in unique_preserve_order(pluralization_variants(requested_name) + known_alias_candidates(requested_name)):
            candidate_matches.extend(resource_index.get(normalize_lookup_name(candidate), []))

        probe_candidates: List[Tuple[str, str]] = []
        seen_probe_candidates: set[Tuple[str, str]] = set()

        def add_probe_candidate(candidate_service: str, candidate_name: str) -> None:
            key = (candidate_service, candidate_name)
            if candidate_name and key not in seen_probe_candidates:
                seen_probe_candidates.add(key)
                probe_candidates.append(key)

        for candidate_service, candidate_name in candidate_matches:
            add_probe_candidate(candidate_service, candidate_name)

        for candidate_name in unique_preserve_order(
            [requested_name] + pluralization_variants(requested_name) + known_alias_candidates(requested_name)
        ):
            for candidate_service in choose_services(service):
                add_probe_candidate(candidate_service, candidate_name)

        resolved_name: Optional[str] = None
        resolved_service: Optional[str] = None
        for candidate_service, candidate_name in probe_candidates:
            if probe_object_candidate(
                base_url=base_url,
                candidate_name=candidate_name,
                service=candidate_service,
                headers=headers,
                timeout=timeout,
                verbose=False,
            ):
                resolved_service = candidate_service
                resolved_name = candidate_name
                break

        if resolved_name and resolved_service:
            note = None
            if resolved_name != requested_name:
                note = f"Suggested corrected object name '{resolved_name}' for '{requested_name}'."
            resolutions.append(
                ObjectResolution(
                    requested_name,
                    resolved_name,
                    resolved_service,
                    unique_preserve_order(name for _, name in candidate_matches),
                    note,
                )
            )
            continue

        trusted_resolution = trusted_object_resolution(requested_name, service)
        if trusted_resolution:
            resolved_service, resolved_name = trusted_resolution
            note = (
                f"Using built-in standard FA object name '{resolved_name}' for '{requested_name}' "
                "even though endpoint pre-validation could not confirm it."
            )
            resolutions.append(
                ObjectResolution(
                    requested_name,
                    resolved_name,
                    resolved_service,
                    unique_preserve_order(name for _, name in candidate_matches) or [resolved_name],
                    note,
                )
            )
            continue

        close_keys = difflib.get_close_matches(normalized_requested, list(normalized_to_name.keys()), n=5, cutoff=0.55)
        suggestions = [normalized_to_name[key] for key in close_keys]
        suggestions.extend(name for name in known_alias_candidates(requested_name) if name in available_names)
        resolutions.append(
            ObjectResolution(
                requested_name,
                None,
                None,
                unique_preserve_order(suggestions),
                None,
            )
        )

    return resolutions


def prompt_for_validated_object_names(
    initial_objects: Sequence[str],
    resource_catalogs: Dict[str, List[str]],
    service: str,
    base_url: str,
    token: str,
    timeout: int,
    verbose: bool = False,
) -> List[str]:
    current_objects = list(initial_objects)

    while True:
        resolutions = resolve_object_names(
            current_objects,
            resource_catalogs,
            service,
            base_url,
            token,
            timeout,
            verbose=verbose,
        )
        unresolved = [item for item in resolutions if not item.resolved_name]

        for item in resolutions:
            if item.note:
                log(item.note)

        if not unresolved:
            return [item.resolved_name for item in resolutions if item.resolved_name]

        already_resolved = [item.resolved_name for item in resolutions if item.resolved_name]

        log("The following object names did not match available FA REST resources:")
        for item in unresolved:
            log(f"- {item.requested_name}")
            if item.suggestions:
                log(f"  Suggestions: {', '.join(item.suggestions)}")

        replacement = prompt_value(
            "Re-enter only the unresolved object name(s), comma-separated, using the suggested FA REST resource names, or type CANCEL to stop"
        )
        if replacement.strip().lower() == "cancel":
            raise CredentialError("Object validation was cancelled.")
        replacement_objects = parse_object_names([replacement])
        if not replacement_objects:
            print("Please enter at least one valid object name.")
            continue

        current_objects = unique_preserve_order(
            [name for name in already_resolved if name] + replacement_objects
        )


def parse_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "t", "yes", "y", "1", "required", "mandatory"}:
            return True
        if lowered in {"false", "f", "no", "n", "0", "optional"}:
            return False
    return None


def first_present(mapping: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def additional_metadata(mapping: Dict[str, Any]) -> Dict[str, Any]:
    extras: Dict[str, Any] = {}
    for key in ADDITIONAL_METADATA_KEYS:
        if key in mapping and mapping[key] not in (None, "", []):
            extras[key] = mapping[key]
    return extras


def normalize_length_value(metadata: Dict[str, Any], data_type: Optional[str]) -> Any:
    for key in ("length", "maxLength", "minLength"):
        value = metadata.get(key)
        if value not in (None, "", []):
            return value

    if (data_type or "").lower() in {"string", "attachment"}:
        precision_value = metadata.get("precision")
        if precision_value not in (None, "", []):
            return precision_value

    return None


def normalize_description_value(metadata: Dict[str, Any]) -> str:
    for key in ("title", "description", "label"):
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def normalize_source_api_value(source_api: str) -> str:
    raw = (source_api or "").strip()
    if not raw:
        return ""

    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme and parsed.netloc:
        path = parsed.path or "/"
        if parsed.query:
            return f"{path}?{parsed.query}"
        return path

    return raw


def normalize_field_structure(
    field: Dict[str, Any],
    source_api: str,
    sample_field_names: Optional[Iterable[str]] = None,
    sample_field_types: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    metadata = field.get("additional_metadata", {}) or {}
    data_type = field.get("data_type")
    field_name = str(field.get("field_name") or field.get("fieldName") or "")
    sample_name_set = {str(name) for name in (sample_field_names or []) if name}
    existing_in_sample = parse_bool(field.get("in_sample", field.get("inSample")))
    in_sample = (
        field_name in sample_name_set
        if sample_name_set
        else bool(existing_in_sample) if existing_in_sample is not None else False
    )
    sample_value_type = (
        field.get("sample_value_type")
        or field.get("sampleValueType")
        or (sample_field_types or {}).get(field_name)
    )
    normalized = {
        "field_name": field_name,
        "data_type": data_type,
        "required": field.get("required"),
        "in_sample": in_sample,
        "sample_value_type": sample_value_type,
        "length": field.get("length") if field.get("length") not in (None, "") else normalize_length_value(metadata, data_type),
        "field_group": field.get("field_group"),
        "flexfield_type": field.get("flexfield_type"),
        "category": field.get("category"),
        "score": field.get("score"),
        "confidence": field.get("confidence"),
        "is_mappable": field.get("is_mappable", field.get("isMappable")),
        "description": field.get("description") or normalize_description_value(metadata),
        "source_api": normalize_source_api_value(field.get("source_api") or source_api),
        "additional_metadata": metadata,
    }
    return normalized


def normalize_fields(
    fields: List[Dict[str, Any]],
    source_api: str,
    sample_field_names: Optional[Iterable[str]] = None,
    sample_field_types: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    return [
        normalize_field_structure(field, source_api, sample_field_names, sample_field_types)
        for field in fields
    ]


def value_for_keys(mapping: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def load_text_source(source: str, timeout: int) -> str:
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(
            source,
            headers={"Accept": "application/json, application/x-yaml, text/yaml, text/plain"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode(
                response.headers.get_content_charset() or "utf-8",
                errors="replace",
            )

    return Path(source).read_text(encoding="utf-8")


def parse_template_document(source: str, content: str) -> Any:
    suffix = Path(urllib.parse.urlparse(source).path).suffix.lower()
    if suffix == ".json":
        return json.loads(content)

    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise ApiResponseError(
                "YAML template support requires PyYAML to be installed, or use JSON templates instead."
            ) from exc
        return yaml.safe_load(content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise ApiResponseError(
                f"Could not parse template source '{source}' as JSON, and YAML support is unavailable."
            ) from exc
        return yaml.safe_load(content)


def expand_template_sources(sources: Sequence[str]) -> List[str]:
    expanded: List[str] = []
    for source in sources:
        parsed = urllib.parse.urlparse(source)
        if parsed.scheme in {"http", "https"}:
            expanded.append(source)
            continue

        path = Path(source)
        if path.is_dir():
            for pattern in ("*.json", "*.yaml", "*.yml"):
                expanded.extend(str(item) for item in sorted(path.glob(pattern)))
        else:
            expanded.append(str(path))
    return unique_preserve_order(expanded)


def extract_template_entries(document: Any, source: str, inherited_object: Optional[str] = None) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []

    if isinstance(document, list):
        for item in document:
            entries.extend(extract_template_entries(item, source, inherited_object))
        return entries

    if not isinstance(document, dict):
        return entries

    local_object = value_for_keys(document, TEMPLATE_OBJECT_KEYS) or inherited_object

    for key in TEMPLATE_COLLECTION_KEYS:
        value = document.get(key)
        if isinstance(value, list):
            for item in value:
                entries.extend(extract_template_entries(item, source, str(local_object) if local_object else None))
            return entries
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                next_object = str(local_object) if local_object else str(nested_key)
                entries.extend(extract_template_entries(nested_value, source, next_object))
            return entries

    field_name = value_for_keys(document, TEMPLATE_FIELD_KEYS)
    if field_name:
        payload = {
            key: value
            for key, value in document.items()
            if key not in set(TEMPLATE_OBJECT_KEYS) | set(TEMPLATE_FIELD_KEYS)
        }
        entries.append(
            {
                "object_name": str(local_object) if local_object else "*",
                "field_name": str(field_name),
                "source": source,
                "data": payload,
            }
        )
        return entries

    for key, value in document.items():
        if isinstance(value, (list, dict)):
            next_object = str(local_object) if local_object else str(key)
            entries.extend(extract_template_entries(value, source, next_object))

    return entries


def load_mapping_templates(sources: Sequence[str], timeout: int) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    template_index: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for source in expand_template_sources(sources):
        content = load_text_source(source, timeout)
        document = parse_template_document(source, content)
        entries = extract_template_entries(document, source)
        for entry in entries:
            object_key = normalize_lookup_name(entry.get("object_name", "*")) or "*"
            field_key = normalize_lookup_name(entry.get("field_name", ""))
            if not field_key:
                continue
            template_index.setdefault(object_key, {}).setdefault(field_key, []).append(entry)
    return template_index


def deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge_dict(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def normalize_field_mode(value: Optional[str]) -> str:
    mode = (value or "standard").strip().lower()
    if mode not in FIELD_MODE_CHOICES:
        raise ApiResponseError(
            f"Unsupported field mode '{value}'. Choose one of: {', '.join(FIELD_MODE_CHOICES)}."
        )
    return mode


def load_filter_config(source: Optional[str], timeout: int) -> Tuple[Dict[str, Any], str]:
    if not source:
        return copy.deepcopy(DEFAULT_FILTER_CONFIG), "built-in defaults"

    content = load_text_source(source, timeout)
    document = parse_template_document(source, content)
    if not isinstance(document, dict):
        raise ApiResponseError(
            "Filter configuration must parse to a JSON/YAML object with classification, scoring, and/or modes keys."
        )

    return deep_merge_dict(DEFAULT_FILTER_CONFIG, document), source


def matches_any_pattern(value: str, patterns: Sequence[str]) -> bool:
    for pattern in patterns:
        try:
            if re.match(pattern, value):
                return True
        except re.error as exc:
            raise ApiResponseError(f"Invalid filter regex '{pattern}': {exc}") from exc
    return False


def infer_sample_value_type(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "string"


def extract_first_sample_record(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("items", "Items"):
            items = payload.get(key)
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        return item
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                return item
    return None


def extract_sample_field_names(sample_record: Optional[Dict[str, Any]]) -> List[str]:
    if not sample_record:
        return []
    return [str(key) for key in sample_record.keys() if key]


def extract_sample_field_types(sample_record: Optional[Dict[str, Any]]) -> Dict[str, str]:
    if not sample_record:
        return {}
    field_types: Dict[str, str] = {}
    for key, value in sample_record.items():
        inferred = infer_sample_value_type(value)
        if inferred:
            field_types[str(key)] = inferred
    return field_types


def detect_flexfield_type(field_name: str, filter_config: Dict[str, Any]) -> Optional[str]:
    name = (field_name or "").strip()
    if not name:
        return None

    lowered = name.lower()
    if lowered.startswith("__flex_"):
        return "Context"
    if "descriptiveflexfield" in lowered or "dff" in lowered:
        return "DFF"
    if "extensibleflexfield" in lowered or "eff" in lowered:
        return "EFF"
    if re.match(r".*attribute\d+$", name, flags=re.IGNORECASE):
        return "Attribute"
    if lowered.endswith("_c"):
        return "Custom"
    if matches_any_pattern(name, filter_config.get("classification", {}).get("flex_patterns", [])):
        return "Configured"
    return None


def determine_field_category(field: Dict[str, Any], filter_config: Dict[str, Any]) -> str:
    field_name = str(field.get("field_name", "") or "").strip()
    if not field_name:
        return CATEGORY_UNKNOWN

    classification_rules = filter_config.get("classification", {})
    normalized_name = normalize_lookup_name(field_name)
    system_fields = {
        normalize_lookup_name(str(name))
        for name in classification_rules.get("system_fields", [])
        if str(name).strip()
    }

    if normalized_name in system_fields:
        return CATEGORY_SYSTEM

    sample_value_type = str(field.get("sample_value_type", "") or "").lower()
    data_type = str(field.get("data_type", "") or "").lower()
    if sample_value_type in {"array", "object"} or data_type in {"array", "object"}:
        return CATEGORY_RELATIONSHIP

    if matches_any_pattern(field_name, classification_rules.get("system_patterns", [])):
        return CATEGORY_SYSTEM
    if matches_any_pattern(field_name, classification_rules.get("flex_patterns", [])):
        return CATEGORY_FLEXFIELD
    if matches_any_pattern(field_name, classification_rules.get("relationship_patterns", [])):
        return CATEGORY_RELATIONSHIP
    if matches_any_pattern(field_name, classification_rules.get("technical_patterns", [])):
        return CATEGORY_TECHNICAL
    return CATEGORY_BUSINESS


def calculate_field_score(field: Dict[str, Any], filter_config: Dict[str, Any]) -> int:
    scoring_rules = filter_config.get("scoring", {})
    score = 0
    category = field.get("category")

    if category == CATEGORY_BUSINESS:
        score += int(scoring_rules.get("business", 50))
    elif category == CATEGORY_SYSTEM:
        score += int(scoring_rules.get("system", -50))
    elif category == CATEGORY_RELATIONSHIP:
        score += int(scoring_rules.get("relationship", -30))
    elif category == CATEGORY_TECHNICAL:
        score += int(scoring_rules.get("technical", -20))
    elif category == CATEGORY_FLEXFIELD:
        score += int(scoring_rules.get("flexfield", 0))
    else:
        score += int(scoring_rules.get("unknown", 0))

    if bool(field.get("required")):
        score += int(scoring_rules.get("required", 30))
    if bool(field.get("in_sample")):
        score += int(scoring_rules.get("in_sample", 20))
    return score


def calculate_confidence(field: Dict[str, Any]) -> float:
    signals = [
        bool(field.get("required")),
        bool(field.get("in_sample")),
        bool(str(field.get("description", "") or "").strip()),
    ]
    return round(sum(1 for signal in signals if signal) / 3, 2)


def apply_output_aliases(field: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(field)
    enriched["fieldName"] = enriched.get("field_name", "")
    enriched["dataType"] = enriched.get("data_type")
    enriched["inSample"] = bool(enriched.get("in_sample"))
    enriched["isMappable"] = bool(enriched.get("is_mappable"))
    enriched["fieldGroup"] = enriched.get("field_group")
    enriched["sampleValueType"] = enriched.get("sample_value_type")
    return enriched


def classify_field(field: Dict[str, Any], filter_config: Dict[str, Any]) -> Dict[str, Any]:
    classified = dict(field)
    category = determine_field_category(classified, filter_config)
    classified["category"] = category
    classified["field_group"] = (
        FIELD_GROUP_FLEXFIELD if category == CATEGORY_FLEXFIELD else FIELD_GROUP_STANDARD
    )
    classified["flexfield_type"] = (
        detect_flexfield_type(str(classified.get("field_name", "")), filter_config)
        if category == CATEGORY_FLEXFIELD
        else None
    )
    classified["score"] = calculate_field_score(classified, filter_config)
    classified["confidence"] = calculate_confidence(classified)
    classified["is_mappable"] = (
        category == CATEGORY_BUSINESS and classified.get("data_type") not in (None, "")
    )
    return apply_output_aliases(classified)


def category_count_map(fields: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {category: 0 for category in FIELD_CATEGORIES}
    for field in fields:
        category = str(field.get("category") or CATEGORY_UNKNOWN)
        counts[category] = counts.get(category, 0) + 1
    return counts


def should_include_field(field: Dict[str, Any], field_mode: str, filter_config: Dict[str, Any]) -> bool:
    mode_rules = filter_config.get("modes", {}).get(field_mode, {})
    category = str(field.get("category") or CATEGORY_UNKNOWN)

    if field_mode == "minimal":
        include_categories = set(mode_rules.get("include_categories", [CATEGORY_BUSINESS]))
        require_required_or_in_sample = bool(mode_rules.get("require_required_or_in_sample", True))
        if category not in include_categories:
            return False
        if not require_required_or_in_sample:
            return True
        return bool(field.get("required")) or bool(field.get("in_sample"))

    if field_mode == "standard":
        include_categories = set(
            mode_rules.get("include_categories", [CATEGORY_BUSINESS, CATEGORY_FLEXFIELD])
        )
        minimum_score = int(mode_rules.get("minimum_score", 0))
        return category in include_categories and int(field.get("score", 0)) > minimum_score

    exclude_categories = set(mode_rules.get("exclude_categories", [CATEGORY_RELATIONSHIP]))
    return category not in exclude_categories


def apply_field_filters(
    fields: List[Dict[str, Any]],
    field_mode: str,
    filter_config: Dict[str, Any],
) -> Dict[str, Any]:
    retrieved_fields = [classify_field(field, filter_config) for field in fields]
    selected_fields = [
        field for field in retrieved_fields if should_include_field(field, field_mode, filter_config)
    ]

    retrieved_category_counts = category_count_map(retrieved_fields)
    selected_category_counts = category_count_map(selected_fields)
    retrieved_flexfields = retrieved_category_counts.get(CATEGORY_FLEXFIELD, 0)
    selected_flexfields = selected_category_counts.get(CATEGORY_FLEXFIELD, 0)

    return {
        "retrieved_fields": retrieved_fields,
        "selected_fields": selected_fields,
        "retrieved_field_count": len(retrieved_fields),
        "sample_field_count": sum(1 for field in retrieved_fields if field.get("in_sample")),
        "retrieved_standard_field_count": len(retrieved_fields) - retrieved_flexfields,
        "retrieved_flexfield_count": retrieved_flexfields,
        "selected_standard_field_count": len(selected_fields) - selected_flexfields,
        "selected_flexfield_count": selected_flexfields,
        "retrieved_category_counts": retrieved_category_counts,
        "selected_category_counts": selected_category_counts,
    }


def apply_enrichment_templates(
    object_name: str,
    fields: List[Dict[str, Any]],
    template_index: Dict[str, Dict[str, List[Dict[str, Any]]]],
) -> List[Dict[str, Any]]:
    if not template_index:
        return fields

    object_keys = unique_preserve_order([normalize_lookup_name(object_name), "*"])
    enriched_fields: List[Dict[str, Any]] = []

    for field in fields:
        field_key = normalize_lookup_name(str(field.get("field_name", "")))
        matches: List[Dict[str, Any]] = []
        for object_key in object_keys:
            matches.extend(template_index.get(object_key, {}).get(field_key, []))

        if not matches:
            enriched_fields.append(field)
            continue

        merged_enrichment: Dict[str, Any] = {}
        template_sources: List[str] = []
        for match in matches:
            merged_enrichment.update(match.get("data", {}))
            if match.get("source"):
                template_sources.append(str(match["source"]))

        enriched = dict(field)
        enriched["enrichment"] = {
            "template_sources": unique_preserve_order(template_sources),
            "template_data": merged_enrichment,
        }
        if not enriched.get("description"):
            enriched["description"] = (
                merged_enrichment.get("description")
                or merged_enrichment.get("title")
                or merged_enrichment.get("label")
                or enriched.get("description")
            )
        enriched_fields.append(enriched)

    return enriched_fields


def normalize_discovery_payload(
    discovery_payload: Dict[str, Any],
    template_index: Optional[Dict[str, Dict[str, List[Dict[str, Any]]]]] = None,
    field_mode: str = "standard",
    filter_config: Optional[Dict[str, Any]] = None,
    filter_config_source: str = "built-in defaults",
) -> Dict[str, Any]:
    resolved_field_mode = normalize_field_mode(field_mode)
    resolved_filter_config = copy.deepcopy(filter_config or DEFAULT_FILTER_CONFIG)
    normalized_objects: List[Dict[str, Any]] = []
    retrieved_total_fields = 0
    exported_total_fields = 0
    exported_standard_fields = 0
    exported_flexfields = 0
    sampled_total_fields = 0
    retrieved_category_totals = category_count_map([])
    exported_category_totals = category_count_map([])
    enrichment_enabled = bool(template_index)

    for item in discovery_payload.get("objects", []):
        source_api = item.get("resolved_endpoint") or ""
        sample_field_names = item.get("sample_field_names", []) or []
        sample_field_types = item.get("sample_field_types", {}) or {}
        normalized_fields = normalize_fields(
            item.get("fields", []) or [],
            source_api,
            sample_field_names,
            sample_field_types,
        )
        if template_index:
            normalized_fields = apply_enrichment_templates(
                str(item.get("object_name", "")),
                normalized_fields,
                template_index,
            )
        filter_result = apply_field_filters(
            normalized_fields,
            resolved_field_mode,
            resolved_filter_config,
        )
        normalized_item = dict(item)
        normalized_item["field_mode"] = resolved_field_mode
        normalized_item["fields"] = filter_result["selected_fields"]
        normalized_item["retrieved_field_count"] = filter_result["retrieved_field_count"]
        normalized_item["retrieved_standard_field_count"] = filter_result[
            "retrieved_standard_field_count"
        ]
        normalized_item["retrieved_flexfield_count"] = filter_result[
            "retrieved_flexfield_count"
        ]
        normalized_item["sample_field_count"] = filter_result["sample_field_count"]
        normalized_item["field_count"] = len(filter_result["selected_fields"])
        normalized_item["standard_field_count"] = filter_result["selected_standard_field_count"]
        normalized_item["flexfield_count"] = filter_result["selected_flexfield_count"]
        normalized_item["retrieved_category_counts"] = filter_result["retrieved_category_counts"]
        normalized_item["category_counts"] = filter_result["selected_category_counts"]
        normalized_objects.append(normalized_item)
        retrieved_total_fields += filter_result["retrieved_field_count"]
        exported_total_fields += len(filter_result["selected_fields"])
        exported_standard_fields += filter_result["selected_standard_field_count"]
        exported_flexfields += filter_result["selected_flexfield_count"]
        sampled_total_fields += filter_result["sample_field_count"]
        for category, count in filter_result["retrieved_category_counts"].items():
            retrieved_category_totals[category] = retrieved_category_totals.get(category, 0) + count
        for category, count in filter_result["selected_category_counts"].items():
            exported_category_totals[category] = exported_category_totals.get(category, 0) + count

    normalized_payload = dict(discovery_payload)
    normalized_payload["objects"] = normalized_objects
    normalized_payload["summary"] = {
        **discovery_payload.get("summary", {}),
        "field_mode": resolved_field_mode,
        "successful": sum(1 for item in normalized_objects if item.get("status") == "SUCCESS"),
        "failed": sum(1 for item in normalized_objects if item.get("status") != "SUCCESS"),
        "retrieved_total_fields": retrieved_total_fields,
        "sampled_total_fields": sampled_total_fields,
        "total_fields": exported_total_fields,
        "standard_fields": exported_standard_fields,
        "flexfields": exported_flexfields,
        "retrieved_category_counts": retrieved_category_totals,
        "category_counts": exported_category_totals,
    }
    normalized_payload["filtering"] = {
        "mode": resolved_field_mode,
        "config_source": filter_config_source,
        "available_modes": list(FIELD_MODE_CHOICES),
        "pipeline": ["raw_fields", "classification", "scoring", "filtering", "output"],
    }
    normalized_payload["processing_layers"] = {
        "discovery": "REST calls against Fusion FA endpoints",
        "sampling": "Collection endpoint sample retrieval (limit=1) when available",
        "enrichment": "Optional mapping-template merge" if enrichment_enabled else "Disabled",
        "filtering": {
            "mode": resolved_field_mode,
            "config_source": filter_config_source,
            "pipeline": ["classification", "scoring", "filtering"],
            "separates_standard_fields_and_flexfields": True,
        },
        "normalization": list(CANONICAL_FIELD_COLUMNS),
        "output": ["JSON", "Excel"],
    }
    return normalized_payload


def build_field_record(
    field_name: Optional[str],
    mapping: Dict[str, Any],
    required_names: Optional[Iterable[str]] = None,
) -> Optional[Dict[str, Any]]:
    if not field_name:
        field_name = first_present(mapping, FIELD_NAME_KEYS)
    if not field_name:
        return None

    data_type = first_present(mapping, FIELD_TYPE_KEYS)
    required = None

    for key in REQUIRED_KEYS:
        if key in mapping:
            parsed = parse_bool(mapping[key])
            if parsed is not None:
                required = not parsed if key == "nullable" else parsed
                break

    required_name_set = {name for name in (required_names or []) if name}
    if required is None and field_name in required_name_set:
        required = True

    return {
        "field_name": str(field_name),
        "data_type": str(data_type) if data_type is not None else None,
        "required": required,
        "additional_metadata": additional_metadata(mapping),
    }


def merge_field_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for record in records:
        name = record["field_name"]
        if name not in merged:
            merged[name] = record
            continue

        current = merged[name]
        if not current.get("data_type") and record.get("data_type"):
            current["data_type"] = record["data_type"]
        if current.get("required") is None and record.get("required") is not None:
            current["required"] = record["required"]
        current["additional_metadata"].update(record.get("additional_metadata", {}))
    return list(merged.values())


def extract_fields(payload: Any) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []

    def walk(node: Any, required_names: Optional[Iterable[str]] = None) -> None:
        if isinstance(node, dict):
            local_required = (
                node.get("required") if isinstance(node.get("required"), list) else required_names
            )

            properties = node.get("properties")
            if isinstance(properties, dict):
                for prop_name, prop_schema in properties.items():
                    if isinstance(prop_schema, dict):
                        record = build_field_record(prop_name, prop_schema, local_required)
                        if record:
                            found.append(record)

            for key in ("fields", "attributes", "items"):
                value = node.get(key)
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            record = build_field_record(None, item, local_required)
                            if record:
                                found.append(record)

            for key in ("fields", "attributes"):
                value = node.get(key)
                if isinstance(value, dict):
                    for attr_name, attr_schema in value.items():
                        if isinstance(attr_schema, dict):
                            record = build_field_record(attr_name, attr_schema, local_required)
                            if record:
                                found.append(record)

            for value in node.values():
                walk(value, local_required)

        elif isinstance(node, list):
            for item in node:
                walk(item, required_names)

    walk(payload)
    return sorted(merge_field_records(found), key=lambda item: item["field_name"].lower())


def extract_error_message(body_text: str) -> str:
    body_text = (body_text or "").strip()
    if not body_text:
        return ""

    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        return body_text[:500]

    candidates: List[str] = []
    if isinstance(payload, dict):
        for key in ("title", "detail", "message", "error", "o:errorDetails"):
            value = payload.get(key)
            if value:
                candidates.append(str(value))
        if isinstance(payload.get("errors"), list):
            for item in payload["errors"]:
                if isinstance(item, dict):
                    message = item.get("message") or item.get("detail") or item.get("title")
                    if message:
                        candidates.append(str(message))
    return " | ".join(candidates)[:500] if candidates else body_text[:500]


def fetch_json(url: str, headers: Dict[str, str], timeout: int) -> Any:
    request = urllib.request.Request(url=url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode(
                response.headers.get_content_charset() or "utf-8", errors="replace"
            )
            if not body.strip():
                raise ApiResponseError(f"Empty response received from {url}")
            try:
                return json.loads(body)
            except json.JSONDecodeError as exc:
                raise ApiResponseError(
                    f"Expected JSON from {url}, but received non-JSON content."
                ) from exc
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = extract_error_message(body)
        if exc.code in {401, 403}:
            raise AuthenticationError(
                f"Authentication failed ({exc.code}) for {url}. {message}"
            ) from exc
        if exc.code == 404:
            raise ObjectNotFoundError(f"Not found ({exc.code}) for {url}. {message}") from exc
        raise ApiResponseError(f"HTTP {exc.code} returned from {url}. {message}") from exc
    except urllib.error.URLError as exc:
        raise ApiResponseError(f"Network error while calling {url}: {exc.reason}") from exc


def resource_collection_candidates(base_url: str, object_name: str, service: str) -> List[str]:
    candidates: List[str] = []
    for svc in resolve_service_order(object_name, service):
        for version in api_version_candidates(svc):
            for obj in object_variants(object_name):
                encoded_obj = urllib.parse.quote(obj, safe="")
                # Some Fusion pods respond correctly only to the bare collection URL,
                # while others tolerate paging/query params like limit=1.
                candidates.append(f"{base_url}/{svc}/resources/{version}/{encoded_obj}?limit=1")
                candidates.append(f"{base_url}/{svc}/resources/{version}/{encoded_obj}")
    return unique_preserve_order(candidates)


def fetch_sample_record(
    base_url: str,
    object_name: str,
    service: str,
    headers: Dict[str, str],
    timeout: int,
    verbose: bool = False,
) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    messages: List[str] = []
    for url in resource_collection_candidates(base_url, object_name, service):
        if verbose:
            log(f"  Trying sample endpoint: {url}")
        try:
            payload = fetch_json(url, headers=headers, timeout=timeout)
        except AuthenticationError:
            raise
        except MetadataError as exc:
            messages.append(str(exc))
            continue

        sample_record = extract_first_sample_record(payload)
        if sample_record is not None:
            return url, sample_record, None
        messages.append(f"No sample record returned from {url}")

    return None, None, messages[0] if messages else "No sample record returned from collection endpoint."


def collection_endpoint_exists(
    base_url: str,
    object_name: str,
    service: str,
    headers: Dict[str, str],
    timeout: int,
    verbose: bool = False,
) -> bool:
    for url in resource_collection_candidates(base_url, object_name, service):
        if verbose:
            log(f"  Probing collection endpoint: {url}")
        request = urllib.request.Request(url=url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status < 400:
                    return True
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise AuthenticationError(
                    f"Authentication failed ({exc.code}) for {url}."
                ) from exc
            if exc.code in {404, 405, 500}:
                continue
            continue
        except urllib.error.URLError:
            continue
    return False


def resolve_metadata(
    base_url: str,
    object_name: str,
    service: str,
    headers: Dict[str, str],
    timeout: int,
    verbose: bool = False,
) -> Tuple[str, Any]:
    errors: List[str] = []
    for url in endpoint_candidates(base_url, object_name, service):
        if verbose:
            log(f"  Trying endpoint: {url}")
        try:
            payload = fetch_json(url, headers=headers, timeout=timeout)
            return url, payload
        except AuthenticationError:
            raise
        except ObjectNotFoundError as exc:
            errors.append(str(exc))
        except ApiResponseError as exc:
            errors.append(str(exc))

    joined_errors = "\n- ".join(errors[:6])
    raise ObjectNotFoundError(
        "Unable to resolve a metadata endpoint for the requested object. "
        f"Tried common describe/catalog endpoints for '{object_name}'."
        + (f"\n- {joined_errors}" if joined_errors else "")
    )


def prompt_value(prompt_text: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    response = input(f"{prompt_text}{suffix}: ").strip()
    return response or (default or "")


def prompt_service(default: str = "auto") -> str:
    while True:
        value = prompt_value("REST service family (auto, crmRestApi, fscmRestApi)", default)
        if value in {"auto", "crmRestApi", "fscmRestApi"}:
            return value
        print("Please enter one of: auto, crmRestApi, fscmRestApi")


def prompt_object_names() -> List[str]:
    while True:
        raw = prompt_value("Object name(s), comma-separated (example: Accounts, Opportunities)")
        objects = parse_object_names([raw])
        if objects:
            return objects
        print("Please enter at least one object name.")


def looks_like_jwt(token: str) -> bool:
    parts = (token or "").split(".")
    return len(parts) == 3 and all(parts)


def prompt_bearer_token(visible: bool = False) -> str:
    prompt_text = "Enter OAuth bearer token"
    prompt_hint = " (JWT / bearer token, not password)"

    try:
        if visible:
            token = input(f"{prompt_text}{prompt_hint}: ").strip()
        else:
            token = getpass.getpass(f"{prompt_text}{prompt_hint} [hidden input]: ").strip()
    except (EOFError, KeyboardInterrupt):
        raise CredentialError("Token entry was cancelled.")
    except Exception:
        visible_value = input(f"{prompt_text}{prompt_hint} [visible fallback]: ").strip()
        token = visible_value

    token = sanitize_secret_value(token)
    if not token:
        raise CredentialError("No bearer token was provided.")
    if not looks_like_jwt(token):
        log(
            "Warning: the value entered does not look like a JWT bearer token. "
            "Make sure you paste the OAuth access token, not your password."
        )
    return token


def prompt_retry_token_after_auth_failure() -> str:
    log("")
    log("Authentication failed (401/403). Please provide a fresh bearer token to retry.")
    log(
        "Paste a fresh OAuth bearer token and press Enter, or copy it to the macOS "
        "clipboard and press Enter on an empty line to use the clipboard value."
    )

    try:
        entered_value = input("Fresh bearer token (blank = clipboard): ").strip()
    except (EOFError, KeyboardInterrupt):
        raise CredentialError("Authentication retry was cancelled.")

    if entered_value:
        token = sanitize_secret_value(entered_value)
        if not token:
            raise CredentialError("No bearer token was provided for retry.")
        if not looks_like_jwt(token):
            log(
                "Warning: the retry value does not look like a JWT bearer token. "
                "Make sure you paste the OAuth access token."
            )
        return token

    return token_from_clipboard()


def token_from_env(env_var_name: str) -> str:
    token = sanitize_secret_value(os.getenv(env_var_name, ""), env_var_name=env_var_name)
    if not token:
        raise CredentialError(
            f"Environment variable '{env_var_name}' is not set or is empty."
        )
    if not looks_like_jwt(token):
        log(
            f"Warning: value from {env_var_name} does not look like a JWT bearer token. "
            "Make sure it contains the OAuth access token."
        )
    return token


def token_from_clipboard() -> str:
    try:
        result = subprocess.run(
            ["pbpaste"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise CredentialError("pbpaste is not available on this machine.") from exc
    except subprocess.CalledProcessError as exc:
        raise CredentialError("Unable to read token from clipboard using pbpaste.") from exc

    token = sanitize_secret_value(result.stdout or "")
    if not token:
        raise CredentialError("Clipboard is empty. Copy the bearer token first, then rerun.")
    if not looks_like_jwt(token):
        log(
            "Warning: clipboard value does not look like a JWT bearer token. "
            "Make sure you copied the OAuth access token, not another value."
        )
    return token


def wait_for_new_clipboard_token(previous_token: str, timeout_seconds: int = 120) -> str:
    log("")
    log(
        "Authentication failed (401/403). Copy a fresh bearer token to the macOS "
        "clipboard now."
    )
    log(
        f"Waiting up to {timeout_seconds} seconds for the clipboard value to change; "
        "no Enter key press is required."
    )

    previous_value = sanitize_secret_value(previous_token or "")
    deadline = time.time() + timeout_seconds
    last_warning = 0.0

    while time.time() < deadline:
        try:
            result = subprocess.run(
                ["pbpaste"],
                check=True,
                capture_output=True,
                text=True,
            )
            candidate = sanitize_secret_value(result.stdout or "")
            if candidate and candidate != previous_value:
                if not looks_like_jwt(candidate):
                    raise CredentialError(
                        "The new clipboard value does not look like a JWT bearer token."
                    )
                log("Detected a new clipboard token.")
                return candidate
        except subprocess.CalledProcessError:
            pass
        except CredentialError as exc:
            now = time.time()
            if now - last_warning >= 5:
                log(f"Still waiting: {exc}")
                last_warning = now

        time.sleep(1)

    raise CredentialError(
        "Timed out waiting for a new bearer token in the clipboard."
    )


def discover_object_metadata(
    base_url: str,
    objects: Sequence[str],
    service: str,
    token: str,
    timeout: int,
    verbose: bool = False,
    token_source: str = "prompt",
    auth_retry_timeout: int = 120,
) -> Dict[str, Any]:
    current_token = token
    results: List[ObjectResult] = []

    for object_name in objects:
        log(f"Fetching metadata for object '{object_name}'...")
        auth_retry_used = False

        while True:
            headers = {"Accept": "application/json", "Authorization": f"Bearer {current_token}"}
            try:
                resolved_endpoint, payload = resolve_metadata(
                    base_url=base_url,
                    object_name=object_name,
                    service=service,
                    headers=headers,
                    timeout=timeout,
                    verbose=verbose,
                )
                sample_endpoint, sample_record, sample_warning = fetch_sample_record(
                    base_url=base_url,
                    object_name=object_name,
                    service=service,
                    headers=headers,
                    timeout=timeout,
                    verbose=verbose,
                )
                sample_field_names = extract_sample_field_names(sample_record)
                sample_field_types = extract_sample_field_types(sample_record)
                fields = normalize_fields(
                    extract_fields(payload),
                    resolved_endpoint,
                    sample_field_names,
                    sample_field_types,
                )
                log(
                    f"Retrieved {len(fields)} fields for '{object_name}' from {resolved_endpoint}"
                )
                if sample_endpoint and sample_field_names:
                    log(
                        f"Sample retrieval found {len(sample_field_names)} populated fields via {sample_endpoint}"
                    )
                elif sample_warning and verbose:
                    log(f"Sample retrieval note for '{object_name}': {sample_warning}")
                results.append(
                    ObjectResult(
                        object_name=object_name,
                        status="SUCCESS",
                        resolved_endpoint=resolved_endpoint,
                        field_count=len(fields),
                        fields=fields,
                        sample_endpoint=sample_endpoint,
                        sample_field_names=sample_field_names,
                        sample_field_types=sample_field_types,
                        sample_warning=sample_warning,
                    )
                )
                break
            except AuthenticationError as exc:
                log(f"Authentication failed for '{object_name}': {exc}")
                if auth_retry_used:
                    results.append(
                        ObjectResult(
                            object_name=object_name,
                            status="ERROR",
                            resolved_endpoint=None,
                            field_count=0,
                            fields=[],
                            error=str(exc),
                        )
                    )
                    break

                try:
                    if token_source == "clipboard":
                        current_token = wait_for_new_clipboard_token(
                            current_token,
                            timeout_seconds=auth_retry_timeout,
                        )
                    else:
                        current_token = prompt_retry_token_after_auth_failure()
                except CredentialError as retry_exc:
                    results.append(
                        ObjectResult(
                            object_name=object_name,
                            status="ERROR",
                            resolved_endpoint=None,
                            field_count=0,
                            fields=[],
                            error=f"{exc} | Retry cancelled: {retry_exc}",
                        )
                    )
                    break

                auth_retry_used = True
                log(f"Retrying '{object_name}' with the refreshed bearer token...")
            except MetadataError as exc:
                log(f"Failed to retrieve '{object_name}': {exc}")
                results.append(
                    ObjectResult(
                        object_name=object_name,
                        status="ERROR",
                        resolved_endpoint=None,
                        field_count=0,
                        fields=[],
                        error=str(exc),
                    )
                )
                break

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "service": service,
        "objects_requested": list(objects),
        "objects": [
            {
                "object_name": item.object_name,
                "status": item.status,
                "resolved_endpoint": item.resolved_endpoint,
                "field_count": item.field_count,
                "fields": item.fields,
                "sample_endpoint": item.sample_endpoint,
                "sample_field_names": item.sample_field_names,
                "sample_field_types": item.sample_field_types,
                "sample_warning": item.sample_warning,
                "error": item.error,
            }
            for item in results
        ],
        "summary": {
            "requested": len(objects),
            "successful": sum(1 for item in results if item.status == "SUCCESS"),
            "failed": sum(1 for item in results if item.status != "SUCCESS"),
            "total_fields": sum(item.field_count for item in results),
        },
    }


def fetch_object_metadata(
    base_url: str,
    objects: Sequence[str],
    service: str,
    token: str,
    timeout: int,
    verbose: bool = False,
    token_source: str = "prompt",
    auth_retry_timeout: int = 120,
) -> Dict[str, Any]:
    """Backward-compatible wrapper for the discovery layer."""
    return discover_object_metadata(
        base_url=base_url,
        objects=objects,
        service=service,
        token=token,
        timeout=timeout,
        verbose=verbose,
        token_source=token_source,
        auth_retry_timeout=auth_retry_timeout,
    )


def default_output_dir() -> Path:
    return Path(__file__).resolve().parent / "output"


def ensure_output_prefix(
    output_prefix: Optional[str],
    output_dir: Path,
    default_name: Optional[str] = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_prefix:
        prefix_name = Path(output_prefix).name
        if not prefix_name:
            prefix_name = Path(output_prefix).stem
        if Path(prefix_name).suffix:
            prefix_name = Path(prefix_name).stem
    else:
        prefix_name = default_name or f"fusion_object_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", prefix_name).strip("._") or "fusion_object_metadata"
    return output_dir / safe_name


def write_json_output(data: Dict[str, Any], json_path: Path) -> None:
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def output_normalized_metadata(data: Dict[str, Any], prefix: Path) -> Tuple[Path, Path]:
    json_path = prefix.with_suffix(".json")
    xlsx_path = prefix.with_suffix(".xlsx")
    write_json_output(data, json_path)
    export_to_excel(data, xlsx_path)
    return json_path, xlsx_path


def safe_sheet_name(name: str, used_names: set[str]) -> str:
    cleaned = re.sub(r"[:\\/?*\[\]]", "_", (name or "").strip()) or "Object"
    cleaned = cleaned[:31]
    candidate = cleaned
    suffix_counter = 2

    while candidate in used_names:
        suffix = f"_{suffix_counter}"
        candidate = f"{cleaned[: max(0, 31 - len(suffix))]}{suffix}"
        suffix_counter += 1

    used_names.add(candidate)
    return candidate


def build_summary_sheet_rows(data: Dict[str, Any]) -> List[List[Any]]:
    rows: List[List[Any]] = [list(SUMMARY_SHEET_COLUMNS)]
    for item in data.get("objects", []):
        category_counts = item.get("category_counts", {}) or {}
        rows.append(
            [
                item.get("object_name", ""),
                item.get("status", ""),
                item.get("field_mode", data.get("filtering", {}).get("mode", "standard")),
                item.get("retrieved_field_count", item.get("field_count", 0)),
                item.get("sample_field_count", 0),
                item.get("field_count", 0),
                category_counts.get(CATEGORY_BUSINESS, 0),
                category_counts.get(CATEGORY_SYSTEM, 0),
                category_counts.get(CATEGORY_FLEXFIELD, 0),
                category_counts.get(CATEGORY_RELATIONSHIP, 0),
                category_counts.get(CATEGORY_TECHNICAL, 0),
                category_counts.get(CATEGORY_UNKNOWN, 0),
                normalize_source_api_value(item.get("resolved_endpoint", "") or ""),
                normalize_source_api_value(item.get("sample_endpoint", "") or ""),
                item.get("error", "") or "",
            ]
        )
    return rows


def build_object_sheet_rows(
    item: Dict[str, Any],
    field_group_filter: Optional[str] = None,
) -> List[List[Any]]:
    rows: List[List[Any]] = [list(CANONICAL_FIELD_COLUMNS)]

    error = item.get("error")
    if error:
        rows.append([
            "ERROR",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            error,
            normalize_source_api_value(item.get("resolved_endpoint", "") or ""),
        ])
        return rows

    fields = item.get("fields", [])
    if field_group_filter:
        fields = [
            field
            for field in fields
            if str(field.get("field_group") or FIELD_GROUP_STANDARD).lower() == field_group_filter
        ]

    for field in fields:
        normalized = normalize_field_structure(field, item.get("resolved_endpoint", "") or "")
        rows.append(
            [
                normalized.get("field_name", ""),
                normalized.get("category", CATEGORY_UNKNOWN),
                normalized.get("data_type", "") or "",
                normalized.get("required", ""),
                normalized.get("in_sample", False),
                normalized.get("score", 0),
                normalized.get("confidence", 0),
                normalized.get("is_mappable", False),
                normalized.get("length", "") if normalized.get("length") is not None else "",
                normalized.get("description", ""),
                normalized.get("source_api", ""),
            ]
        )

    return rows


def excel_column_name(index_1_based: int) -> str:
    result = ""
    current = index_1_based
    while current:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


def worksheet_xml(rows: List[List[Any]]) -> str:
    row_xml: List[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: List[str] = []
        for col_index, value in enumerate(row, start=1):
            cell_ref = f"{excel_column_name(col_index)}{row_index}"
            if value is None or value == "":
                cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t></t></is></c>')
            elif isinstance(value, bool):
                text = "TRUE" if value else "FALSE"
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr"><is><t>{xml_escape(text)}</t></is></c>'
                )
            elif isinstance(value, (int, float)):
                cells.append(f'<c r="{cell_ref}"><v>{value}</v></c>')
            else:
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr"><is><t xml:space="preserve">'
                    f'{xml_escape(str(value))}</t></is></c>'
                )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        '</worksheet>'
    )


def write_excel_workbook(output_path: Path, sheets: List[Tuple[str, List[List[Any]]]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content_types_overrides = [
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    workbook_sheets: List[str] = []
    workbook_rels: List[str] = []

    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as workbook:
        for index, (sheet_name, rows) in enumerate(sheets, start=1):
            workbook.writestr(f"xl/worksheets/sheet{index}.xml", worksheet_xml(rows))
            workbook_sheets.append(
                f'<sheet name="{xml_escape(sheet_name[:31])}" sheetId="{index}" r:id="rId{index}"/>'
            )
            workbook_rels.append(
                f'<Relationship Id="rId{index}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{index}.xml"/>'
            )
            content_types_overrides.append(
                f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            )

        workbook.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            + "".join(content_types_overrides)
            + '</Types>',
        )
        workbook.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            '<Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
            'Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
            'Target="docProps/app.xml"/>'
            '</Relationships>',
        )
        workbook.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<workbookPr/>'
            '<bookViews><workbookView xWindow="0" yWindow="0" windowWidth="24000" windowHeight="12000"/>'
            '</bookViews>'
            f'<sheets>{"".join(workbook_sheets)}</sheets>'
            '</workbook>',
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(workbook_rels)
            + f'<Relationship Id="rId{len(sheets) + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/>'
            '</Relationships>',
        )
        workbook.writestr(
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>',
        )

        created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        workbook.writestr(
            "docProps/core.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties '
            'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<dc:title>Fusion Object Metadata</dc:title>'
            '<dc:creator>fusion-data-definition-architect</dc:creator>'
            '<cp:lastModifiedBy>fusion-data-definition-architect</cp:lastModifiedBy>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
            '</cp:coreProperties>',
        )
        workbook.writestr(
            "docProps/app.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
            'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            '<Application>fusion-data-definition-architect</Application>'
            f'<TitlesOfParts><vt:vector size="{len(sheets)}" baseType="lpstr">'
            + "".join(f'<vt:lpstr>{xml_escape(name[:31])}</vt:lpstr>' for name, _ in sheets)
            + '</vt:vector></TitlesOfParts>'
            f'<HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>{len(sheets)}</vt:i4></vt:variant></vt:vector></HeadingPairs>'
            '</Properties>',
        )


def export_to_excel(data: Dict[str, Any], output_path: Path) -> None:
    used_sheet_names: set[str] = set()
    sheets: List[Tuple[str, List[List[Any]]]] = [
        (safe_sheet_name("Summary", used_sheet_names), build_summary_sheet_rows(data))
    ]

    for item in data.get("objects", []):
        sheets.append(
            (
                safe_sheet_name(f"{item.get('object_name', 'Object')}_Standard", used_sheet_names),
                build_object_sheet_rows(item, field_group_filter=FIELD_GROUP_STANDARD),
            )
        )

        if item.get("retrieved_flexfield_count", 0) or item.get("flexfield_count", 0):
            sheets.append(
                (
                    safe_sheet_name(f"{item.get('object_name', 'Object')}_Flexfields", used_sheet_names),
                    build_object_sheet_rows(item, field_group_filter=FIELD_GROUP_FLEXFIELD),
                )
            )

    if len(sheets) == 1 and not data.get("objects", []):
        sheets.append(("Objects", [["No object metadata was returned."]]))

    write_excel_workbook(output_path, sheets)


def print_run_summary(data: Dict[str, Any], json_path: Path, xlsx_path: Path) -> None:
    print("\nMetadata retrieval complete.\n")
    for item in data.get("objects", []):
        if item.get("status") == "SUCCESS":
            retrieved_field_count = item.get("retrieved_field_count", item.get("field_count", 0))
            sample_field_count = item.get("sample_field_count", 0)
            category_counts = item.get("category_counts", {}) or {}
            print(
                f"✓ {item.get('object_name')}: metadata {retrieved_field_count}, sample {sample_field_count}, "
                f"exported {item.get('field_count', 0)} in {item.get('field_mode', data.get('filtering', {}).get('mode', 'standard'))} mode "
                f"(business {category_counts.get(CATEGORY_BUSINESS, 0)} / flexfields {category_counts.get(CATEGORY_FLEXFIELD, 0)}) "
                f"via {item.get('resolved_endpoint')}"
            )
        else:
            print(f"✗ {item.get('object_name')}: {item.get('error', 'Unknown error')}" )

    summary = data.get("summary", {})
    print("\nSummary:")
    print(f"- Requested objects: {summary.get('requested', 0)}")
    print(f"- Successful: {summary.get('successful', 0)}")
    print(f"- Failed: {summary.get('failed', 0)}")
    print(f"- Field mode: {summary.get('field_mode', data.get('filtering', {}).get('mode', 'standard'))}")
    print(f"- Retrieved fields before filtering: {summary.get('retrieved_total_fields', summary.get('total_fields', 0))}")
    print(f"- Fields seen in sample rows: {summary.get('sampled_total_fields', 0)}")
    print(f"- Total fields exported: {summary.get('total_fields', 0)}")
    print(f"- Business fields exported: {(summary.get('category_counts', {}) or {}).get(CATEGORY_BUSINESS, 0)}")
    print(f"- System fields exported: {(summary.get('category_counts', {}) or {}).get(CATEGORY_SYSTEM, 0)}")
    print(f"- Flexfields exported: {summary.get('flexfields', 0)}")
    print(f"- Relationship fields exported: {(summary.get('category_counts', {}) or {}).get(CATEGORY_RELATIONSHIP, 0)}")
    print(f"- Technical fields exported: {(summary.get('category_counts', {}) or {}).get(CATEGORY_TECHNICAL, 0)}")
    print(f"- JSON output: {json_path}")
    print(f"- Excel output: {xlsx_path}")


def load_json_input(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ApiResponseError(f"Input JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ApiResponseError(f"Input JSON file is not valid JSON: {path}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interactively retrieve Oracle Fusion/CX object metadata and export it to JSON + Excel."
    )
    parser.add_argument(
        "--base-url",
        help="Environment base URL, e.g. https://<env-host>/ . If omitted, the script prompts for it.",
    )
    parser.add_argument(
        "--objects",
        nargs="*",
        help="One or many object names. You can separate values with spaces or commas.",
    )
    parser.add_argument(
        "--service",
        choices=("auto", "crmRestApi", "fscmRestApi"),
        default=None,
        help="REST service family. If omitted, the script prompts with default 'auto'.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds (default: 60).",
    )
    parser.add_argument(
        "--output-prefix",
        help="Output file name prefix. Generated files are always written to scripts/output as <prefix>.json and <prefix>.xlsx.",
    )
    parser.add_argument(
        "--input-json",
        help="Skip API calls and convert an existing JSON output file to Excel.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print endpoint-by-endpoint progress while retrieving metadata.",
    )
    parser.add_argument(
        "--field-mode",
        choices=tuple(FIELD_MODE_CHOICES),
        default="standard",
        help="Filtering mode for exported fields: minimal, standard, or full (default: standard).",
    )
    parser.add_argument(
        "--filter-config",
        help="Optional JSON/YAML file or URL with filtering rules that override the built-in field-mode defaults.",
    )
    parser.add_argument(
        "--token-visible",
        action="store_true",
        help="Prompt for the bearer token using normal visible input instead of hidden input.",
    )
    parser.add_argument(
        "--token-from-clipboard",
        action="store_true",
        help="Read the bearer token from the macOS clipboard using pbpaste instead of prompting.",
    )
    parser.add_argument(
        "--token-env-var",
        help="Read the bearer token from the given environment variable instead of prompting.",
    )
    parser.add_argument(
        "--auth-retry-timeout",
        type=int,
        default=120,
        help="Seconds to wait for a refreshed clipboard token after a 401/403 when using --token-from-clipboard.",
    )
    parser.add_argument(
        "--mapping-template-source",
        action="append",
        default=[],
        help="Optional enrichment source(s): local JSON/YAML file, directory, or HTTP(S) URL containing mapping templates.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = default_output_dir()

    try:
        filter_config, filter_config_source = load_filter_config(args.filter_config, args.timeout)

        if args.input_json:
            input_json_path = Path(args.input_json)
            source_data = load_json_input(input_json_path)
            template_index = load_mapping_templates(args.mapping_template_source, args.timeout)
            data = normalize_discovery_payload(
                source_data,
                template_index,
                field_mode=args.field_mode,
                filter_config=filter_config,
                filter_config_source=filter_config_source,
            )
            prefix = ensure_output_prefix(
                args.output_prefix,
                output_dir,
                default_name=f"{input_json_path.stem}_export",
            )
            json_path, xlsx_path = output_normalized_metadata(data, prefix)
            print(f"Normalized JSON output created: {json_path}")
            print(f"Excel output created: {xlsx_path}")
            return 0

        if args.base_url:
            base_url = normalize_base_url(args.base_url)
        else:
            has_fa_url = prompt_yes_no(
                "Do you have an Oracle Fusion Applications (FA) environment URL?",
                default=True,
            )
            if not has_fa_url:
                log(
                    "No FA environment URL was provided. The script will not execute live metadata retrieval. "
                    "Use the skill in knowledge-only mode to list standard fields based on built-in knowledge."
                )
                return 0
            base_url = normalize_base_url(
                prompt_value("Environment Base URL (example: https://<env-host>/)")
            )

        service = args.service or "auto"

        if args.token_from_clipboard and args.token_env_var:
            raise CredentialError(
                "Use only one of --token-from-clipboard or --token-env-var."
            )

        using_supplied_token_source = bool(
            args.token_from_clipboard or args.token_env_var or args.token_visible
        )
        if not using_supplied_token_source:
            has_bearer_token = prompt_yes_no(
                "Can you obtain a bearer token for this FA instance? This is the only supported connection method.",
                default=True,
            )
            if not has_bearer_token:
                log(
                    "Without a bearer token, the script will not execute live retrieval. "
                    "Use the skill in knowledge-only mode to list standard fields based on built-in knowledge."
                )
                return 0

        if args.token_from_clipboard:
            log("\nReading bearer token from clipboard. It is used only in memory for this run.\n")
            token = token_from_clipboard()
            token_source = "clipboard"
        elif args.token_env_var:
            log(
                f"\nReading bearer token from environment variable '{args.token_env_var}'. "
                "It is used only in memory for this run.\n"
            )
            token = token_from_env(args.token_env_var)
            token_source = "env"
        else:
            log("\nThe script will now prompt for a bearer token. It is used only in memory for this run.\n")
            token = prompt_bearer_token(visible=args.token_visible)
            token_source = "prompt"

        log("Token received. Validating access to the FA environment...\n")
        token, resource_catalogs = validate_fa_connection(
            base_url=base_url,
            token=token,
            timeout=args.timeout,
            service=service,
            token_source=token_source,
            auth_retry_timeout=args.auth_retry_timeout,
            verbose=args.verbose,
        )

        objects = parse_object_names(args.objects or [])
        if not objects:
            objects = prompt_object_names()

        objects = prompt_for_validated_object_names(
            objects,
            resource_catalogs,
            service,
            base_url,
            token,
            args.timeout,
            verbose=args.verbose,
        )

        log("Starting object metadata retrieval with validated FA REST object names...\n")

        discovery_data = discover_object_metadata(
            base_url=base_url,
            objects=objects,
            service=service,
            token=token,
            timeout=args.timeout,
            verbose=args.verbose,
            token_source=token_source,
            auth_retry_timeout=args.auth_retry_timeout,
        )
        template_index = load_mapping_templates(args.mapping_template_source, args.timeout)
        data = normalize_discovery_payload(
            discovery_data,
            template_index,
            field_mode=args.field_mode,
            filter_config=filter_config,
            filter_config_source=filter_config_source,
        )

        prefix = ensure_output_prefix(args.output_prefix, output_dir)
        json_path, xlsx_path = output_normalized_metadata(data, prefix)
        print_run_summary(data, json_path, xlsx_path)

        if data.get("summary", {}).get("successful", 0) == 0:
            return 5
        return 0

    except InvalidUrlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except CredentialError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    except AuthenticationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 4
    except ObjectNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 5
    except ApiResponseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 6
    except KeyboardInterrupt:
        print("\nCancelled by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())

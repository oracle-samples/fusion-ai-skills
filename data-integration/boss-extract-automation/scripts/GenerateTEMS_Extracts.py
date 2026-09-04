#!/usr/bin/env python3
"""BOSS extract automation with staged commands, preflight validation, and JSON summaries."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import socket
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

DEBUG = False


def load_env_file() -> None:
    env_path = Path(__file__).resolve().parent.parent / "assets" / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


load_env_file()

ENV = {
    "BOSS_HOST": os.getenv("BOSS_HOST"),
    "IDCS_HOST": os.getenv("IDCS_HOST"),
    "IDCS_CLIENT_ID": os.getenv("IDCS_CLIENT_ID"),
    "IDCS_CLIENT_SECRET": os.getenv("IDCS_CLIENT_SECRET"),
    "BOSS_USERNAME": os.getenv("BOSS_USERNAME"),
    "BOSS_PASSWORD": os.getenv("BOSS_PASSWORD"),
    "ESS_USERNAME": os.getenv("ESS_USERNAME") or os.getenv("BOSS_USERNAME"),
    "ESS_PASSWORD": os.getenv("ESS_PASSWORD") or os.getenv("BOSS_PASSWORD"),
    "IDCS_BOSS_SCOPE": os.getenv("IDCS_BOSS_SCOPE"),
    "IDCS_BATCH_SCOPE": os.getenv("IDCS_BATCH_SCOPE"),
    "DEFAULT_OWNER": os.getenv("DEFAULT_OWNER"),
    "DEFAULT_OWNER_ROLE": os.getenv("DEFAULT_OWNER_ROLE", "HCM_Job_Roles"),
    "DEFAULT_EMAILS": os.getenv("DEFAULT_EMAILS"),
    "DEFAULT_NOTIFICATION": os.getenv("DEFAULT_NOTIFICATION", "Y,Y,Y"),
    "OUTPUT_DIR": os.getenv("OUTPUT_DIR", os.path.join(os.getcwd(), "output")),
    "DB_USER": os.getenv("DB_USER"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
    "DB_CONNECT_STRING": os.getenv("DB_CONNECT_STRING"),
    "DB_WALLET_LOCATION": os.getenv("DB_WALLET_LOCATION"),
    "DB_WALLET_PASSWORD": os.getenv("DB_WALLET_PASSWORD"),
    "POLL_INTERVAL_SEC": os.getenv("POLL_INTERVAL_SEC", "5"),
    "POLL_TIMEOUT_SEC": os.getenv("POLL_TIMEOUT_SEC", "900"),
    "DEFAULT_PVO": os.getenv("DEFAULT_PVO"),
    "CATALOG_CSV_PATH": os.getenv("CATALOG_CSV_PATH"),
}

COMMAND_CHOICES = ["run", "preflight", "validate-view", "create-extract", "monitor", "download"]
FREQUENCY_CHOICES = ["Immediate", "Simple", "Hourly", "Daily", "Weekly", "Monthly", "Yearly"]
EXTRACT_TYPE_CHOICES = ["Full", "Incremental"]
OUTPUT_DATA_FORMAT_CHOICES = ["CSV", "JSON"]
METADATA_SOURCE_CHOICES = ["auto", "fixture", "mapping", "db"]
ALLOW_INSECURE_HTTP = os.getenv("ALLOW_INSECURE_HTTP", "").strip().lower() in {"1", "true", "yes", "y"}

REQUIRED_ENV = {
    "live": [
        "BOSS_HOST",
        "IDCS_HOST",
        "IDCS_CLIENT_ID",
        "IDCS_CLIENT_SECRET",
        "BOSS_USERNAME",
        "BOSS_PASSWORD",
        "IDCS_BOSS_SCOPE",
        "IDCS_BATCH_SCOPE",
        "DEFAULT_OWNER",
        "DEFAULT_EMAILS",
        "DB_USER",
        "DB_PASSWORD",
        "DB_CONNECT_STRING",
        "DB_WALLET_LOCATION",
        "DB_WALLET_PASSWORD",
    ],
    "network_only": ["BOSS_HOST", "IDCS_HOST"],
    "db": ["DB_USER", "DB_PASSWORD", "DB_CONNECT_STRING", "DB_WALLET_LOCATION", "DB_WALLET_PASSWORD"],
}

TERMINAL_BATCH_STATES = {"SUCCEEDED", "COMPLETED", "ERROR", "FAILED", "CANCELLED", "PAUSED", "WARNING"}
TERMINAL_ESS_STATES = {"SUCCEEDED", "ERROR", "WARNING", "CANCELLED"}


class HttpError(RuntimeError):
    pass


class PreflightError(RuntimeError):
    pass


@dataclass
class Summary:
    status: str = "ok"
    command: str = ""
    failed_step: Optional[str] = None
    missing_dependencies: List[str] = field(default_factory=list)
    missing_env: List[str] = field(default_factory=list)
    unsupported_environment: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    created_ids: Dict[str, Any] = field(default_factory=dict)
    downloaded_files: List[str] = field(default_factory=list)
    names: Dict[str, str] = field(default_factory=dict)
    planned_api_calls: List[Dict[str, str]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def fail(self, step: str, message: str, *, status: str = "error") -> None:
        self.status = status
        self.failed_step = step
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "status": self.status,
            "failed_step": self.failed_step,
            "missing_dependencies": self.missing_dependencies,
            "missing_env": self.missing_env,
            "unsupported_environment": self.unsupported_environment,
            "warnings": self.warnings,
            "created_ids": self.created_ids,
            "downloaded_files": self.downloaded_files,
            "names": self.names,
            "planned_api_calls": self.planned_api_calls,
            "details": self.details,
        }
        return payload


def emit_summary(summary: Summary, exit_code: Optional[int] = None) -> None:
    print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
    if exit_code is not None:
        sys.exit(exit_code)


def getenv_required(keys: List[str]) -> List[str]:
    return [key for key in keys if not (ENV.get(key) or "").strip()]


def parse_float_env(name: str, default: float) -> float:
    raw = ENV.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise PreflightError(f"Environment variable {name} must be numeric, got: {raw!r}") from exc


POLL_INTERVAL_SEC = parse_float_env("POLL_INTERVAL_SEC", 5.0)
POLL_TIMEOUT_SEC = parse_float_env("POLL_TIMEOUT_SEC", 900.0)


def _ensure_host(host: str) -> str:
    parsed = urlparse((host or "").strip())
    if not parsed.scheme or not parsed.hostname:
        raise PreflightError(f"Invalid URL in environment: {host!r}")
    if parsed.scheme != "https" and not (ALLOW_INSECURE_HTTP and parsed.scheme == "http"):
        raise PreflightError(
            "Only HTTPS endpoints are allowed. "
            "Set ALLOW_INSECURE_HTTP=true only for controlled non-production environments."
        )
    if parsed.query or parsed.fragment:
        raise PreflightError(f"URL must not include query or fragment: {host!r}")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _bearer(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _is_duplicate_error(msg: str) -> bool:
    text = (msg or "").lower()
    return any(
        item in text
        for item in [
            "already exists",
            "duplicate",
            "unique constraint",
            "409",
            "name exists",
            "constraint was violated",
            "cannot have the same name as existing extract group",
        ]
    )


def lazy_import_oracledb() -> Any:
    spec = importlib.util.find_spec("oracledb")
    if spec is None:
        raise RuntimeError(
            "Install oracledb first: python -m pip install -r ai_skills/boss_extract_automation/requirements.txt"
        )
    try:
        import oracledb  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Install oracledb first: python -m pip install -r ai_skills/boss_extract_automation/requirements.txt"
        ) from exc
    return oracledb


def check_dependency(name: str) -> Optional[str]:
    if importlib.util.find_spec(name) is None:
        return name
    return None


def check_output_dir(path_str: str) -> Optional[str]:
    path = Path(path_str)
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return f"Output directory not writable: {path} ({exc})"
    return None


def check_wallet_path(path_str: Optional[str]) -> Optional[str]:
    if not path_str:
        return "DB_WALLET_LOCATION is not set"
    path = Path(path_str)
    if not path.exists():
        return f"Wallet path does not exist: {path}"
    if not path.is_dir():
        return f"Wallet path is not a directory: {path}"
    return None


def _host_port(url: str) -> Tuple[str, int]:
    normalized = _ensure_host(url)
    parsed = urlparse(normalized)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.hostname, port


def _safe_output_filename(name: str) -> str:
    candidate = (name or "").strip().replace("\\", "/")
    if not candidate:
        raise ValueError("Output file name is empty")
    if candidate.startswith("/") or candidate.startswith("../") or "/../" in candidate:
        raise ValueError(f"Unsafe output file name from API: {name!r}")
    pure_name = Path(candidate).name
    if pure_name in {"", ".", ".."}:
        raise ValueError(f"Unsafe output file name from API: {name!r}")
    return pure_name


def check_reachability(url: str, timeout: float = 3.0) -> Optional[str]:
    host, port = _host_port(url)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return None
    except OSError as exc:
        return f"Cannot reach {host}:{port} ({exc})"


def run_preflight(args: argparse.Namespace) -> Summary:
    summary = Summary(command="preflight")
    required_keys = list(REQUIRED_ENV["network_only"]) + [
        "IDCS_CLIENT_ID",
        "IDCS_CLIENT_SECRET",
        "BOSS_USERNAME",
        "BOSS_PASSWORD",
        "IDCS_BOSS_SCOPE",
        "IDCS_BATCH_SCOPE",
        "DEFAULT_OWNER",
        "DEFAULT_EMAILS",
    ]
    if args.require_db:
        required_keys.extend(REQUIRED_ENV["db"])
    missing = getenv_required(required_keys)
    if missing:
        summary.missing_env.extend(missing)

    for dep in ("requests",):
        missing_dep = check_dependency(dep)
        if missing_dep:
            summary.missing_dependencies.append(missing_dep)
    if args.require_db:
        missing_dep = check_dependency("oracledb")
        if missing_dep:
            summary.missing_dependencies.append(missing_dep)

    wallet_issue = check_wallet_path(ENV.get("DB_WALLET_LOCATION")) if args.require_db else None
    if wallet_issue:
        summary.unsupported_environment.append(wallet_issue)

    output_issue = check_output_dir(ENV["OUTPUT_DIR"])
    if output_issue:
        summary.unsupported_environment.append(output_issue)

    if args.check_network:
        for key in REQUIRED_ENV["network_only"]:
            value = ENV.get(key)
            if value:
                issue = check_reachability(value)
                if issue:
                    summary.unsupported_environment.append(issue)

    if summary.missing_env or summary.missing_dependencies or summary.unsupported_environment:
        summary.status = "failed"
        summary.failed_step = "preflight"
        if summary.missing_dependencies:
            summary.warnings.append(
                "Install dependencies with: python -m pip install -r ai_skills/boss_extract_automation/requirements.txt"
            )
        if summary.missing_env:
            summary.warnings.append(
                "Populate the missing environment variables from ai_skills/boss_extract_automation/assets/.env.example"
            )
        return summary

    summary.details = {
        "output_dir": str(Path(ENV["OUTPUT_DIR"]).resolve()),
        "wallet_path": ENV.get("DB_WALLET_LOCATION"),
        "network_checks": bool(args.check_network),
    }
    return summary


def to_business_object(business_view_name: str) -> str:
    name = re.sub(r"extract$", "", business_view_name, flags=re.IGNORECASE)
    return name[:1].upper() + name[1:] if name else name


def make_alias(attr: str) -> str:
    return attr.replace(".", "")


def fetch_module_and_attributes(pool: Any, business_view_name: str) -> Tuple[str, List[str]]:
    sql = """
        select MODULENAME,
               BUSINESS_VIEW_ATTRIBUTE
          from V_BUSINESS_OBJECTS
         where BUSINESS_VIEW_NAME = :bvn
           and BUSINESS_VIEW_ATTRIBUTE is not null
           and BUSINESS_VIEW_ATTRIBUTE != 'Not in business view'
         order by BUSINESS_VIEW_ATTRIBUTE
    """
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, bvn=business_view_name)
            rows = cursor.fetchall()
    if not rows:
        raise ValueError(f"No attributes found for BUSINESS_VIEW_NAME={business_view_name!r}")
    return rows[0][0], [row[1] for row in rows]


def load_metadata_from_fixture(path: str, business_view_name: str) -> Tuple[str, List[str]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    fixture = data.get("views", {}).get(business_view_name)
    if not fixture:
        raise ValueError(f"View {business_view_name!r} not found in fixture {path}")
    module_name = fixture.get("module")
    attributes = fixture.get("attributes") or []
    if not module_name or not attributes:
        raise ValueError(f"Fixture for {business_view_name!r} is missing module or attributes")
    return module_name, attributes


def load_mapping_config() -> Dict[str, Any]:
    mapping_path = Path(__file__).resolve().parent.parent / "assets" / "mapping.json"
    return json.loads(mapping_path.read_text(encoding="utf-8"))


def _default_catalog_csv_path() -> str:
    configured = ENV.get("CATALOG_CSV_PATH")
    if configured:
        return configured
    return str(Path(__file__).resolve().parents[3] / "pythonProject" / "catalog_output.csv")


def _catalog_business_view_name(path_value: str) -> str:
    return (path_value or "").rstrip("/").split("/")[-1]


def load_catalog_module_lookup(path: str) -> Dict[str, str]:
    catalog_path = Path(path)
    if not catalog_path.exists():
        raise ValueError(f"Catalog CSV not found: {catalog_path}")

    lookup: Dict[str, str] = {}
    with catalog_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            metadata_type = (row.get("Metadata Type") or row.get("metadataType") or "").strip()
            if metadata_type and metadata_type != "BusinessView":
                continue
            business_view_name = _catalog_business_view_name(row.get("Path") or row.get("path") or "")
            module_name = (row.get("Module Name") or row.get("moduleName") or "").strip()
            if business_view_name and module_name:
                lookup[business_view_name] = module_name
    if not lookup:
        raise ValueError(f"No BusinessView rows with module names found in catalog CSV: {catalog_path}")
    return lookup


def load_metadata_from_mapping(business_view_name: str, catalog_csv_path: Optional[str] = None) -> Tuple[str, List[str]]:
    data = load_mapping_config()
    mappings = data.get("mappings") or []
    mapping_entry = next((item for item in mappings if item.get("business_view_name") == business_view_name), None)
    if not mapping_entry:
        raise ValueError(f"View {business_view_name!r} not found in assets/mapping.json")

    attributes: List[str] = []
    seen = set()
    for column in mapping_entry.get("columns") or []:
        attr = (column.get("business_view_column") or "").strip()
        if not attr or attr == "Not in business view" or attr in seen:
            continue
        seen.add(attr)
        attributes.append(attr)
    if not attributes:
        raise ValueError(f"No usable business_view_column values found for {business_view_name!r} in assets/mapping.json")

    catalog_lookup = load_catalog_module_lookup(catalog_csv_path or _default_catalog_csv_path())
    module_name = catalog_lookup.get(business_view_name)
    if not module_name:
        raise ValueError(
            f"Module name for view {business_view_name!r} not found in catalog CSV {catalog_csv_path or _default_catalog_csv_path()}"
        )
    return module_name, attributes


def load_extract_config() -> Dict[str, Any]:
    config_path = Path(__file__).resolve().parent.parent / "assets" / "extract_config.json"
    if not config_path.exists():
        raise ValueError(f"Missing configuration file: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_default_mapping_entry() -> Dict[str, Any]:
    data = load_mapping_config()
    mappings = data.get("mappings") or []
    default_pvo = ENV.get("DEFAULT_PVO")
    if default_pvo:
        for item in mappings:
            if item.get("pvo") == default_pvo:
                return item
        raise ValueError(f"DEFAULT_PVO {default_pvo!r} was not found in assets/mapping.json")
    if not mappings:
        raise ValueError("No mappings found in assets/mapping.json")
    return mappings[0]


def build_args_namespace(command: str) -> argparse.Namespace:
    extract_config = load_extract_config()
    mapping_entry = get_default_mapping_entry()
    business_view_name = mapping_entry.get("business_view_name")
    if not business_view_name:
        raise ValueError("Default mapping entry is missing business_view_name")

    frequency = extract_config.get("frequency", "Immediate")
    if frequency not in FREQUENCY_CHOICES:
        raise ValueError(f"DEFAULT_FREQUENCY must be one of {FREQUENCY_CHOICES}, got {frequency!r}")

    extract_type = extract_config.get("extract_type", "Full")
    if extract_type not in EXTRACT_TYPE_CHOICES:
        raise ValueError(f"DEFAULT_EXTRACT_TYPE must be one of {EXTRACT_TYPE_CHOICES}, got {extract_type!r}")

    output_data_format = extract_config.get("output_data_format")
    if output_data_format is not None and output_data_format not in OUTPUT_DATA_FORMAT_CHOICES:
        raise ValueError(
            f"DEFAULT_OUTPUT_DATA_FORMAT must be one of {OUTPUT_DATA_FORMAT_CHOICES}, got {output_data_format!r}"
        )

    metadata_fixture = extract_config.get("metadata_fixture") or None
    metadata_source = extract_config.get("metadata_source", "auto")
    if metadata_source not in METADATA_SOURCE_CHOICES:
        raise ValueError(f"metadata_source must be one of {METADATA_SOURCE_CHOICES}, got {metadata_source!r}")
    catalog_csv_path = extract_config.get("catalog_csv_path") or ENV.get("CATALOG_CSV_PATH") or _default_catalog_csv_path()

    return argparse.Namespace(
        command=command,
        business_view_name=business_view_name,
        extract_name=extract_config.get("extract_name"),
        group_name=extract_config.get("group_name"),
        schedule_name=extract_config.get("schedule_name"),
        owner=ENV["DEFAULT_OWNER"],
        owner_role=ENV["DEFAULT_OWNER_ROLE"],
        emails=ENV["DEFAULT_EMAILS"],
        notification=extract_config.get("notification", ENV["DEFAULT_NOTIFICATION"]),
        frequency=frequency,
        extract_type=extract_type,
        frequency_hourly_interval=extract_config.get("frequency_hourly_interval"),
        frequency_day_in_month=extract_config.get("frequency_day_in_month"),
        frequency_month=extract_config.get("frequency_month"),
        frequency_days_in_week=extract_config.get("frequency_days_in_week"),
        start_time=extract_config.get("start_time"),
        end_time=extract_config.get("end_time"),
        description=extract_config.get("description", "Data Extract Definition (automated)"),
        output_data_format=output_data_format,
        csv_delimiter=extract_config.get("csv_delimiter"),
        sort_by=extract_config.get("sort_by"),
        csv_format=extract_config.get("csv_format"),
        history_start_date=extract_config.get("history_start_date"),
        filter_condition=extract_config.get("filter_condition"),
        poll=bool(extract_config.get("poll", True)),
        debug=bool(extract_config.get("debug", False)),
        dry_run=bool(extract_config.get("dry_run", False)),
        preflight=False,
        check_network=bool(extract_config.get("check_network", False)),
        metadata_source=metadata_source,
        metadata_fixture=metadata_fixture,
        catalog_csv_path=catalog_csv_path,
        schedule_id=extract_config.get("schedule_id"),
        job_request_id=extract_config.get("job_request_id"),
        require_db=bool(extract_config.get("require_db", False)),
        pvo=mapping_entry.get("pvo"),
        mapping_entry=mapping_entry,
        extract_config=extract_config,
    )


def build_payload(business_view_name: str, module_name: str, attributes: List[str]) -> Dict[str, Any]:
    business_object = to_business_object(business_view_name)
    field_aliases = {attr: make_alias(attr) for attr in attributes}
    select_cols = ", ".join(field_aliases.values())
    extraction_query_obj = {
        "viewQueries": {
            business_view_name: {
                "module": module_name,
                "businessObject": business_object,
                "view": business_view_name,
                "fieldAliases": field_aliases,
            }
        },
        "select": (
            f"select {select_cols} from {business_view_name} "
            "where timeUpdated between to_timestamp(:minSrcLastUpdateDate ,'YYYY-MM-DD HH24:MI:SS.FF9') "
            "and to_timestamp(:maxSrcLastUpdateDate,'YYYY-MM-DD HH24:MI:SS.FF9') "
            "and timeCreated >= to_timestamp(:minCreationDate,'YYYY-MM-DD HH24:MI:SS.FF9') "
        ),
    }
    return {"bossArtifacts": {"extractionQuery": json.dumps(extraction_query_obj, separators=(",", ":"))}}


def derive_names(view: str, extract_name: Optional[str] = None, group_name: Optional[str] = None, schedule_name: Optional[str] = None) -> Tuple[str, str, str]:
    base = view[:-7] if view.lower().endswith("extract") else view
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    cap = base[:1].upper() + base[1:] if base else base
    return (
        extract_name or f"{cap}Extract",
        group_name or f"{cap}ExtractGroup_{ts}",
        schedule_name or f"{cap}Schedule-{ts}",
    )


def build_export_definition_body(
    name: str,
    description: str,
    owner: str,
    owner_role: str,
    export_cfg: Optional[Dict[str, Any]],
    extraction_query_json: str,
    filter_condition: Optional[str] = None,
) -> Dict[str, Any]:
    export_configuration = {
        "type": "BV",
        "outputDataFormat": "CSV",
        "csvDelimiter": ",",
        "sortBy": None,
        "csvFormat": None,
        "historyStartDate": None,
    }
    if export_cfg:
        export_configuration.update(export_cfg)
    body = {
        "name": name,
        "description": description,
        "owner": owner,
        "ownerRole": owner_role,
        "exportConfiguration": export_configuration,
        "bossArtifacts": {"extractionQuery": extraction_query_json},
    }
    if filter_condition:
        body["filterCondition"] = filter_condition
    return body


def _parse_location_id(resp: requests.Response) -> str:
    location = resp.headers.get("Location") or resp.headers.get("location")
    if not location:
        raise HttpError("Missing Location header in response")
    return location.rstrip("/").split("/")[-1]


_TOKENS: Dict[str, str] = {}


def get_token(scope: str) -> str:
    if scope in _TOKENS:
        return _TOKENS[scope]
    missing = getenv_required(["IDCS_CLIENT_ID", "IDCS_CLIENT_SECRET", "BOSS_USERNAME", "BOSS_PASSWORD", "IDCS_HOST"])
    if missing:
        raise RuntimeError(f"Missing required environment variables for token retrieval: {', '.join(missing)}")
    url = _ensure_host(ENV["IDCS_HOST"] or "") + "/oauth2/v1/token"
    response = requests.post(
        url,
        data={
            "grant_type": "password",
            "username": ENV["BOSS_USERNAME"],
            "password": ENV["BOSS_PASSWORD"],
            "scope": scope,
        },
        auth=requests.auth.HTTPBasicAuth(ENV["IDCS_CLIENT_ID"], ENV["IDCS_CLIENT_SECRET"]),
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        timeout=30,
    )
    if response.status_code != 200:
        raise HttpError(f"IDCS token error {response.status_code}: {response.text}")
    token = response.json().get("access_token")
    if not token:
        raise HttpError("IDCS token response missing access_token")
    _TOKENS[scope] = token
    return token


def create_export_definition(token: str, body: Dict[str, Any]) -> Tuple[str, str]:
    url = _ensure_host(ENV["BOSS_HOST"] or "") + "/api/boss/data/objects/ora/commonBoss/dataExport/v1/exportDefinitions"
    resp = requests.post(url, headers={"Content-Type": "application/json", "Accept": "application/json", **_bearer(token)}, data=json.dumps(body), timeout=60)
    if resp.status_code not in (200, 201):
        raise HttpError(f"Create exportDefinition failed {resp.status_code}: {resp.text}")
    return _parse_location_id(resp), body.get("name", "")


def create_export_definition_with_retry(token: str, body: Dict[str, Any]) -> Tuple[str, str]:
    try:
        return create_export_definition(token, body)
    except HttpError as exc:
        if not _is_duplicate_error(str(exc)):
            raise
        updated = dict(body)
        updated["name"] = f"{body.get('name', 'ExportDef')}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        return create_export_definition(token, updated)


def create_export_group(token: str, group_name: str, owner: str, owner_role: str, extract_names: List[str]) -> Tuple[str, str]:
    url = _ensure_host(ENV["BOSS_HOST"] or "") + "/api/boss/data/objects/ora/commonBoss/dataExport/v1/exportGroupDefinitions"
    payload = {
        "name": group_name,
        "owner": owner,
        "ownerRole": owner_role,
        "groupedExtracts": {"items": [{"name": name} for name in extract_names]},
    }
    resp = requests.post(url, headers={"Content-Type": "application/json", "Accept": "application/json", **_bearer(token)}, data=json.dumps(payload), timeout=60)
    if resp.status_code not in (200, 201):
        raise HttpError(f"Create exportGroup failed {resp.status_code}: {resp.text}")
    return _parse_location_id(resp), group_name


def create_export_group_with_retry(token: str, group_name: str, owner: str, owner_role: str, extract_names: List[str]) -> Tuple[str, str]:
    try:
        return create_export_group(token, group_name, owner, owner_role, extract_names)
    except HttpError as exc:
        if not _is_duplicate_error(str(exc)):
            raise
        retry_name = f"{group_name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        return create_export_group(token, retry_name, owner, owner_role, extract_names)


def schedule_extract_group(
    token: str,
    export_group_id: str,
    schedule_name: str,
    group_name: str,
    extract_type: str,
    notification: str,
    emails: str,
    frequency: str,
    frequency_hourly_interval: Optional[str],
    frequency_day_in_month: Optional[str],
    frequency_month: Optional[str],
    frequency_days_in_week: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
) -> str:
    url = _ensure_host(ENV["BOSS_HOST"] or "") + "/api/boss/data/objects/ora/scmCore/dataExtract/v1/$en/extractSchedules"
    payload: Dict[str, Any] = {
        "extractDefinition": {"exportGroupId": str(export_group_id)},
        "name": schedule_name,
        "extractType": extract_type,
        "notification": notification,
        "emails": emails,
        "frequency": frequency,
        "extractDefinitionName": group_name,
    }
    optional_fields = {
        "frequencyHourlyInterval": frequency_hourly_interval,
        "frequencyDayInMonth": frequency_day_in_month,
        "frequencyMonth": frequency_month,
        "frequencyDaysInWeek": frequency_days_in_week,
        "startTime": start_time,
        "endTime": end_time,
    }
    payload.update({key: value for key, value in optional_fields.items() if value is not None})
    resp = requests.post(url, headers={"Content-Type": "application/json", "Accept": "application/json", **_bearer(token)}, data=json.dumps(payload), timeout=60)
    if resp.status_code not in (200, 201):
        raise HttpError(f"Schedule extract failed {resp.status_code}: {resp.text}")
    return _parse_location_id(resp)


def schedule_extract_group_with_retry(
    token: str,
    export_group_id: str,
    schedule_name: str,
    group_name: str,
    extract_type: str,
    notification: str,
    emails: str,
    frequency: str,
    frequency_hourly_interval: Optional[str],
    frequency_day_in_month: Optional[str],
    frequency_month: Optional[str],
    frequency_days_in_week: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
) -> Tuple[str, str]:
    try:
        schedule_resource_id = schedule_extract_group(
            token,
            export_group_id,
            schedule_name,
            group_name,
            extract_type,
            notification,
            emails,
            frequency,
            frequency_hourly_interval,
            frequency_day_in_month,
            frequency_month,
            frequency_days_in_week,
            start_time,
            end_time,
        )
        return schedule_resource_id, schedule_name
    except HttpError as exc:
        if not _is_duplicate_error(str(exc)):
            raise
        retry_name = f"{schedule_name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        schedule_resource_id = schedule_extract_group(
            token,
            export_group_id,
            retry_name,
            group_name,
            extract_type,
            notification,
            emails,
            frequency,
            frequency_hourly_interval,
            frequency_day_in_month,
            frequency_month,
            frequency_days_in_week,
            start_time,
            end_time,
        )
        return schedule_resource_id, retry_name


def get_schedule(token: str, schedule_resource_id: str) -> Dict[str, Any]:
    url = _ensure_host(ENV["BOSS_HOST"] or "") + f"/api/boss/data/objects/ora/scmCore/dataExtract/v1/$en/extractSchedules/{schedule_resource_id}"
    resp = requests.get(url, headers=_bearer(token), timeout=60)
    if resp.status_code != 200:
        raise HttpError(f"Get schedule failed {resp.status_code}: {resp.text}")
    return resp.json()


def get_ess_job_status(schedule_id: str, max_wait: float = POLL_TIMEOUT_SEC, interval: float = POLL_INTERVAL_SEC) -> Dict[str, Any]:
    if not ENV["ESS_USERNAME"] or not ENV["ESS_PASSWORD"]:
        raise RuntimeError("ESS_USERNAME and ESS_PASSWORD must be set for ESS status checks")
    url = _ensure_host(ENV["BOSS_HOST"] or "") + f"/ess/rest/scheduler/v1/requests/{schedule_id}"
    auth = requests.auth.HTTPBasicAuth(ENV["ESS_USERNAME"], ENV["ESS_PASSWORD"])
    start = time.time()
    latest: Dict[str, Any] = {}
    while True:
        resp = requests.get(url, auth=auth, timeout=60)
        if resp.status_code != 200:
            raise HttpError(f"ESS status failed {resp.status_code}: {resp.text}")
        latest = resp.json()
        state = str(latest.get("state"))
        print(f"[ESS] schedule {schedule_id} state: {state}")
        if state in TERMINAL_ESS_STATES:
            return latest
        if time.time() - start > max_wait:
            return latest
        time.sleep(interval)


def find_batch_job_request(batch_token: str, schedule_id: str, max_wait: float = POLL_TIMEOUT_SEC, interval: float = POLL_INTERVAL_SEC) -> Dict[str, Any]:
    url = _ensure_host(ENV["BOSS_HOST"] or "") + "/api/saas-batch/jobscheduler/v1/jobRequests/"
    headers = {"Content-Type": "application/json", "Accept": "application/json", **_bearer(batch_token)}
    start = time.time()
    while True:
        resp = requests.get(url, headers=headers, timeout=60)
        if resp.status_code != 200:
            raise HttpError(f"Batch jobRequests failed {resp.status_code}: {resp.text}")
        items = (resp.json() or {}).get("items") or []
        for item in items:
            params = ((item.get("jobRequest") or {}).get("requestParameters") or {})
            parent = str(params.get("parentRequest")) if params.get("parentRequest") is not None else None
            ctx = str(params.get("requestExecutionContext") or "")
            client_request_uuid = str((item.get("jobRequest") or {}).get("clientRequestUuid") or "")
            if (
                parent == str(schedule_id)
                or client_request_uuid == str(schedule_id)
                or client_request_uuid.startswith(f"{schedule_id},")
                or ctx.startswith(f"{schedule_id},")
            ):
                return item
        if time.time() - start > max_wait:
            raise TimeoutError(f"Timed out waiting for batch job request linked to scheduleId {schedule_id}")
        time.sleep(interval)


def get_batch_job_request(batch_token: str, job_request_id: str) -> Dict[str, Any]:
    url = _ensure_host(ENV["BOSS_HOST"] or "") + f"/api/saas-batch/jobscheduler/v1/jobRequests/{job_request_id}"
    resp = requests.get(url, headers={"Content-Type": "application/json", "Accept": "application/json", **_bearer(batch_token)}, timeout=60)
    if resp.status_code != 200:
        raise HttpError(f"Get jobRequest failed {resp.status_code}: {resp.text}")
    return resp.json() or {}


def _batch_status(job: Dict[str, Any]) -> Tuple[Optional[str], str]:
    if job.get("jobStatus") is not None:
        return str(job.get("jobStatus")), "top.jobStatus"
    details = job.get("jobDetails") or {}
    if details.get("jobStatus") is not None:
        return str(details.get("jobStatus")), "jobDetails.jobStatus"
    progress = job.get("jobProgress") or {}
    if progress.get("status") is not None:
        return str(progress.get("status")), "jobProgress.status"
    return None, "<missing>"


def poll_batch_job_status(batch_token: str, job_request_id: str, max_wait: float = POLL_TIMEOUT_SEC, interval: float = POLL_INTERVAL_SEC) -> Dict[str, Any]:
    start = time.time()
    latest: Dict[str, Any] = {}
    while True:
        latest = get_batch_job_request(batch_token, job_request_id)
        status, _ = _batch_status(latest)
        print(f"[Batch] jobRequestId={job_request_id} status={status}")
        if status in TERMINAL_BATCH_STATES:
            return latest
        if time.time() - start > max_wait:
            return latest
        time.sleep(interval)


def list_output_files(batch_token: str, job_request_id: str) -> List[Dict[str, Any]]:
    url = _ensure_host(ENV["BOSS_HOST"] or "") + f"/api/saas-batch/jobfilemanager/v1/jobRequests/{job_request_id}/outputFiles"
    resp = requests.get(url, headers={"Content-Type": "application/json", "Accept": "application/json", **_bearer(batch_token)}, timeout=60)
    if resp.status_code != 200:
        raise HttpError(f"List output files failed {resp.status_code}: {resp.text}")
    return (resp.json() or {}).get("items") or []


def download_output_file(batch_token: str, job_request_id: str, file_name: str, dest_dir: str) -> str:
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    safe_name = _safe_output_filename(file_name)
    url = _ensure_host(ENV["BOSS_HOST"] or "") + f"/api/saas-batch/jobfilemanager/v1/jobRequests/{job_request_id}/outputFiles/{safe_name}/content"
    with requests.get(url, headers=_bearer(batch_token), stream=True, timeout=60) as response:
        if response.status_code != 200:
            raise HttpError(f"Download failed {response.status_code}: {response.text}")
        destination = Path(dest_dir) / safe_name
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)
    return str(destination)


def build_export_cfg(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    export_cfg: Dict[str, Any] = {}
    mapping = {
        "outputDataFormat": args.output_data_format,
        "csvDelimiter": args.csv_delimiter,
        "sortBy": args.sort_by,
        "csvFormat": args.csv_format,
        "historyStartDate": args.history_start_date,
    }
    export_cfg.update({key: value for key, value in mapping.items() if value is not None})
    return export_cfg or None


def build_stage_plan(args: argparse.Namespace, extraction_query_json: Optional[str] = None) -> Summary:
    summary = Summary(command=args.command)
    extract_name, group_name, schedule_name = derive_names(args.business_view_name, args.extract_name, args.group_name, args.schedule_name)
    summary.names = {"extract": extract_name, "group": group_name, "schedule": schedule_name}
    base = _ensure_host(ENV["BOSS_HOST"] or "<missing-boss-host>")
    summary.planned_api_calls = [
        {"step": "create-extract", "method": "POST", "url": f"{base}/api/boss/data/objects/ora/commonBoss/dataExport/v1/exportDefinitions"},
        {"step": "create-group", "method": "POST", "url": f"{base}/api/boss/data/objects/ora/commonBoss/dataExport/v1/exportGroupDefinitions"},
        {"step": "schedule", "method": "POST", "url": f"{base}/api/boss/data/objects/ora/scmCore/dataExtract/v1/$en/extractSchedules"},
        {"step": "monitor-ess", "method": "GET", "url": f"{base}/ess/rest/scheduler/v1/requests/<scheduleId>"},
        {"step": "monitor-batch", "method": "GET", "url": f"{base}/api/saas-batch/jobscheduler/v1/jobRequests/"},
        {"step": "download", "method": "GET", "url": f"{base}/api/saas-batch/jobfilemanager/v1/jobRequests/<jobRequestId>/outputFiles"},
    ]
    if extraction_query_json:
        summary.details["extraction_query_preview"] = json.loads(extraction_query_json)
    return summary


def get_metadata(args: argparse.Namespace) -> Tuple[str, List[str]]:
    metadata_source = getattr(args, "metadata_source", "auto")
    if metadata_source == "fixture":
        if not args.metadata_fixture:
            raise ValueError("metadata_source='fixture' requires metadata_fixture")
        return load_metadata_from_fixture(args.metadata_fixture, args.business_view_name)
    if metadata_source == "mapping":
        return load_metadata_from_mapping(args.business_view_name, args.catalog_csv_path)
    if metadata_source == "auto" and args.metadata_fixture:
        return load_metadata_from_fixture(args.metadata_fixture, args.business_view_name)

    if metadata_source == "auto":
        try:
            return load_metadata_from_mapping(args.business_view_name, args.catalog_csv_path)
        except Exception:
            pass

    oracledb = lazy_import_oracledb()
    pool = oracledb.create_pool(
        user=ENV["DB_USER"],
        password=ENV["DB_PASSWORD"],
        dsn=ENV["DB_CONNECT_STRING"],
        wallet_location=ENV["DB_WALLET_LOCATION"],
        wallet_password=ENV["DB_WALLET_PASSWORD"],
    )
    try:
        return fetch_module_and_attributes(pool, args.business_view_name)
    finally:
        pool.close()


def cmd_validate_view(args: argparse.Namespace) -> Summary:
    summary = Summary(command="validate-view")
    module_name, attrs = get_metadata(args)
    payload = build_payload(args.business_view_name, module_name, attrs)
    summary.details = {
        "business_view_name": args.business_view_name,
        "module_name": module_name,
        "attribute_count": len(attrs),
        "sample_attributes": attrs[:10],
        "payload_preview": json.loads(payload["bossArtifacts"]["extractionQuery"]),
    }
    return summary


def cmd_create_extract(args: argparse.Namespace) -> Summary:
    module_name, attrs = get_metadata(args)
    extraction_query_json = build_payload(args.business_view_name, module_name, attrs)["bossArtifacts"]["extractionQuery"]
    summary = build_stage_plan(args, extraction_query_json)
    if args.dry_run:
        summary.status = "dry-run"
        return summary
    body = build_export_definition_body(
        summary.names["extract"],
        args.description,
        args.owner,
        args.owner_role,
        build_export_cfg(args),
        extraction_query_json,
        args.filter_condition,
    )
    token = get_token(ENV["IDCS_BOSS_SCOPE"] or "")
    export_id, export_name = create_export_definition_with_retry(token, body)
    summary.created_ids["export_definition_id"] = export_id
    summary.names["extract"] = export_name
    return summary


def cmd_monitor(args: argparse.Namespace) -> Summary:
    summary = Summary(command="monitor")
    summary.created_ids["schedule_id"] = args.schedule_id
    summary.created_ids["job_request_id"] = args.job_request_id
    if args.dry_run:
        summary.status = "dry-run"
        return summary
    if args.schedule_id:
        token = get_token(ENV["IDCS_BOSS_SCOPE"] or "")
        ess = get_ess_job_status(args.schedule_id)
        summary.details["ess"] = ess
        if ess.get("state") not in {"SUCCEEDED", "WARNING"}:
            summary.fail("monitor", f"ESS job ended in state {ess.get('state')}", status="failed")
    if args.job_request_id:
        batch_token = get_token(ENV["IDCS_BATCH_SCOPE"] or "")
        job = poll_batch_job_status(batch_token, args.job_request_id)
        summary.details["batch"] = job
    return summary


def cmd_download(args: argparse.Namespace) -> Summary:
    summary = Summary(command="download")
    summary.created_ids["job_request_id"] = args.job_request_id
    if args.dry_run:
        summary.status = "dry-run"
        return summary
    batch_token = get_token(ENV["IDCS_BATCH_SCOPE"] or "")
    files = list_output_files(batch_token, args.job_request_id)
    if not files:
        summary.fail("download", f"No output files found for jobRequestId={args.job_request_id}", status="failed")
        return summary
    for item in files:
        name = item.get("fileName")
        if name:
            summary.downloaded_files.append(download_output_file(batch_token, args.job_request_id, name, ENV["OUTPUT_DIR"]))
    return summary


def cmd_full_run(args: argparse.Namespace) -> Summary:
    if not args.dry_run:
        require_db = bool(args.require_db or args.metadata_source == "db")
        preflight = run_preflight(argparse.Namespace(require_db=require_db, check_network=args.check_network))
        if preflight.status != "ok":
            return preflight

    module_name, attrs = get_metadata(args)
    extraction_query_json = build_payload(args.business_view_name, module_name, attrs)["bossArtifacts"]["extractionQuery"]
    summary = build_stage_plan(args, extraction_query_json)
    summary.details["module_name"] = module_name
    summary.details["attribute_count"] = len(attrs)
    if args.dry_run:
        summary.status = "dry-run"
        return summary

    boss_token = get_token(ENV["IDCS_BOSS_SCOPE"] or "")
    export_body = build_export_definition_body(
        summary.names["extract"],
        args.description,
        args.owner,
        args.owner_role,
        build_export_cfg(args),
        extraction_query_json,
        args.filter_condition,
    )
    export_id, export_name = create_export_definition_with_retry(boss_token, export_body)
    summary.created_ids["export_definition_id"] = export_id
    summary.names["extract"] = export_name

    group_id, group_name = create_export_group_with_retry(boss_token, summary.names["group"], args.owner, args.owner_role, [export_name])
    summary.created_ids["export_group_id"] = group_id
    summary.names["group"] = group_name

    schedule_res_id, schedule_name = schedule_extract_group_with_retry(
        boss_token,
        group_id,
        summary.names["schedule"],
        group_name,
        args.extract_type,
        args.notification,
        args.emails,
        args.frequency,
        args.frequency_hourly_interval,
        args.frequency_day_in_month,
        args.frequency_month,
        args.frequency_days_in_week,
        args.start_time,
        args.end_time,
    )
    summary.created_ids["schedule_resource_id"] = schedule_res_id
    summary.names["schedule"] = schedule_name

    schedule = get_schedule(boss_token, schedule_res_id)
    schedule_id = str(schedule.get("scheduleId")) if schedule else None
    summary.created_ids["schedule_id"] = schedule_id
    summary.details["schedule"] = schedule

    if args.poll and schedule_id:
        ess_status = get_ess_job_status(schedule_id)
        summary.details["ess"] = ess_status
        if ess_status.get("state") not in {"SUCCEEDED", "WARNING"}:
            summary.fail("monitor", f"ESS job ended in state {ess_status.get('state')}", status="failed")
            return summary

    batch_token = get_token(ENV["IDCS_BATCH_SCOPE"] or "")
    job = find_batch_job_request(batch_token, schedule_id or "")
    job_request_id = str(job.get("jobRequestId"))
    summary.created_ids["job_request_id"] = job_request_id
    status, _ = _batch_status(job)
    if status not in {"SUCCEEDED", "COMPLETED"}:
        if args.poll:
            job = poll_batch_job_status(batch_token, job_request_id)
            status, _ = _batch_status(job)
        else:
            summary.fail("monitor", f"Batch job not complete (status={status}) and polling disabled", status="failed")
            return summary
    summary.details["batch"] = job
    if status not in {"SUCCEEDED", "COMPLETED"}:
        summary.fail("monitor", f"Batch job did not succeed (status={status})", status="failed")
        return summary

    files = list_output_files(batch_token, job_request_id)
    if not files:
        summary.fail("download", f"No output files found for jobRequestId={job_request_id}", status="failed")
        return summary
    for item in files:
        name = item.get("fileName")
        if name:
            summary.downloaded_files.append(download_output_file(batch_token, job_request_id, name, ENV["OUTPUT_DIR"]))
    return summary


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automate BOSS extract creation, validation, monitoring, and download")
    parser.add_argument("command", nargs="?", default="run", choices=COMMAND_CHOICES, help="Stage to execute")
    parsed = parser.parse_args(argv)
    return build_args_namespace(parsed.command)


def normalize_command(args: argparse.Namespace) -> str:
    if args.preflight:
        return "preflight"
    return args.command


def ensure_command_args(args: argparse.Namespace) -> None:
    if normalize_command(args) == "monitor" and not (args.schedule_id or args.job_request_id):
        raise ValueError("monitor requires --schedule-id or --job-request-id")
    if normalize_command(args) == "download" and not args.job_request_id:
        raise ValueError("download requires --job-request-id")


def main(argv: Optional[List[str]] = None) -> None:
    global DEBUG
    args = parse_args(argv)
    args.command = normalize_command(args)
    DEBUG = bool(args.debug)

    try:
        ensure_command_args(args)
        if args.command == "preflight":
            require_db = bool(args.require_db or args.metadata_source == "db")
            summary = run_preflight(argparse.Namespace(require_db=require_db, check_network=args.check_network))
        elif args.command == "validate-view":
            summary = cmd_validate_view(args)
        elif args.command == "create-extract":
            summary = cmd_create_extract(args)
        elif args.command == "monitor":
            summary = cmd_monitor(args)
        elif args.command == "download":
            summary = cmd_download(args)
        else:
            summary = cmd_full_run(args)
        emit_summary(summary, 0 if summary.status in {"ok", "dry-run"} else 1)
    except Exception as exc:
        summary = Summary(status="failed", command=args.command, failed_step=args.command)
        message = str(exc)
        if isinstance(exc, RuntimeError) and "Install oracledb first:" in message:
            summary.missing_dependencies.append("oracledb")
        summary.warnings.append(message)
        if DEBUG:
            summary.details["traceback"] = traceback.format_exc()
        emit_summary(summary, 1)


if __name__ == "__main__":
    main()
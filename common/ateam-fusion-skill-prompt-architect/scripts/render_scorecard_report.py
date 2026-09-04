#!/usr/bin/env python3
"""
Render a browser-friendly HTML report for prompt benchmark scorecards.

Example:
  python3 render_scorecard_report.py \
    --scorecard ../assets/synthetic-benchmark/synthetic_scorecard.json \
    --eval-params ../assets/synthetic-benchmark/synthetic_eval_params.json \
    --manifest ../assets/synthetic-benchmark/synthetic_prompt_manifest.json \
    --output-html ../assets/synthetic-benchmark/synthetic_scorecard_report.html
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _rate(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _metric_gate_status(value: float | None, operator: str, threshold: float) -> str:
    if value is None:
        return "not_evaluable"
    if operator == ">=":
        return "pass" if value >= threshold else "fail"
    if operator == "<=":
        return "pass" if value <= threshold else "fail"
    return "not_evaluable"


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def build_rows(
    eval_params: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    prompts = manifest.get("prompts", [])
    prompt_index: dict[str, dict[str, Any]] = {}
    if isinstance(prompts, list):
        for p in prompts:
            if isinstance(p, dict):
                prompt_index[str(p.get("prompt_id", ""))] = p

    thresholds = eval_params.get("thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}

    runs = eval_params.get("prompt_runs", [])
    if not isinstance(runs, list):
        runs = []

    rows: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue

        prompt_id = str(run.get("prompt_id", ""))
        prompt_meta = prompt_index.get(prompt_id, {})

        sections_present = float(run.get("sections_present", 0.0))
        sections_required = float(run.get("sections_required", 0.0))
        impl_cov = float(run.get("implementation_pillars_covered", 0.0))
        impl_req = float(run.get("implementation_pillars_required", 0.0))
        verified = float(run.get("verified_claims", 0.0))
        total_claims = float(run.get("total_claims", 0.0))
        unsupported = float(run.get("unsupported_claims", 0.0))

        coverage_rate = _rate(sections_present, sections_required)
        implementation_coverage_rate = _rate(impl_cov, impl_req)
        fusion_fidelity_rate = _rate(verified, total_claims)
        hallucination_rate = _rate(unsupported, total_claims)

        gate_checks = {
            "task_success_rate": _metric_gate_status(
                1.0 if bool(run.get("successful", False)) else 0.0,
                ">=",
                1.0,
            ),
            "fusion_fidelity_rate": _metric_gate_status(
                fusion_fidelity_rate,
                ">=",
                float(thresholds.get("fusion_fidelity_rate_min", 0.95)),
            ),
            "implementation_coverage_rate": _metric_gate_status(
                implementation_coverage_rate,
                ">=",
                float(thresholds.get("implementation_coverage_rate_min", 0.95)),
            ),
            "hallucination_rate": _metric_gate_status(
                hallucination_rate,
                "<=",
                float(thresholds.get("hallucination_rate_max", 0.02)),
            ),
            "avg_iteration_count": _metric_gate_status(
                float(run.get("iterations", 0.0)),
                "<=",
                float(thresholds.get("avg_iteration_count_max", 2.0)),
            ),
            "p95_latency_ms": _metric_gate_status(
                float(run.get("latency_ms", 0.0)),
                "<=",
                float(thresholds.get("p95_latency_ms_max", 3000.0)),
            ),
        }

        fail_reasons = [k for k, v in gate_checks.items() if v == "fail"]
        run_status = "pass" if not fail_reasons else "fail"

        rows.append(
            {
                "run_id": str(run.get("run_id", "")),
                "prompt_id": prompt_id,
                "category": str(run.get("category", prompt_meta.get("category", "unknown"))),
                "title": str(prompt_meta.get("title", "")),
                "objective": str(prompt_meta.get("objective", "")),
                "focus": ", ".join(prompt_meta.get("focus", [])) if isinstance(prompt_meta.get("focus"), list) else "",
                "successful": bool(run.get("successful", False)),
                "first_pass_accepted": bool(run.get("first_pass_accepted", False)),
                "accepted_artifact": bool(run.get("accepted_artifact", False)),
                "coverage_rate": coverage_rate,
                "implementation_coverage_rate": implementation_coverage_rate,
                "fusion_fidelity_rate": fusion_fidelity_rate,
                "hallucination_rate": hallucination_rate,
                "latency_ms": float(run.get("latency_ms", 0.0)),
                "iterations": float(run.get("iterations", 0.0)),
                "generated_tokens": float(run.get("generated_tokens", 0.0)),
                "consistent": bool(run.get("consistent", False)),
                "is_repeat_case": bool(run.get("is_repeat_case", False)),
                "prompt_file": str(prompt_meta.get("prompt_file", "")),
                "run_status": run_status,
                "fail_reasons": fail_reasons,
            }
        )

    return rows


def render_html(
    scorecard: dict[str, Any],
    eval_params: dict[str, Any],
    manifest: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    thresholds = eval_params.get("thresholds", {}) if isinstance(eval_params.get("thresholds"), dict) else {}
    categories = manifest.get("categories", {}) if isinstance(manifest.get("categories"), dict) else {}
    prompt_count = int(manifest.get("prompt_count", len(manifest.get("prompts", []))))
    category_summary = ", ".join(f"{count} {name}" for name, count in categories.items())
    subtitle = f"Browser report with filtering + sorting over {prompt_count} synthetic prompts"
    if category_summary:
        subtitle = f"{subtitle} ({category_summary})"
    subtitle = f"{subtitle}."
    gate_definitions = {
        "task_success_rate": {
            "label": "Task Success Rate",
            "definition": "Share of runs that produced an implementation-usable artifact.",
            "formula": "successful_runs / total_runs",
        },
        "fusion_fidelity_rate": {
            "label": "Fusion Fidelity Rate",
            "definition": "Share of claims verified against trusted Fusion references.",
            "formula": "verified_claims / total_claims",
        },
        "implementation_coverage_rate": {
            "label": "Implementation Coverage Rate",
            "definition": "Coverage of required implementation pillars (cross-pillar, integration, governance, data, security, extensibility, observability).",
            "formula": "implementation_pillars_covered / implementation_pillars_required",
        },
        "hallucination_rate": {
            "label": "Hallucination Rate",
            "definition": "Share of unsupported key technical claims.",
            "formula": "unsupported_claims / total_key_claims",
        },
        "p95_latency_ms": {
            "label": "P95 Latency (ms)",
            "definition": "95th percentile generation latency across runs.",
            "formula": "p95(latency_ms)",
        },
        "avg_iteration_count": {
            "label": "Average Iteration Count",
            "definition": "Average number of revision loops required per run.",
            "formula": "sum(iterations) / run_count",
        },
    }

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Fusion Prompt Benchmark Scorecard</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background:#f6f8fb; color:#1f2937; }}
    .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
    h1, h2 {{ margin: 0 0 10px; }}
    .muted {{ color:#6b7280; font-size: 0.95rem; }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(210px,1fr)); gap:12px; margin:16px 0; }}
    .card {{ background:white; border:1px solid #e5e7eb; border-radius:10px; padding:12px; box-shadow:0 1px 2px rgba(0,0,0,.03); }}
    .metric {{ font-size:1.3rem; font-weight:700; }}
    .status {{ font-weight:700; text-transform:uppercase; font-size:.8rem; padding:3px 8px; border-radius:999px; display:inline-block; }}
    .status.green {{ background:#dcfce7; color:#166534; }}
    .status.red {{ background:#fee2e2; color:#991b1b; }}
    .status.amber {{ background:#fef3c7; color:#92400e; }}
    .status.pass {{ background:#dcfce7; color:#166534; }}
    .status.fail {{ background:#fee2e2; color:#991b1b; }}
    .toolbar {{ background:white; border:1px solid #e5e7eb; border-radius:10px; padding:12px; display:grid; gap:10px; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); }}
    label {{ font-size:.8rem; color:#374151; display:block; margin-bottom:4px; }}
    input, select {{ width:100%; border:1px solid #d1d5db; border-radius:8px; padding:8px; font-size:.9rem; background:white; }}
    table {{ width:100%; border-collapse: collapse; background:white; border:1px solid #e5e7eb; margin-top:12px; }}
    th, td {{ border-bottom:1px solid #e5e7eb; padding:8px; text-align:left; font-size:.85rem; vertical-align:top; }}
    th {{ background:#f9fafb; position:sticky; top:0; z-index:1; }}
    th button {{ border:none; background:none; padding:0; font-weight:700; cursor:pointer; color:#111827; }}
    tbody tr:hover {{ background:#f9fafb; }}
    .table-wrap {{ max-height:65vh; overflow:auto; border-radius:10px; }}
    .small {{ font-size:.78rem; color:#6b7280; }}
    .pill {{ display:inline-block; border-radius:999px; padding:2px 8px; font-size:.75rem; background:#eef2ff; color:#3730a3; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Fusion Skill Prompt Architect — Synthetic Benchmark Scorecard</h1>
    <div class="muted">{subtitle}</div>

    <div class="grid" id="summaryCards"></div>

    <div class="card">
      <h2>Gate Results</h2>
      <div id="gateResults"></div>
      <div class="small" style="margin-top:8px;">Thresholds: <code id="thresholdsText"></code></div>
    </div>

    <div style="height:12px"></div>
    <div class="toolbar">
      <div>
        <label>Search (run/prompt/title/objective)</label>
        <input id="searchInput" placeholder="type to filter" />
      </div>
      <div>
        <label>Category</label>
        <select id="categoryFilter">
          <option value="all">All</option>
          <option value="golden">Golden</option>
          <option value="edge">Edge</option>
          <option value="adversarial">Adversarial</option>
        </select>
      </div>
      <div>
        <label>Run status</label>
        <select id="statusFilter">
          <option value="all">All</option>
          <option value="pass">Pass</option>
          <option value="fail">Fail</option>
        </select>
      </div>
      <div>
        <label>First-pass accepted</label>
        <select id="firstPassFilter">
          <option value="all">All</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      </div>
      <div>
        <label>Min implementation coverage rate</label>
        <input id="minImplCoverage" type="number" min="0" max="1" step="0.01" value="0" />
      </div>
      <div>
        <label>Max hallucination rate</label>
        <input id="maxHallucination" type="number" min="0" max="1" step="0.01" value="1" />
      </div>
    </div>

    <div class="small" style="margin:8px 0;" id="rowCounter"></div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th><button data-sort="run_id">Run</button></th>
            <th><button data-sort="prompt_id">Prompt</button></th>
            <th><button data-sort="category">Category</button></th>
            <th><button data-sort="title">Title</button></th>
            <th><button data-sort="run_status">Status</button></th>
            <th><button data-sort="first_pass_accepted">First Pass</button></th>
            <th><button data-sort="coverage_rate">Coverage</button></th>
            <th><button data-sort="implementation_coverage_rate">Impl Coverage</button></th>
            <th><button data-sort="fusion_fidelity_rate">Fidelity</button></th>
            <th><button data-sort="hallucination_rate">Hallucination</button></th>
            <th><button data-sort="latency_ms">Latency ms</button></th>
            <th><button data-sort="iterations">Iterations</button></th>
            <th>Fail reasons</th>
            <th>Prompt file</th>
          </tr>
        </thead>
        <tbody id="runsBody"></tbody>
      </table>
    </div>
  </div>

  <script>
    const SCORECARD = {json.dumps(scorecard)};
    const THRESHOLDS = {json.dumps(thresholds)};
    const CATEGORIES = {json.dumps(categories)};
    const GATE_DEFS = {json.dumps(gate_definitions)};
    const RUN_ROWS = {json.dumps(rows)};

    const statusClass = (s) => s === 'green' || s === 'pass' ? 'green' : (s === 'red' || s === 'fail' ? 'red' : 'amber');

    function promptHref(promptFile) {{
      if (!promptFile) return '';
      if (promptFile.startsWith('file://') || /^https?:\\/\\//.test(promptFile)) return promptFile;
      if (promptFile.startsWith('/')) return encodeURI(`file://${{promptFile}}`);
      return encodeURI(promptFile);
    }}

    function promptLink(promptFile) {{
      const href = promptHref(promptFile);
      return href ? `<a href="${{href}}" target="_blank">open</a>` : '<span class="small">n/a</span>';
    }}

    function pct(v) {{
      if (v === null || v === undefined || Number.isNaN(v)) return 'n/a';
      return `${{(v * 100).toFixed(2)}}%`;
    }}

    function num(v, d=2) {{
      if (v === null || v === undefined || Number.isNaN(v)) return 'n/a';
      return Number(v).toFixed(d);
    }}

    function formatGateValue(metric, value) {{
      if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
      if (metric.endsWith('_rate')) return pct(value);
      if (metric.includes('latency')) return `${{num(value, 0)}} ms`;
      return num(value, 3);
    }}

    function interpretation(metric, info) {{
      if (info.value === null || info.value === undefined || Number.isNaN(Number(info.value))) {{
        return 'Not evaluable: no metric value was available for this gate.';
      }}

      const value = Number(info.value);
      const threshold = Number(info.threshold);
      const delta = info.operator === '>=' ? value - threshold : threshold - value;
      const absDelta = Math.abs(delta);
      const deltaText = metric.endsWith('_rate') ? pct(absDelta) : num(absDelta, metric.includes('latency') ? 0 : 3);

      if (info.status === 'pass') {{
        if (info.operator === '>=') {{
          return `Pass: metric is above minimum gate by ${{deltaText}}.`;
        }}
        return `Pass: metric is below maximum gate by ${{deltaText}}.`;
      }}

      if (info.operator === '>=') {{
        return `Fail: metric is below required minimum by ${{deltaText}}. Improve control quality or coverage.`;
      }}
      return `Fail: metric is above allowed maximum by ${{deltaText}}. Reduce risk/latency or raise quality controls.`;
    }}

    function renderSummary() {{
      const cards = document.getElementById('summaryCards');
      const metrics = SCORECARD.metrics || {{}};
      const overall = SCORECARD.overall_status || 'amber';
      const items = [
        ['Overall status', overall.toUpperCase(), overall],
        ['Task success rate', pct(metrics.task_success_rate), null],
        ['Fusion fidelity rate', pct(metrics.fusion_fidelity_rate), null],
        ['Implementation coverage rate', pct(metrics.implementation_coverage_rate), null],
        ['Hallucination rate', pct(metrics.hallucination_rate), null],
        ['p95 latency (ms)', num(metrics.p95_latency_ms, 0), null],
        ['Avg iteration count', num(metrics.avg_iteration_count, 2), null],
        ['Sample size', num(metrics.sample_size, 0), null],
      ];
      cards.innerHTML = items.map(([k,v,s]) => `
        <div class="card">
          <div class="small">${{k}}</div>
          <div class="metric">${{v}}</div>
          ${{s ? `<span class="status ${{statusClass(s)}}">${{s}}</span>` : ''}}
        </div>
      `).join('');

      const gateResults = SCORECARD.gate_results || {{}};
      const gateHtml = Object.entries(gateResults).map(([metric, info]) => `
        <div class="card" style="margin:8px 0;">
          <div><strong>${{(GATE_DEFS[metric] && GATE_DEFS[metric].label) || metric}}</strong> <span class="status ${{statusClass(info.status)}}">${{info.status}}</span></div>
          <div class="small"><strong>Definition:</strong> ${{(GATE_DEFS[metric] && GATE_DEFS[metric].definition) || 'n/a'}}</div>
          <div class="small"><strong>Formula:</strong> <code>${{(GATE_DEFS[metric] && GATE_DEFS[metric].formula) || 'n/a'}}</code></div>
          <div class="small"><strong>Gate rule:</strong> value ${{info.operator}} ${{formatGateValue(metric, info.threshold)}}</div>
          <div class="small"><strong>Observed value:</strong> ${{formatGateValue(metric, info.value)}}</div>
          <div class="small"><strong>Interpretation:</strong> ${{interpretation(metric, info)}}</div>
        </div>
      `).join('');
      document.getElementById('gateResults').innerHTML = gateHtml;
      document.getElementById('thresholdsText').textContent = JSON.stringify(THRESHOLDS);
    }}

    let sortKey = 'run_id';
    let sortDir = 'asc';

    function compare(a, b) {{
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === 'number' && typeof bv === 'number') {{
        return sortDir === 'asc' ? av - bv : bv - av;
      }}
      const aa = String(av ?? '');
      const bb = String(bv ?? '');
      return sortDir === 'asc' ? aa.localeCompare(bb) : bb.localeCompare(aa);
    }}

    function passesFilters(row) {{
      const q = document.getElementById('searchInput').value.toLowerCase().trim();
      const category = document.getElementById('categoryFilter').value;
      const status = document.getElementById('statusFilter').value;
      const firstPass = document.getElementById('firstPassFilter').value;
      const minImpl = Number(document.getElementById('minImplCoverage').value || 0);
      const maxHall = Number(document.getElementById('maxHallucination').value || 1);

      if (category !== 'all' && row.category !== category) return false;
      if (status !== 'all' && row.run_status !== status) return false;
      if (firstPass !== 'all' && String(row.first_pass_accepted) !== firstPass) return false;

      const impl = Number(row.implementation_coverage_rate ?? 0);
      const hall = Number(row.hallucination_rate ?? 0);
      if (impl < minImpl) return false;
      if (hall > maxHall) return false;

      if (q) {{
        const blob = `${{row.run_id}} ${{row.prompt_id}} ${{row.title}} ${{row.objective}} ${{row.focus}}`.toLowerCase();
        if (!blob.includes(q)) return false;
      }}
      return true;
    }}

    function renderRows() {{
      const body = document.getElementById('runsBody');
      const rows = RUN_ROWS.filter(passesFilters).sort(compare);
      body.innerHTML = rows.map((r) => `
        <tr>
          <td>${{r.run_id}}</td>
          <td><span class="pill">${{r.prompt_id}}</span></td>
          <td>${{r.category}}</td>
          <td>
            <div><strong>${{r.title || ''}}</strong></div>
            <div class="small">${{r.objective || ''}}</div>
          </td>
          <td><span class="status ${{statusClass(r.run_status)}}">${{r.run_status}}</span></td>
          <td>${{r.first_pass_accepted}}</td>
          <td>${{pct(r.coverage_rate)}}</td>
          <td>${{pct(r.implementation_coverage_rate)}}</td>
          <td>${{pct(r.fusion_fidelity_rate)}}</td>
          <td>${{pct(r.hallucination_rate)}}</td>
          <td>${{num(r.latency_ms, 0)}}</td>
          <td>${{num(r.iterations, 0)}}</td>
          <td class="small">${{(r.fail_reasons || []).join(', ') || 'none'}}</td>
          <td>${{promptLink(r.prompt_file)}}</td>
        </tr>
      `).join('');
      document.getElementById('rowCounter').textContent = `Showing ${{rows.length}} of ${{RUN_ROWS.length}} runs | Categories: ${{JSON.stringify(CATEGORIES)}}`;
    }}

    function bind() {{
      ['searchInput','categoryFilter','statusFilter','firstPassFilter','minImplCoverage','maxHallucination'].forEach((id) => {{
        const el = document.getElementById(id);
        el.addEventListener('input', renderRows);
        el.addEventListener('change', renderRows);
      }});

      document.querySelectorAll('th button[data-sort]').forEach((btn) => {{
        btn.addEventListener('click', () => {{
          const key = btn.getAttribute('data-sort');
          if (sortKey === key) {{
            sortDir = sortDir === 'asc' ? 'desc' : 'asc';
          }} else {{
            sortKey = key;
            sortDir = 'asc';
          }}
          renderRows();
        }});
      }});
    }}

    renderSummary();
    bind();
    renderRows();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render HTML report for synthetic prompt benchmark scorecard")
    parser.add_argument("--scorecard", required=True, help="Path to scorecard JSON (output of evaluate_prompt_skill.py)")
    parser.add_argument("--eval-params", required=True, help="Path to eval params JSON with prompt_runs")
    parser.add_argument("--manifest", required=True, help="Path to synthetic prompt manifest JSON")
    parser.add_argument("--output-html", required=True, help="Path to output HTML report")
    args = parser.parse_args()

    scorecard = _load_json(Path(args.scorecard).resolve())
    eval_params = _load_json(Path(args.eval_params).resolve())
    manifest = _load_json(Path(args.manifest).resolve())
    rows = build_rows(eval_params=eval_params, manifest=manifest)

    html = render_html(scorecard=scorecard, eval_params=eval_params, manifest=manifest, rows=rows)
    output = Path(args.output_html).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Wrote: {output}")


if __name__ == "__main__":
    main()

"""Renderable RVO-style step replay around the frozen Corus v1 kernel."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

import yaml

from demo.replay import apply_replay

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "rvo"
DEFAULT_HTML_PATH = Path("demo/rvo_replay.html")


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_rvo_fixture(fixture_dir: Path = FIXTURE_DIR) -> dict[str, Any]:
    """Load the demo RVO fixture in the same shape consumed by corus_v1."""
    return {
        "project": _read_yaml(fixture_dir / "project.yaml"),
        "agents": _read_yaml(fixture_dir / "agents.yaml"),
        "objectives": _read_yaml(fixture_dir / "objectives.yaml"),
        "contracts": _read_yaml(fixture_dir / "contracts.yaml"),
        "artifacts": _read_yaml(fixture_dir / "artifacts.yaml"),
        "demo_replay": _read_yaml(fixture_dir / "replay.yaml"),
    }


def _step_events(replay: dict[str, Any], step_index: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for step in replay["steps"][: step_index + 1]:
        events.extend(step.get("events", []))
    return events


def _label(labels: dict[str, str], object_id: str) -> str:
    return labels.get(object_id, object_id)


def _action_labels(actions: list[dict[str, Any]], labels: dict[str, str]) -> list[str]:
    return [_label(labels, action["contract"]) for action in actions]


def _blocked_requirement_labels(
    kernel: dict[str, Any],
    labels: dict[str, str],
) -> list[str]:
    blocked: set[str] = set()
    for contract in kernel["contracts"]:
        for artifact_id in contract.get("blocked_by", []):
            blocked.add(_label(labels, artifact_id))
    return sorted(blocked)


def _claim_statuses(
    payload: dict[str, Any],
    labels: dict[str, str],
) -> dict[str, str]:
    return {
        _label(labels, claim["id"]): claim["status"]
        for claim in payload["state"]["claims"]
    }


def _proof_payload(
    payload: dict[str, Any],
    labels: dict[str, str],
) -> dict[str, Any]:
    kernel = payload["kernel"]["derived"]
    claims = payload["state"]["claims"]
    return {
        "sources": [
            _label(labels, source["id"])
            for source in payload["state"]["source_refs"]
        ],
        "supported": [
            _label(labels, claim["id"])
            for claim in claims
            if claim.get("status") in {"supported", "admitted"}
        ],
        "rejected": [
            _label(labels, claim["id"])
            for claim in claims
            if claim.get("status") == "rejected"
        ],
        "next_executor_actions": _action_labels(
            kernel["next_work"]["executor_actions"],
            labels,
        ),
        "next_consumer_actions": _action_labels(
            kernel["next_work"]["consumer_actions"],
            labels,
        ),
        "raw": {
            "sources": [source["id"] for source in payload["state"]["source_refs"]],
            "claims": [
                f"{claim['id']}={claim['status']}"
                for claim in claims
            ],
            "executor_actions": [
                action["contract"]
                for action in kernel["next_work"]["executor_actions"]
            ],
            "consumer_actions": [
                action["contract"]
                for action in kernel["next_work"]["consumer_actions"]
            ],
        },
    }


def _surface_payload(
    step: dict[str, Any],
    payload: dict[str, Any],
    labels: dict[str, str],
) -> dict[str, Any]:
    kernel = payload["kernel"]["derived"]
    surfaces = step["surfaces"]
    return {
        "coordinate": {
            "title": "Coordinate",
            **surfaces["coordinate"],
            "next_executor_actions": _action_labels(
                kernel["next_work"]["executor_actions"],
                labels,
            ),
            "next_consumer_actions": _action_labels(
                kernel["next_work"]["consumer_actions"],
                labels,
            ),
        },
        "implement": {
            "title": "Implement",
            **surfaces["implement"],
            "validation_blockers": _blocked_requirement_labels(kernel, labels),
        },
        "value": {
            "title": "Value",
            **surfaces["value"],
            "claim_statuses": _claim_statuses(payload, labels),
        },
    }


def build_step_replay() -> dict[str, Any]:
    """Build cumulative step payloads for the RVO demo replay."""
    bundle = load_rvo_fixture()
    replay = bundle["demo_replay"]
    labels = replay.get("object_labels", {})
    steps: list[dict[str, Any]] = []

    for index, step in enumerate(replay["steps"]):
        payload = apply_replay(
            bundle,
            _step_events(replay, index),
            claims=replay.get("initial_claims", []),
        )
        steps.append(
            {
                "index": index,
                "id": step["id"],
                "label": step["label"],
                "event": step["event_text"],
                "state_kind": step["state_kind"],
                "state": step["state_text"],
                "changed": step.get("changed", []),
                "primary_surface": step.get("primary_surface", "coordinate"),
                "takeaway": step["takeaway"],
                "surfaces": _surface_payload(step, payload, labels),
                "proof": _proof_payload(payload, labels),
                "sources": payload["state"]["source_refs"],
                "claims": payload["state"]["claims"],
                "artifact_statuses": payload["state"]["artifact_statuses"],
                "kernel": payload["kernel"],
            }
        )

    return {
        "title": replay["title"],
        "framing": replay["framing"],
        "core_line": replay["core_line"],
        "object_labels": labels,
        "steps": steps,
    }


def _text_step(step: dict[str, Any]) -> list[str]:
    return [
        f"Step {step['index']} - {step['label']}",
        f"Event: {step['event']}",
        f"{step['state_kind'].title()} state: {step['state']}",
        "Changed this step:",
        *[f"  - {item}" for item in step["changed"]],
        "Surfaces:",
        f"  Coordinate: {step['surfaces']['coordinate']['body']}",
        f"  Implement: {step['surfaces']['implement']['body']}",
        f"  Value: {step['surfaces']['value']['body']}",
        f"Viewer takeaway: {step['takeaway']}",
    ]


def render_replay_text(replay: dict[str, Any] | None = None) -> str:
    """Render a terminal-friendly step replay."""
    replay = replay or build_step_replay()
    lines = [
        replay["title"],
        replay["framing"],
        "",
        "Replay timeline",
    ]
    for step in replay["steps"]:
        lines.append(f"{step['index']}. {step['label']}")
    for step in replay["steps"]:
        lines.append("")
        lines.extend(_text_step(step))
    lines.extend(["", replay["core_line"]])
    return "\n".join(lines) + "\n"


def _json_script(payload: dict[str, Any]) -> str:
    return html.escape(json.dumps(payload, sort_keys=True), quote=False)


def render_replay_html(replay: dict[str, Any] | None = None) -> str:
    """Render the interactive static replay page."""
    replay = replay or build_step_replay()
    title = html.escape(replay["title"])
    data = _json_script(replay)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1d252c;
      --muted: #63707b;
      --line: #d7dde2;
      --panel: #ffffff;
      --page: #f5f7f8;
      --accent: #1f6f68;
      --amber: #8a5a00;
      --rose: #9d2f3d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--page);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    main {{
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }}
    header {{
      padding: 24px 32px 18px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 28px;
      line-height: 1.15;
      font-weight: 720;
    }}
    .framing {{
      margin: 0;
      color: var(--muted);
      font-size: 15px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(240px, 320px) minmax(0, 1fr);
      gap: 0;
      min-height: 0;
    }}
    aside {{
      border-right: 1px solid var(--line);
      background: #edf1f2;
      padding: 18px;
    }}
    .timeline-title {{
      margin: 0 0 12px;
      font-size: 13px;
      color: var(--muted);
      text-transform: uppercase;
      font-weight: 700;
    }}
    .step-button {{
      width: 100%;
      display: grid;
      grid-template-columns: 28px 1fr;
      align-items: start;
      gap: 8px;
      min-height: 52px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--ink);
      text-align: left;
      padding: 8px;
      border-radius: 6px;
      cursor: pointer;
      font: inherit;
    }}
    .step-button:hover {{ background: #f8fafb; }}
    .step-button.active {{
      background: var(--panel);
      border-color: #b9c7c5;
    }}
    .marker {{
      display: inline-flex;
      width: 24px;
      height: 24px;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: #d8e6e3;
      color: #154d48;
      font-size: 12px;
      font-weight: 700;
      flex: none;
    }}
    .step-button.active .marker {{ background: var(--accent); color: white; }}
    .step-label {{
      display: block;
      font-size: 14px;
      line-height: 1.25;
      font-weight: 680;
    }}
    .step-event {{
      display: block;
      margin-top: 3px;
      font-size: 12px;
      line-height: 1.25;
      color: var(--muted);
    }}
    .content {{
      min-width: 0;
      display: grid;
      grid-template-rows: auto auto auto 1fr;
      gap: 18px;
      padding: 22px 28px;
    }}
    .step-head {{
      display: grid;
      gap: 7px;
      max-width: 980px;
    }}
    .kicker {{
      color: var(--accent);
      font-size: 13px;
      font-weight: 720;
      text-transform: uppercase;
    }}
    h2 {{
      margin: 0;
      font-size: 24px;
      line-height: 1.18;
    }}
    .event {{
      margin: 0;
      color: var(--muted);
      line-height: 1.45;
    }}
    .changed-strip {{
      background: #eef7f5;
      border: 1px solid #b9d6d1;
      border-radius: 8px;
      padding: 14px 16px;
    }}
    .changed-strip h3 {{
      margin: 0 0 8px;
      font-size: 13px;
      color: #16534d;
      text-transform: uppercase;
    }}
    .changed-strip ul {{
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 4px;
      color: #26363f;
      font-size: 14px;
      line-height: 1.35;
    }}
    .surface-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .surface-grid.primary-coordinate {{
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .surface-grid.primary-coordinate .surface-card.primary {{
      grid-column: 1 / -1;
      min-height: 210px;
      border-color: #9ccbc4;
      box-shadow: 0 1px 0 rgba(31, 111, 104, 0.12);
    }}
    .surface-card, .drawer {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .surface-card {{
      min-height: 190px;
      padding: 16px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: 12px;
    }}
    .card-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }}
    .surface-card h3 {{
      margin: 0;
      font-size: 17px;
      line-height: 1.2;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 9px;
      background: #edf1f2;
      color: #34444f;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .surface-card.primary .pill {{
      background: #d8ebe7;
      color: #16534d;
    }}
    .surface-card p {{
      margin: 0;
      line-height: 1.45;
      color: #2c3842;
      font-size: 15px;
    }}
    .meta {{
      border-top: 1px solid var(--line);
      padding-top: 10px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      min-height: 42px;
    }}
    .drawer {{
      min-height: 220px;
      padding: 0;
    }}
    .drawer summary {{
      cursor: pointer;
      padding: 16px;
      border-bottom: 1px solid var(--line);
      font-weight: 720;
    }}
    .proof-grid {{
      padding: 16px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 18px;
      align-content: start;
    }}
    .drawer h3 {{
      margin: 0 0 8px;
      font-size: 14px;
      text-transform: uppercase;
      color: var(--muted);
    }}
    .drawer ul {{
      margin: 0;
      padding-left: 18px;
      color: #2c3842;
      font-size: 13px;
      line-height: 1.45;
    }}
    .raw-objects {{
      grid-column: 1 / -1;
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }}
    .raw-objects summary {{
      border: 0;
      padding: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .raw-columns {{
      margin-top: 10px;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .takeaway {{
      grid-column: 1 / -1;
      margin-top: 4px;
      border-top: 1px solid var(--line);
      padding-top: 12px;
      color: var(--ink);
      font-weight: 650;
    }}
    .core-line {{
      grid-column: 1 / -1;
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 840px) {{
      .layout {{ grid-template-columns: 1fr; }}
      aside {{ border-right: 0; border-bottom: 1px solid var(--line); }}
      .surface-grid, .surface-grid.primary-coordinate, .proof-grid, .raw-columns {{ grid-template-columns: 1fr; }}
      header, .content {{ padding-left: 18px; padding-right: 18px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{title}</h1>
      <p class="framing">{html.escape(replay["framing"])}</p>
    </header>
    <section class="layout">
      <aside>
        <p class="timeline-title">Replay timeline</p>
        <div id="timeline"></div>
      </aside>
      <section class="content">
        <div class="step-head">
          <span class="kicker" id="step-kicker"></span>
          <h2 id="step-title"></h2>
          <p class="event" id="step-event"></p>
        </div>
        <section class="changed-strip">
          <h3>Changed this step</h3>
          <ul id="changed-list"></ul>
        </section>
        <div class="surface-grid" id="surface-grid">
          <article class="surface-card" id="coordinate-card">
            <div class="card-head">
              <h3>Coordinate</h3>
              <span class="pill" id="coordinate-status"></span>
            </div>
            <p id="coordinate-body"></p>
            <div class="meta" id="coordinate-meta"></div>
          </article>
          <article class="surface-card" id="implement-card">
            <div class="card-head">
              <h3>Implement</h3>
              <span class="pill" id="implement-status"></span>
            </div>
            <p id="implement-body"></p>
            <div class="meta" id="implement-meta"></div>
          </article>
          <article class="surface-card" id="value-card">
            <div class="card-head">
              <h3>Value</h3>
              <span class="pill" id="value-status"></span>
            </div>
            <p id="value-body"></p>
            <div class="meta" id="value-meta"></div>
          </article>
        </div>
        <details class="drawer" open>
          <summary>Proof drawer · Sources · Claims · Kernel output</summary>
          <section class="proof-grid">
            <div>
              <h3>Sources</h3>
              <ul id="sources-list"></ul>
            </div>
            <div>
              <h3>Supported</h3>
              <ul id="supported-list"></ul>
            </div>
            <div>
              <h3>Rejected</h3>
              <ul id="rejected-list"></ul>
            </div>
            <div>
              <h3>Next Work</h3>
              <ul id="next-work-list"></ul>
            </div>
            <details class="raw-objects">
              <summary>View raw objects</summary>
              <div class="raw-columns">
                <div>
                  <h3>Sources</h3>
                  <ul id="raw-sources-list"></ul>
                </div>
                <div>
                  <h3>Claims</h3>
                  <ul id="raw-claims-list"></ul>
                </div>
                <div>
                  <h3>Kernel Output</h3>
                  <ul id="raw-kernel-list"></ul>
                </div>
              </div>
            </details>
            <div class="takeaway" id="takeaway"></div>
            <p class="core-line">{html.escape(replay["core_line"])}</p>
          </section>
        </details>
      </section>
    </section>
  </main>
  <script id="replay-data" type="application/json">{data}</script>
  <script>
    const replay = JSON.parse(document.getElementById('replay-data').textContent);
    const timeline = document.getElementById('timeline');
    const els = {{
      kicker: document.getElementById('step-kicker'),
      title: document.getElementById('step-title'),
      event: document.getElementById('step-event'),
      changed: document.getElementById('changed-list'),
      surfaceGrid: document.getElementById('surface-grid'),
      coordinateCard: document.getElementById('coordinate-card'),
      coordinateBody: document.getElementById('coordinate-body'),
      coordinateStatus: document.getElementById('coordinate-status'),
      coordinateMeta: document.getElementById('coordinate-meta'),
      implementCard: document.getElementById('implement-card'),
      implementBody: document.getElementById('implement-body'),
      implementStatus: document.getElementById('implement-status'),
      implementMeta: document.getElementById('implement-meta'),
      valueCard: document.getElementById('value-card'),
      valueBody: document.getElementById('value-body'),
      valueStatus: document.getElementById('value-status'),
      valueMeta: document.getElementById('value-meta'),
      sources: document.getElementById('sources-list'),
      supported: document.getElementById('supported-list'),
      rejected: document.getElementById('rejected-list'),
      nextWork: document.getElementById('next-work-list'),
      rawSources: document.getElementById('raw-sources-list'),
      rawClaims: document.getElementById('raw-claims-list'),
      rawKernel: document.getElementById('raw-kernel-list'),
      takeaway: document.getElementById('takeaway')
    }};
    const buttons = replay.steps.map((step, index) => {{
      const button = document.createElement('button');
      button.className = 'step-button';
      button.type = 'button';
      button.innerHTML = `<span class="marker">${{index}}</span><span><span class="step-label">Step ${{index}} ${{step.label}}</span><span class="step-event">${{step.event}}</span></span>`;
      button.addEventListener('click', () => renderStep(index));
      timeline.appendChild(button);
      return button;
    }});
    function listItems(element, items, emptyText) {{
      element.innerHTML = '';
      if (!items.length) {{
        const li = document.createElement('li');
        li.textContent = emptyText;
        element.appendChild(li);
        return;
      }}
      items.forEach((item) => {{
        const li = document.createElement('li');
        li.textContent = item;
        element.appendChild(li);
      }});
    }}
    function renderStep(index) {{
      const step = replay.steps[index];
      buttons.forEach((button, i) => button.classList.toggle('active', i === index));
      els.kicker.textContent = `Step ${{step.index}}`;
      els.title.textContent = step.label;
      els.event.textContent = step.event;
      listItems(els.changed, step.changed, 'No visible change');
      els.surfaceGrid.classList.toggle('primary-coordinate', step.primary_surface === 'coordinate');
      els.coordinateCard.classList.toggle('primary', step.primary_surface === 'coordinate');
      els.implementCard.classList.toggle('primary', step.primary_surface === 'implement');
      els.valueCard.classList.toggle('primary', step.primary_surface === 'value');
      els.coordinateStatus.textContent = step.surfaces.coordinate.status;
      els.implementStatus.textContent = step.surfaces.implement.status;
      els.valueStatus.textContent = step.surfaces.value.status;
      els.coordinateBody.textContent = step.surfaces.coordinate.body;
      els.implementBody.textContent = step.surfaces.implement.body;
      els.valueBody.textContent = step.surfaces.value.body;
      els.coordinateMeta.textContent = `Next executor: ${{step.surfaces.coordinate.next_executor_actions.join(', ') || 'none'}}`;
      els.implementMeta.textContent = `Pending before validation: ${{step.surfaces.implement.validation_blockers.join(', ') || 'none'}}`;
      const claimMeta = Object.entries(step.surfaces.value.claim_statuses).map(([id, status]) => `${{id}}=${{status}}`);
      els.valueMeta.textContent = claimMeta.join(', ');
      listItems(els.sources, step.proof.sources.map((source) => `${{source}} attached`), 'No sources attached');
      listItems(els.supported, step.proof.supported, 'No supported claims');
      listItems(els.rejected, step.proof.rejected, 'No rejected claims');
      listItems(els.nextWork, [
        ...step.proof.next_executor_actions.map((item) => `Executor: ${{item}}`),
        ...step.proof.next_consumer_actions.map((item) => `Consumer: ${{item}}`)
      ], 'No next work');
      listItems(els.rawSources, step.proof.raw.sources, 'No raw sources');
      listItems(els.rawClaims, step.proof.raw.claims, 'No raw claims');
      listItems(els.rawKernel, [
        `state: ${{step.state}}`,
        `executor_actions: ${{step.proof.raw.executor_actions.join(', ') || 'none'}}`,
        `consumer_actions: ${{step.proof.raw.consumer_actions.join(', ') || 'none'}}`
      ], 'No raw kernel output');
      els.takeaway.textContent = step.takeaway;
    }}
    renderStep(0);
  </script>
</body>
</html>
"""


def write_replay_html(path: Path = DEFAULT_HTML_PATH) -> Path:
    """Write the static replay page and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_replay_html(), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m demo.rvo_replay",
        description="Render the RVO context replay",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit step replay payload as JSON",
    )
    parser.add_argument(
        "--html",
        nargs="?",
        const=str(DEFAULT_HTML_PATH),
        default=None,
        help="Write the static replay page to a file",
    )
    args = parser.parse_args(argv)

    if args.json:
        print(json.dumps(build_step_replay(), indent=2, sort_keys=True))
    elif args.html is not None:
        path = write_replay_html(Path(args.html))
        print(f"Wrote RVO replay page: {path}")
    else:
        print(render_replay_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""aggregate.py - summarize results/results.jsonl into results/summary.md.

results.jsonl is append-only: every run_eval.py invocation adds records
without touching prior ones. This script only reads it, so it's always safe
to re-run - it regenerates summary.md from scratch each time rather than
patching it incrementally.

Usage:
    python scripts/aggregate.py
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def config_table(records: list[dict]) -> str:
    by_config: dict[str, list[dict]] = {}
    for r in records:
        by_config.setdefault(r["config"], []).append(r)

    lines = [
        "| Config | Passed | Total | Pass rate | Median (s) | Total (s) |",
        "|---|---|---|---|---|---|",
    ]
    for config in sorted(by_config):
        rs = by_config[config]
        auto = [r for r in rs if r.get("grading") != "manual"]
        passed = sum(1 for r in auto if r.get("passed"))
        total = len(auto)
        rate = f"{passed / total:.0%}" if total else "n/a"
        secs = [r["seconds"] for r in rs if "seconds" in r]
        median = f"{statistics.median(secs):.1f}" if secs else "n/a"
        total_s = f"{sum(secs):.1f}" if secs else "n/a"
        lines.append(f"| {config} | {passed} | {total} | {rate} | {median} | {total_s} |")
    return "\n".join(lines)


def task_matrix(records: list[dict]) -> str:
    configs = sorted({r["config"] for r in records})
    tasks = sorted({r["id"] for r in records})
    mark = {True: "PASS", False: "FAIL", None: "-"}

    # Later records win on repeat (config, task) pairs, since the file is a
    # log of every run - the matrix shows the most recent result per pair.
    latest: dict[tuple[str, str], str] = {}
    for r in records:
        latest[(r["id"], r["config"])] = mark[r.get("passed")]

    header = "| Task | " + " | ".join(configs) + " |"
    sep = "|---|" + "---|" * len(configs)
    rows = [
        f"| {task} | " + " | ".join(latest.get((task, c), "") for c in configs) + " |"
        for task in tasks
    ]
    return "\n".join([header, sep, *rows])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=Path("results/results.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("results/summary.md"))
    args = ap.parse_args()

    records = load(args.results)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "# Results summary\n\n"
        "## By config\n\n" + config_table(records) + "\n\n"
        "## By task\n\n" + task_matrix(records) + "\n"
    )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

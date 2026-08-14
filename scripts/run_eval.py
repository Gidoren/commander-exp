"""
run_eval.py - run one agent configuration against the task set.

Pass criterion, for `code` tasks, needs no hand-written checker:
  1. create a worktree at the task's PARENT commit
  2. let the agent work
  3. check out the test files FROM THE FIX COMMIT into the worktree
  4. run the tests

Those tests failed before the fix and passed after it, by construction. The
agent never sees them - they arrive only at grading time - so it cannot cheat
by editing them.

`infra` tasks use an explicit `check` command in the manifest instead.

Usage:
    python run_eval.py tasks.json --config baseline \
        --cmd 'pi -m qwen3.6-27b --yolo "{task}"'
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=check
    )


def run_one(repo: Path, task: dict, cmd_tmpl: str, timeout: int) -> dict:
    wt = repo.parent / f".eval-{uuid.uuid4().hex[:8]}"
    started = time.time()
    record = {"sha": task["sha"], "task": task["task"], "kind": task["kind"]}

    try:
        git(repo, "worktree", "add", "--detach", str(wt), task["parent"])

        cmd = cmd_tmpl.format(task=task["task"].replace('"', '\\"'))
        agent = subprocess.run(
            cmd, cwd=wt, shell=True, capture_output=True,
            text=True, timeout=timeout,
        )
        record["agent_exit"] = agent.returncode
        record["agent_tail"] = (agent.stdout + agent.stderr)[-2000:]

        if task["kind"] == "code":
            # Bring in the real tests AFTER the agent is done.
            git(repo, "checkout", task["sha"], "--", *task["test_files"], check=False)
            for f in task["test_files"]:
                src = repo / f
                dst = wt / f
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            git(repo, "checkout", "HEAD", "--", *task["test_files"], check=False)
            check_cmd = task.get("check", "pytest -q " + " ".join(task["test_files"]))
        else:
            check_cmd = task["check"]  # required for infra tasks

        graded = subprocess.run(
            check_cmd, cwd=wt, shell=True, capture_output=True,
            text=True, timeout=900,
        )
        record["passed"] = graded.returncode == 0
        record["check_tail"] = (graded.stdout + graded.stderr)[-2000:]
        record["diff_stat"] = git(wt, "diff", "--stat", check=False).stdout.strip()

    except subprocess.TimeoutExpired:
        record["passed"] = False
        record["error"] = "timeout"
    except subprocess.CalledProcessError as e:
        record["passed"] = False
        record["error"] = f"{e.cmd}: {e.stderr[:400]}"
    finally:
        record["seconds"] = round(time.time() - started, 1)
        git(repo, "worktree", "remove", "--force", str(wt), check=False)

    return record


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", type=Path)
    ap.add_argument("--config", required=True, help="name for this run")
    ap.add_argument("--cmd", required=True, help="agent command, {task} substituted")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--out", type=Path, default=Path("results.jsonl"))
    args = ap.parse_args()

    manifest = json.loads(args.tasks.read_text())
    repo = Path(manifest["repo"])
    tasks = manifest["candidates"]

    results = []
    for i, t in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] {t['task'][:70]}")
        r = run_one(repo, t, args.cmd, args.timeout)
        r["config"] = args.config
        results.append(r)
        print(f"    {'PASS' if r.get('passed') else 'FAIL'}  {r['seconds']}s")

    with args.out.open("a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    passed = sum(1 for r in results if r.get("passed"))
    total_s = sum(r["seconds"] for r in results)
    print(f"\n{args.config}: {passed}/{len(results)} passed, {total_s / 60:.1f} min")
    print("\n| config | passed | total | wall clock |")
    print("|---|---|---|---|")
    print(f"| {args.config} | {passed} | {len(results)} | {total_s / 60:.1f} min |")


if __name__ == "__main__":
    main()

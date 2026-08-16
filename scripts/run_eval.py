"""
run_eval.py - run one agent configuration against the deckcheck task set.

Hidden tests live OUTSIDE the repository, in a plain directory. They are never
committed to any branch, because `git worktree add` shares the object store and
all refs with the parent repo - an agent in a worktree can read any branch via
`git show`. Keeping the tests out of git entirely is the only airtight version.

    ~/src/commander-exp/          # the repo, main only
    ~/src/commander-exp-tests/    # test_t01_nonland.py, test_t11_companions.py, ...

Grading flow per task:
    1. worktree at `start_ref`
    2. agent runs with no access to the tests
    3. test files copied in from --tests-dir
    4. `check` runs

Usage:
    python scripts/run_eval.py tasks/tasks.json \
        --config baseline-1 \
        --tests-dir ~/src/commander-exp-tests \
        --cmd 'pi --yolo {task}'
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=check
    )


def substitute_cmd(cmd_tmpl: str) -> str:
    """Replace {task} with the env-var reference the task is passed through.

    The task string is never interpolated into the shell command directly -
    it goes through $EVAL_TASK in the subprocess environment instead, so
    special characters (->, quotes, ...) can't be word-split by the shell.
    A --cmd template that wraps {task} in its own quotes would double-quote
    the substitution and break that guarantee, so it's rejected outright.
    """
    if '"{task}"' in cmd_tmpl or "'{task}'" in cmd_tmpl:
        raise SystemExit("--cmd: do not quote {task}; substitution supplies quoting")
    return cmd_tmpl.replace("{task}", '"$EVAL_TASK"')


def preflight(repo: Path, tests_dir: Path, tasks: list[dict]) -> None:
    """Refuse to run if the tests are reachable from inside the repo."""
    if tests_dir.resolve().is_relative_to(repo.resolve()):
        raise SystemExit(f"FATAL: tests-dir {tests_dir} is inside the repo")

    tracked = git(repo, "log", "--all", "--name-only", "--pretty=format:").stdout
    leaked = sorted({
        f for t in tasks for f in t.get("test_files", [])
        if Path(f).name in tracked
    })
    if leaked:
        raise SystemExit(
            "FATAL: hidden test filenames appear in git history:\n  "
            + "\n  ".join(leaked)
            + "\nPurge them (git-filter-repo --path <dir> --invert-paths) "
              "and delete any branch holding them before measuring anything."
        )

    for t in tasks:
        for f in t.get("test_files", []):
            if not (tests_dir / Path(f).name).exists():
                raise SystemExit(f"FATAL: missing test file {tests_dir / Path(f).name}")


def run_one(repo: Path, tests_dir: Path, task: dict, cmd_tmpl: str, timeout: int) -> dict:
    wt = repo.parent / f".eval-{uuid.uuid4().hex[:8]}"
    started = time.time()
    rec: dict = {
        "id": task["id"],
        "tier": task["tier"],
        "task": task["task"],
        "grading": task.get("grading", "auto"),
    }

    try:
        git(repo, "worktree", "add", "--detach", str(wt), task.get("start_ref", "main"))

        cmd = substitute_cmd(cmd_tmpl)
        env = {**os.environ, "EVAL_TASK": task["task"], "CI": "1", "TERM": "dumb"}
        try:
            agent = subprocess.run(
                cmd, cwd=wt, shell=True, capture_output=True, text=True,
                timeout=timeout, stdin=subprocess.DEVNULL, env=env,
            )
            rec["agent_exit"] = agent.returncode
            stdout, stderr = agent.stdout, agent.stderr
        except subprocess.TimeoutExpired as e:
            # Partial output is captured on the exception itself - grab it
            # before the timeout propagates, instead of losing it.
            rec["agent_exit"] = None
            rec["agent_tail"] = ((e.stdout or "") + (e.stderr or ""))[-3000:]
            rec["diff_stat"] = git(wt, "diff", "--stat", check=False).stdout.strip()
            rec["passed"], rec["error"] = False, "timeout"
            return rec

        rec["agent_tail"] = (stdout + stderr)[-3000:]
        rec["diff_stat"] = git(wt, "diff", "--stat", check=False).stdout.strip()

        if rec["grading"] == "manual":
            # t14 / t15 have no correct answer. Record behaviour, not a boolean.
            rec["passed"] = None
            rec["note"] = task.get("note", "")
            return rec

        # Tests arrive only now, from outside git.
        for f in task["test_files"]:
            dst = wt / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tests_dir / Path(f).name, dst)

        graded = subprocess.run(
            task["check"], cwd=wt, shell=True,
            capture_output=True, text=True, timeout=900,
        )
        rec["passed"] = graded.returncode == 0
        rec["check_tail"] = (graded.stdout + graded.stderr)[-3000:]

    except subprocess.TimeoutExpired:
        rec["passed"], rec["error"] = False, "timeout"
    except subprocess.CalledProcessError as e:
        rec["passed"], rec["error"] = False, f"{e.cmd}: {e.stderr[:400]}"
    finally:
        rec["seconds"] = round(time.time() - started, 1)
        git(repo, "worktree", "remove", "--force", str(wt), check=False)

    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", type=Path)
    ap.add_argument("--config", required=True)
    ap.add_argument("--cmd", required=True, help="agent command, {task} substituted")
    ap.add_argument("--tests-dir", type=Path, required=True)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--out", type=Path, default=Path("results/results.jsonl"))
    ap.add_argument(
        "--only", default="",
        help="comma-separated task ids, e.g. t01_nonland,t11_companions. "
             "Preflight then only requires those tests to exist.",
    )
    args = ap.parse_args()

    tasks = json.loads(args.tasks.read_text())["tasks"]

    if args.only:
        keep = {s.strip() for s in args.only.split(",") if s.strip()}
        unknown = keep - {t["id"] for t in tasks}
        if unknown:
            raise SystemExit(f"unknown task ids: {sorted(unknown)}")
        tasks = [t for t in tasks if t["id"] in keep]

    preflight(args.repo, args.tests_dir, tasks)

    results = []
    for i, t in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] {t['id']}")
        r = run_one(args.repo, args.tests_dir, t, args.cmd, args.timeout)
        r["config"] = args.config
        results.append(r)
        mark = {True: "PASS", False: "FAIL", None: "MANUAL"}[r.get("passed")]
        print(f"    {mark}  {r['seconds']}s")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    auto = [r for r in results if r.get("grading") != "manual"]
    passed = sum(1 for r in auto if r.get("passed"))
    print(f"\n{args.config}: {passed}/{len(auto)} auto-graded, "
          f"{len(results) - len(auto)} manual, "
          f"{sum(r['seconds'] for r in results) / 60:.1f} min")


if __name__ == "__main__":
    main()

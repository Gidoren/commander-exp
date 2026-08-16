# Brief: step 2 — spec cleanup and the decomposition experiment

## Context

The eval harness is built and validated. Baseline is **9/13 auto-graded, 92 min,
single run** with Qwen3.6-27B via Pi 0.84.2 against a local OpenAI-compatible
endpoint.

Important: every baseline run before this one had **truncated task prompts** —
`run_eval.py` interpolated the task string into a `shell=True` command and the
shell split it at the first `->`, so the model received partial function
signatures. Any number in `results.jsonl` from a config other than the most
recent `baseline-1` is invalid. Do not compare against them.

Current failures:

| Task | Time | Diagnosis |
|---|---|---|
| t04_parse_edge | 732s | real — section headers with counts, e.g. `Commander (1)` |
| t07_identity | 101s | **unexplained regression** — passed 3/3 previously at 1000–3400s |
| t08_cmdr_subset | 363s | spec ambiguity in the hidden test, not a model failure |
| t12_brackets | 119s | spec ambiguity in the hidden test, not a model failure |

t11_companions passes but took 3025s — the slowest result in the set and the
motivation for the decomposition experiment below.

## Non-goals

Do not build any of the following. They are gated on evidence this step is
meant to produce:

- Any orchestrator, state machine, or supervisor
- Any second model, model routing, or frontier-model API integration
- Fresh-context-per-subtask machinery beyond what the manifest already does
- A dashboard or web UI

## Paths

```
~/commander-experiments/src/commander-exp     # the eval repo
~/.local/share/deckcheck-answers/tests        # hidden tests
~/.local/share/deckcheck-answers/deckcheck    # reference implementation
```

The answers directory must stay outside the repo and outside the worktree's
parent directory. Worktrees are created at `<repo>/../.eval-*`, so anything
adjacent to `src/` is readable by the agent's bash tool.

---

## 2.1 Guard against the quoting bug recurring

`run_eval.py` substitutes `{task}` with `"$EVAL_TASK"` and passes the task via
the environment. If a `--cmd` template wraps `{task}` in its own quotes, the
result is doubled quotes and the string word-splits again.

Add to `run_one`, before the substitution:

```python
if '"{task}"' in cmd_tmpl or "'{task}'" in cmd_tmpl:
    raise SystemExit("--cmd: do not quote {task}; substitution supplies quoting")
```

Also add a regression test asserting a task string containing `->` and an
apostrophe survives the substitution intact.

**Done when:** the guard fires on a quoted template and the round-trip test passes.

## 2.2 Capture agent output on timeout

The `except subprocess.TimeoutExpired` path records `passed` and `error` but
never `agent_tail` or `diff_stat`, so timeouts are the least informative
records in the file. They should be the most.

Restructure so partial output is captured before the exception propagates.

**Done when:** a task killed by timeout still records whatever the agent produced.

## 2.3 Resolve the two spec ambiguities

These are defects in the hidden tests, not model failures. Fix the test **and**
the corresponding stub docstring in the repo so the spec is unambiguous from
either direction.

**t08 — `check_color_identity` with no commanders.** The test asserts `[]`.
The model returned violations, reasoning that an empty commander identity
permits nothing. Both readings are defensible. Pick one, state it explicitly in
`deckcheck/legality.py`'s stub docstring, and make the test match.

**t12 — bracket thresholds.** The test pins: 0 tutors → bracket 1, any tutor →
2, 1–3 game changers → 3, 4+ game changers or any mass land denial or any
two-card combo → 4, never 5. The model read the tutor threshold and the
extra-turn regex differently. Either loosen the test or tighten
`deckcheck/brackets.py`'s stub docstring so the boundaries are stated as
numbers, not adjectives.

**Done when:** both stub docstrings state the rule precisely enough that a
reader could not arrive at the model's interpretation, and the reference
implementation still passes.

## 2.4 Investigate the t07 regression

`t07_identity` passed three times at 1000–3400s, then failed at 101s in the
clean run. The clean run is the only one where the model received the full
prompt, so this may be a genuine behaviour change rather than noise.

Read `agent_tail` and `check_tail` for both the old passes and the new failure.
Report which tests failed and whether the model stopped early, misread the
spec, or hit an error. Do not fix anything — this is diagnosis.

**Done when:** `results/t07-regression.md` explains what differs, or states
plainly that it looks like run-to-run variance.

## 2.5 The decomposition experiment

The hypothesis: `t11_companions` is slow and unreliable because it bundles nine
structurally distinct rules into one task, and the model loses coherence across
them. If true, splitting the task should improve both time and reliability
without changing the model or adding any orchestration.

Add three tasks to `tasks/tasks.json`, keeping `t11_companions` intact:

- **`t11a_companions_mv`** — Lurrus, Obosh, Gyruda, Keruga (mana-value rules)
- **`t11b_companions_cost`** — Jegantha, Kaheera (cost and type rules)
- **`t11c_companions_struct`** — Umori, Zirda, Yorion (structural rules)

Each task string must pin the same `check_companion(deck, companion)` signature
and state only its own subset of rules. Each uses the existing
`test_t11_companions.py` as its check, filtered to the relevant tests via
`pytest -k`. Split the test file into three if `-k` selection is awkward.

Subtasks run against `start_ref: main` independently — no shared state. The
comparison is: does `t11a + t11b + t11c` beat `t11` on total wall clock and on
pass rate?

Run each configuration **three times**, since per-task results flip run to run
and a single comparison proves nothing:

```bash
for i in 1 2 3; do
  make baseline ONLY=t11_companions CONFIG=decomp-whole-$i
  make baseline ONLY=t11a_companions_mv,t11b_companions_cost,t11c_companions_struct \
    CONFIG=decomp-split-$i
done
```

The Makefile's `baseline` target does not currently accept `ONLY` or `CONFIG`.
Add both.

**Done when:** `results/decomposition.md` reports total wall clock and pass
counts for both configurations across three runs, with a plain-language verdict.

## 2.6 Build `aggregate.py`

Referenced in earlier plans, never written. Reads `results.jsonl`, emits
`results/summary.md`: a config-level table (config, passed, total, pass rate,
median and total wall clock) and a per-task matrix of which configs passed
which tasks. Append-only source; never overwrite prior runs.

Must exclude `grading: "manual"` tasks from pass-rate denominators.

**Done when:** `make summary` regenerates the table from scratch.

---

## Definition of done

- [x] Quoting guard in place with a regression test
- [x] Timeouts capture agent output
- [x] t08 and t12 stub docstrings unambiguous; tests match; reference passes
- [x] `results/t07-regression.md` written
- [x] `results/decomposition.md` written with a verdict
- [x] `aggregate.py` working
- [x] No orchestration code in the repo

## Ask before assuming

1. Which reading to adopt for t08's no-commander case.
2. Whether to loosen t12's test or tighten its docstring.
3. Whether to split `test_t11_companions.py` or use `pytest -k` selection.
